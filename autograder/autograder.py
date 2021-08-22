import multiprocessing
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Dict, List, Set, Type, Tuple

from autograder.testcase_utils.testcase_io import TestCaseIO
from .config_manager import GradingConfig
from .output_summary import BufferOutputLogger, GradingOutputLogger, get_submission_name
from .testcase_utils.abstract_testcase import ArgList, TestCase
from .testcase_utils.stdout_testcase import StdoutOnlyTestCase
from .testcase_utils.submission import Submission, find_appropriate_source_file_stem
from .testcase_utils.testcase_picker import TestCasePicker
from .util import AutograderError, import_from_path, get_file_stems

EMPTY_TESTCASE_IO = TestCaseIO.get_empty_io()


class Grader:
    no_output: bool
    submissions: List[Submission]
    tests: Dict[Type[TestCase], List[TestCase]]
    raw_submissions: List[Path]
    paths: "AutograderPaths"

    logger: GradingOutputLogger
    config: GradingConfig
    testcase_picker: TestCasePicker
    stdout_only_tests: list

    def __init__(self, current_dir, no_output=False, submissions=None):
        if submissions is None:
            submissions = []
        self.no_output = no_output
        self.raw_submissions = submissions
        self.stdout_formatters = {}
        self.paths = AutograderPaths(current_dir)

    def run(self):
        io_choices = {}
        try:
            self.stdout_formatters = self._import_formatters(self.paths.stdout_formatters)
            self.config = GradingConfig(self.paths.config, self.paths.default_config)
            self.testcase_picker = TestCasePicker(
                self.paths.testcase_types_dir,
                self.config.possible_source_file_stems,
                self.config.stdout_only_grading_enabled,
            )
            self.logger = GradingOutputLogger(
                self.paths.current_dir,
                self.paths.output_summary,
                self.paths.results_dir,
                self.config.assignment_name,
                self.config.total_points_possible,
                self.no_output,
                self.config.generate_results,
            )
            self._prepare_directory_structure()
            self.submissions = self._gather_submissions()
            io_choices = self._gather_io()
            # also copies testcase_utils to temp dir
            self.tests, unused_io_choices = self._gather_testcases(io_choices.copy())
            if self.config.stdout_only_grading_enabled:
                self.tests[StdoutOnlyTestCase] = self._generate_stdout_only_testcases(unused_io_choices)
            process_count = multiprocessing.cpu_count() if self.config.parallel_grading_enabled else 1
            with multiprocessing.Pool(process_count) as pool:
                man = multiprocessing.Manager()
                total_class_points = sum(pool.map(Runner(self, man.Lock()), self.submissions))
            class_average = total_class_points / len(self.submissions)
            self.logger(f"\nAverage score: {round(class_average)}/{self.config.total_points_possible}")
            self.logger.print_key()
        finally:
            for io in io_choices.values():
                io.cleanup()
            self.cleanup()
        return class_average

    def run_on_single_submission(self, submission: Submission, lock):
        with temporarily_change_dir(submission.dir):
            self._copy_extra_files(submission.dir)
            with self.logger.single_submission_output_logger(lock) as logger:
                result = self._get_testcase_output(submission, logger)
        # Cleanup after running tests on student submission
        shutil.rmtree(submission.dir)
        return result

    def cleanup(self):
        if self.paths.temp_dir.exists():
            shutil.rmtree(self.paths.temp_dir)

    def _prepare_directory_structure(self):
        # Cleanup in case any error
        self.cleanup()
        self.paths.temp_dir.mkdir()
        self._check_required_directories_exist()
        if self.config.generate_results:
            self.paths.results_dir.mkdir(exist_ok=True)

    def _copy_extra_files(self, to_dir: Path):
        if self.paths.extra_dir.exists():
            for path in self.paths.extra_dir.iterdir():
                new_path = to_dir / path.name
                shutil.copy(str(path), str(new_path))

    def _check_required_directories_exist(self):
        for directory in self.paths.required_dirs:
            if not directory.exists():
                raise AutograderError(
                    f"{directory} directory not found. It is required for the grader to function.\n"
                    "Maybe you specified the incorrect directory? Use `autograder submission_directory_here`"
                )

    def _gather_submissions(self) -> List[Submission]:
        """Returns sorted list of paths to submissions"""
        submissions_to_grade = set(self.raw_submissions)
        submissions: List[Submission] = []
        for submission_path in self.paths.current_dir.iterdir():
            if submissions_to_grade and submission_path.name not in submissions_to_grade:
                continue

            testcase_type = self.testcase_picker.pick(submission_path)
            if testcase_type is not None:
                if (
                    self.config.any_submission_file_name_is_allowed
                    or find_appropriate_source_file_stem(submission_path, self.config.possible_source_file_stems)
                    is not None
                ):
                    submissions.append(Submission(submission_path, testcase_type, self.paths.temp_dir))
                else:
                    self.logger(f"{submission_path} does not contain the required file name. Skipping it.")

        if not len(submissions):
            raise AutograderError(f"No student submissions found in '{self.paths.current_dir}'.")

        # Allows consistent output
        submissions.sort(key=lambda s: s.path)
        return submissions

    def _gather_io(self) -> Dict[str, TestCaseIO]:
        outputs = get_file_stems(self.paths.output_dir)
        inputs = get_file_stems(self.paths.input_dir)
        io: Set[str] = set().union(outputs, inputs)
        dict_io = {p: TestCaseIO(p, self.stdout_formatters, self.paths.input_dir, self.paths.output_dir) for p in io}
        return dict_io

    def _generate_stdout_only_testcases(self, io_choices: Dict[str, TestCaseIO]) -> List[TestCase]:
        default_timeout = self.config.timeouts.get("ALL", 1)
        default_weight = self.config.testcase_weights.get("ALL", 1)
        return [
            StdoutOnlyTestCase(
                io.output_file,
                self.config.timeouts.get(io.name, default_timeout),
                self.config.generate_arglists(io.name),
                self.config.testcase_weights.get(io.name, default_weight),
                io,
            )
            for io in io_choices.values()
            if io.expected_output
        ]

    def _gather_testcases(
        self, io: Dict[str, TestCaseIO]
    ) -> Tuple[Dict[Type[TestCase], List[TestCase]], Dict[str, TestCaseIO]]:
        """Returns sorted list of testcase_types from tests/testcases"""
        if not self.paths.testcases_dir.exists():
            return {}, io
        tests = {t: [] for t in self.testcase_picker.testcase_types}
        default_weight = self.config.testcase_weights.get("ALL", 1)
        default_timeout = self.config.timeouts.get("ALL", 1)
        for test in self.paths.testcases_dir.iterdir():
            if not test.is_file():
                continue
            testcase_type = self.testcase_picker.pick(test)
            if testcase_type is None:
                self.logger(f"No appropriate language for {test} found.")
                continue
            arglist = self.config.generate_arglists(test.name)
            shutil.copy(str(test), str(self.paths.temp_dir))
            tests[testcase_type].append(
                testcase_type(
                    self.paths.temp_dir / test.name,
                    self.config.timeouts.get(test.name, default_timeout),
                    arglist,
                    self.config.testcase_weights.get(test.name, default_weight),
                    io.pop(test.stem, EMPTY_TESTCASE_IO),
                )
            )
        # Allows consistent output
        for test_list in tests.values():
            test_list.sort(key=lambda t: t.path.name)
        return tests, io

    @staticmethod
    def _import_formatters(
        path_to_stdout_formatters: Path,
    ) -> Dict[str, Callable[[str], str]]:
        if path_to_stdout_formatters.exists():
            module = import_from_path("stdout_formatters", path_to_stdout_formatters)
            return {k: v for k, v in module.__dict__.items() if callable(v)}
        else:
            return {}

    def _precompile_submission(self, submission: Submission, logger):
        try:
            arglists = self.config.generate_arglists(submission.path.name)
            return submission.type.precompile_submission(
                submission.path,
                submission.dir,
                self.config.possible_source_file_stems,
                arglists[ArgList.SUBMISSION_PRECOMPILATION],
            )
        except Exception as e:  # type: ignore
            self.logger.print_precompilation_error_to_results_file(
                submission, self.config.total_points_possible, e, logger
            )

    def _get_testcase_output(self, submission: Submission, logger: BufferOutputLogger) -> float:
        """Returns grading info as a dict"""
        logger(f"Grading {get_submission_name(submission.path)}")
        precompiled_submission = self._precompile_submission(submission, logger)
        if precompiled_submission is None:
            return 0
        total_testcase_score = 0
        testcase_results = []
        # Note: self.stdout_only_tests are not included in self.tests
        allowed_tests = self.tests.get(submission.type, [])
        if not allowed_tests:
            # TODO: Replace all print statements with proper logging
            print(f"No testcase_utils suitable for the submission {submission.path.name} found.")
        submission.type.run_additional_testcase_operations_in_student_dir(submission.dir)
        for test in allowed_tests:
            logger(f"Running '{test.name}'")
            testcase_score, message = test.run(precompiled_submission)
            logger(message)
            testcase_results.append((test.name, message))
            total_testcase_score += testcase_score
        raw_student_score = total_testcase_score / (sum(t.weight for t in allowed_tests) or 1)
        normalized_student_score = raw_student_score * self.config.total_score_to_100_ratio
        self.logger.print_testcase_results_to_results_file(
            submission.path, testcase_results, normalized_student_score, logger
        )
        return normalized_student_score


class AutograderPaths:
    __slots__ = (
        "current_dir",
        "temp_dir",
        "results_dir",
        "output_summary",
        "tests_dir",
        "testcases_dir",
        "extra_dir",
        "input_dir",
        "output_dir",
        "stdout_formatters",
        "testcase_types_dir",
        "default_stdout_formatters",
        "config",
        "default_config",
        "required_dirs",
    )
    current_dir: Path
    temp_dir: Path
    results_dir: Path
    output_summary: Path
    tests_dir: Path

    testcases_dir: Path
    extra_dir: Path
    input_dir: Path
    output_dir: Path
    stdout_formatters: Path
    config: Path
    required_dirs: tuple

    testcase_types_dir: Path
    default_stdout_formatters: Path
    default_config: Path

    def __init__(self, current_dir):
        self.current_dir = current_dir
        self.temp_dir = current_dir / "temp"
        self.results_dir = current_dir / "results"
        self.output_summary = current_dir / "grader_output.txt"
        self.tests_dir = current_dir / "tests"

        self.testcases_dir = self.tests_dir / "testcases"
        self.extra_dir = self.tests_dir / "extra"
        self.input_dir = self.tests_dir / "input"
        self.output_dir = self.tests_dir / "output"

        self.stdout_formatters = self.tests_dir / "stdout_formatters.py"
        self.config = self.tests_dir / "config.ini"

        self.required_dirs = ()

        autograder_dir = Path(__file__).parent
        self.testcase_types_dir = autograder_dir / "testcase_types"
        self.default_stdout_formatters = autograder_dir / "default_stdout_formatters.py"
        self.default_config = autograder_dir / "default_config.ini"

    def generate_config(self):
        if not self.config.exists():
            if self.default_config.exists():
                shutil.copy(str(self.default_config), str(self.config))
            else:
                raise AutograderError(f"Failed to generate config:'{self.default_config}' not found.")


# Grades single submissions. We use it because multiprocessing.pool only accepts top-level callable objects.
class Runner:
    def __init__(self, grader, lock):
        self.grader: Grader = grader
        self.lock = lock

    def __call__(self, submission: Submission):
        return self.grader.run_on_single_submission(submission, self.lock)


@contextmanager
def temporarily_change_dir(new_dir):
    old_dir = Path.cwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(str(old_dir))
