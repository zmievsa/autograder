from .testcases.util.testcase_io import TestCaseIO
from .testcases.multifile import MultifileTestCase, is_multifile_submission
import multiprocessing
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from stat import S_IRGRP, S_IROTH, S_IRUSR, S_IWUSR, S_IXUSR
from typing import Callable, Dict, List, Set, Tuple, Type

import sh

from .testcases.abstract_base_class import ArgList, TestCase, submission_is_allowed

from .testcases import Submission
from .config_manager import GradingConfig
from .output_summary import BufferOutputLogger, GradingOutputLogger, get_submission_name
from .util import AutograderError, import_from_path

READ_EXECUTE_PERMISSION = S_IRUSR ^ S_IRGRP ^ S_IROTH ^ S_IXUSR
READ_EXECUTE_WRITE_PERMISSION = READ_EXECUTE_PERMISSION ^ S_IWUSR


class Grader:
    no_output: bool
    submissions: List[Submission]
    tests: Dict[Type[TestCase], List[TestCase]]
    raw_submissions: List[Path]
    paths: "AutograderPaths"
    multifile_submissions_found: bool

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
            self.config = GradingConfig(self.paths.testcases_dir, self.paths.config, self.paths.default_config)
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
            self.submissions, self.multifile_submissions_found = self._gather_submissions(self.raw_submissions)
            io_choices = self._gather_io()
            self.tests = self._gather_testcases(io_choices)  # also copies testcases to temp dir
            if self.multifile_submissions_found:
                self.tests[MultifileTestCase] = self._generate_multifile_testcases(io_choices)
            process_count = multiprocessing.cpu_count() if self.config.parallel_grading_enabled else 1
            with multiprocessing.Pool(process_count) as pool:
                man = multiprocessing.Manager()
                total_class_points = sum(pool.map(Runner(self, man.Lock()), self.submissions))
            class_average = total_class_points / len(self.submissions)
            self.logger(f"\nAverage score: {round(class_average)}/{self.config.total_points_possible}")
            self.logger.print_key()
        finally:
            self.cleanup()
            for io in io_choices.values():
                io.cleanup()
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

    def _gather_submissions(self, submissions_to_grade) -> Tuple[List[Submission], bool]:
        """ Returns sorted list of paths to submissions """
        submissions_to_grade = set(submissions_to_grade)
        submissions: List[Submission] = []
        multifile_submissions_found = False
        for submission_path in self.paths.current_dir.iterdir():
            if submissions_to_grade and submission_path.name not in submissions_to_grade:
                continue

            testcase_type = self.config.testcase_types.get(submission_path.suffix, None)
            if testcase_type is not None:
                if self.config.auto_source_file_name_enabled:
                    submissions.append(Submission(submission_path, testcase_type, self.paths.temp_dir))
                elif submission_is_allowed(
                    submission_path,
                    self.config.possible_source_file_stems,
                    self.config.source_file_stem_is_case_insensitive,
                ):
                    submissions.append(Submission(submission_path, testcase_type, self.paths.temp_dir))
                else:
                    self.logger(f"{submission_path} does not contain the required file name. Skipping it.")
            elif (
                self.config.multifile_submissions_enabled
                and submission_path.is_dir()
                and is_multifile_submission(
                    submission_path,
                    self.config.possible_source_file_stems,
                    self.config.source_file_stem_is_case_insensitive,
                )
            ):
                submissions.append(Submission(submission_path, MultifileTestCase, self.paths.temp_dir))
                multifile_submissions_found = True

        if not len(submissions):
            raise AutograderError(f"No student submissions found in '{self.paths.current_dir}'.")

        # Allows consistent output
        submissions.sort(key=lambda s: s.path)
        return submissions, multifile_submissions_found

    def _gather_io(self) -> Dict[str, TestCaseIO]:
        GET_FILE_STEMS = lambda d: (p.stem for p in d.iterdir()) if d.exists() else []
        outputs = GET_FILE_STEMS(self.paths.output_dir)
        inputs = GET_FILE_STEMS(self.paths.input_dir)
        io: Set[str] = set().union(outputs, inputs)
        dict_io = {p: TestCaseIO(p, self.stdout_formatters, self.paths.input_dir, self.paths.output_dir) for p in io}
        return dict_io

    def _generate_multifile_testcases(self, io_choices: Dict[str, TestCaseIO]) -> List[TestCase]:
        default_timeout = self.config.timeouts.get("ALL", 1)
        default_weight = self.config.testcase_weights.get("ALL", 1)
        return [
            MultifileTestCase(
                self.paths.temp_dir,
                self.config.timeouts.get(io.name, default_timeout),
                {},
                self.config.anti_cheat,
                self.config.testcase_weights.get(io.name, default_weight),
                io_choices,
            )
            for io in io_choices.values()
            if io.expected_output
        ]

    def _gather_testcases(self, io) -> Dict[Type[TestCase], List[TestCase]]:
        """ Returns sorted list of testcases from tests/testcases """
        tests = {t: [] for t in self.config.testcase_types.values()}
        default_weight = self.config.testcase_weights.get("ALL", 1)
        default_timeout = self.config.timeouts.get("ALL", 1)
        for test in self.paths.testcases_dir.iterdir():
            weight = self.config.testcase_weights.get(test.name, default_weight)
            timeout = self.config.timeouts.get(test.name, default_timeout)
            testcase_type = self.config.testcase_types.get(test.suffix, None)
            if not test.is_file():
                continue
            if testcase_type is None:
                self.logger(f"No appropriate language for {test} found.")
                continue
            arglist = self.config.generate_arglists(test.name)
            shutil.copy(test, self.paths.temp_dir)
            tests[testcase_type].append(
                testcase_type(  # type: ignore # The typing error here appears due to the limitations of python's typing
                    self.paths.temp_dir / test.name,
                    timeout,
                    arglist,
                    self.config.anti_cheat,
                    weight,
                    io,
                )
            )
        # Allows consistent output
        for test_list in tests.values():
            test_list.sort(key=lambda t: t.path.name)
        return tests

    def _import_formatters(self, path_to_stdout_formatters: Path) -> Dict[str, Callable[[str], str]]:
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
                self.config.source_file_stem_is_case_insensitive,
                arglists[ArgList.SUBMISSION_PRECOMPILATION],
            )
        except Exception as e:  # type: ignore
            self.logger.print_precompilation_error_to_results_file(
                submission, self.config.total_points_possible, e, logger
            )

    def _get_testcase_output(self, submission: Submission, logger: BufferOutputLogger) -> float:
        """ Returns grading info as a dict """
        logger(f"Grading {get_submission_name(submission.path)}")
        precompiled_submission = self._precompile_submission(submission, logger)
        if precompiled_submission is None:
            return 0
        total_testcase_score = 0
        testcase_results = []
        allowed_tests = self.tests[submission.type]
        if not allowed_tests:
            print(f"No testcases suitable for the submission {submission.path.name} found.")
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
    default_stdout_formatters: Path
    config: Path
    default_config: Path

    required_dirs: tuple

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

        autograder_dir = Path(__file__).parent
        self.default_stdout_formatters = autograder_dir / "default_stdout_formatters.py"
        self.default_config = autograder_dir / "default_config.ini"

        self.required_dirs = (self.testcases_dir,)

    def generate_config(self):
        if not self.config.exists():
            if self.default_config.exists():
                shutil.copy(self.default_config, self.config)
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
        os.chdir(old_dir)
