import multiprocessing
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Dict, List, Set, Type, Tuple
import sh

from .config_manager import GradingConfig
from .output_summary import GradingOutputLogger, JsonGradingOutputLogger
from .testcase_utils.shell import get_stderr
from .testcase_utils.abstract_testcase import ArgList, TestCase
from .testcase_utils.stdout_testcase import StdoutOnlyTestCase
from .testcase_utils.submission import Submission, find_appropriate_source_file_stem
from .testcase_utils.testcase_picker import TestCasePicker
from .testcase_utils.testcase_io import TestCaseIO
from .util import AutograderError, hide_path_to_directory, import_from_path, get_file_stems, temporarily_change_dir

EMPTY_TESTCASE_IO = TestCaseIO.get_empty_io()


# TODO: What if grader built a less complex object whose only purpose is actually grading? Should improve complexity.
class Grader:
    json_output: bool
    submissions: List[Submission]
    tests: Dict[Type[TestCase], List[TestCase]]
    raw_submissions: List[Path]
    paths: "AutograderPaths"

    logger: GradingOutputLogger
    config: GradingConfig
    testcase_picker: TestCasePicker
    stdout_only_tests: list

    def __init__(self, current_dir: Path, json_output: bool = False, submissions=None):
        if submissions is None:
            submissions = []
        self.json_output = json_output
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
            logger_type = JsonGradingOutputLogger if self.json_output else GradingOutputLogger
            self.logger = logger_type(
                self.paths.results_dir,
                self.config.assignment_name,
                self.config.total_points_possible,
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
                modified_submissions = pool.map(Runner(self, man.Lock()), self.submissions)
                total_class_points = sum(s.final_grade for s in modified_submissions)
            class_average = round(total_class_points / len(self.submissions))
            self.logger.print_final_score(modified_submissions, class_average)
            self.logger.print_key()
        finally:
            for io in io_choices.values():
                io.cleanup()
            self.cleanup()
        return class_average

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
                    pass
                    # TODO: Figure out what to do with this
                    # self.logger(f"{submission_path} does not contain the required file name. Skipping it.")

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
                # No logging is allowed because of json mode
                # self.logger(f"No appropriate language for {test} found.")
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
    def _import_formatters(path_to_stdout_formatters: Path) -> Dict[str, Callable[[str], str]]:
        if path_to_stdout_formatters.exists():
            module = import_from_path("stdout_formatters", path_to_stdout_formatters)
            return {k: v for k, v in module.__dict__.items() if callable(v)}
        else:
            return {}


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


class Runner:
    """Grades single submissions"""

    def __init__(self, grader, lock):
        self.grader: Grader = grader
        self.lock = lock

    def __call__(self, submission: Submission) -> Submission:
        self.run_on_single_submission(submission, self.lock)
        return submission

    def run_on_single_submission(self, submission: Submission, lock):
        with temporarily_change_dir(submission.dir):
            self._copy_extra_files(submission.dir)
            self._get_testcase_output(submission)
            with lock:
                self.grader.logger.print_single_student_grading_results(submission)
        # Cleanup after running tests on student submission
        shutil.rmtree(submission.dir)

    def _copy_extra_files(self, to_dir: Path):
        if self.grader.paths.extra_dir.exists():
            for path in self.grader.paths.extra_dir.iterdir():
                new_path = to_dir / path.name
                shutil.copy(str(path), str(new_path))

    # TODO: rename to "_run_testcases_on_submission" or something
    def _get_testcase_output(self, submission: Submission):
        """Grades single submission and returns its normalized score

        Note: Has side effects in submission instance
        """
        try:
            precompiled_submission = self._precompile_submission(submission)
        except sh.ErrorReturnCode as e:
            error = hide_path_to_directory(get_stderr(e, "Failed to precompile:"), submission.dir)
            submission.register_precompilation_error(error)
            return 0
        allowed_tests = self.grader.tests.get(submission.type, [])
        if not allowed_tests:
            submission.register_precompilation_error("No suitable testcases found.")
            return 0
        submission.type.run_additional_testcase_operations_in_student_dir(submission.dir)
        for test in allowed_tests:
            testcase_score, message = test.run(precompiled_submission)
            submission.add_grade(test.name, testcase_score, test.weight, message)
        submission.register_final_grade(self.grader.config.total_score_to_100_ratio)

    def _precompile_submission(self, submission: Submission) -> Path:
        arglists = self.grader.config.generate_arglists(submission.path.name)
        return submission.type.precompile_submission(
            submission.path,
            submission.dir,
            self.grader.config.possible_source_file_stems,
            arglists[ArgList.SUBMISSION_PRECOMPILATION],
        )
