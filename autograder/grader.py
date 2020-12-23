from autograder.testcases.java import JavaTestCase
import multiprocessing
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from stat import S_IRGRP, S_IROTH, S_IRUSR, S_IWUSR, S_IXUSR
from typing import Callable, Dict, List, Optional

import sh

from autograder.testcases.abstract_base_class import ArgList

from . import testcases
from .config_manager import GradingConfig
from .output_summary import BufferOutputLogger, GradingOutputLogger, get_submission_name
from .util import AutograderError, import_from_path

READ_EXECUTE_PERMISSION = S_IRUSR ^ S_IRGRP ^ S_IROTH ^ S_IXUSR
READ_EXECUTE_WRITE_PERMISSION = READ_EXECUTE_PERMISSION ^ S_IWUSR


class Grader:
    no_output: bool
    submissions: List[Path]
    tests: List[testcases.TestCase]
    raw_submissions: List[Path]
    paths: "AutograderPaths"

    def __init__(self, current_dir, no_output=False, submissions=None):
        if submissions is None:
            submissions = []
        self.no_output = no_output
        self.raw_submissions = submissions
        self.output_formatters = {}
        self.paths = AutograderPaths(current_dir)

    def run(self):
        try:
            self.output_formatters = self._import_formatters(self.paths.output_formatters)
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
            self.submissions = self._gather_submissions(self.raw_submissions)
            self._prepare_directory_structure()
            self.tests = self._gather_testcases()  # also copies testcases to temp dir
            process_count = multiprocessing.cpu_count() if self.config.parallel_grading_enabled else 1
            with multiprocessing.Pool(process_count) as pool:
                man = multiprocessing.Manager()
                total_class_points = sum(pool.map(Runner(self, man.Lock()), self.submissions))
            class_average = total_class_points / len(self.submissions)
            self.logger(f"\nAverage score: {round(class_average)}/{self.config.total_points_possible}")
            self.logger.print_key()
        finally:
            self.cleanup()
        return class_average

    def run_on_single_submission(self, submission, lock):
        student_dir = self.paths.temp_dir / submission.name
        student_dir.mkdir()
        with temporarily_change_dir(student_dir):
            self._copy_extra_files(student_dir)
            with self.logger.single_submission_output_logger(lock) as logger:
                result = self._get_testcase_output(submission, student_dir, logger)
        # Cleanup after running tests on student submission
        shutil.rmtree(student_dir)
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
                # os.chmod(new_path, READ_EXECUTE_PERMISSION)

    def _check_required_directories_exist(self):
        for directory in self.paths.required_dirs:
            if not directory.exists():
                raise AutograderError(
                    f"{directory} directory not found. It is required for the grader to function.\n"
                    "Maybe you specified the incorrect directory? Use `autograder submission_directory_here`"
                )

    def _gather_testcases(self) -> List[testcases.TestCase]:
        """ Returns sorted list of testcases from tests/testcases """
        tests = []
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
            arglist = self.config._generate_arglists(test.name)
            shutil.copy(test, self.paths.temp_dir)
            tests.append(
                testcase_type(
                    self.paths.temp_dir / test.name,
                    self.config.source_file_name,
                    self.paths.input_dir,
                    self.paths.output_dir,
                    timeout,
                    self.output_formatters,
                    arglist,
                    self.config.anti_cheat,
                    weight,
                    self.per_char_formatting_enabled,
                    self.full_output_formatting_enabled,
                )
            )
        # Allows consistent output
        tests.sort(key=lambda t: t.path.name)
        return tests

    def _gather_submissions(self, submissions_to_grade) -> List[Path]:
        """ Returns sorted list of paths to submissions """
        submissions_to_grade = set(submissions_to_grade)
        submissions: List[Path] = []
        for submission in self.paths.current_dir.iterdir():
            if submissions_to_grade and submission.name not in submissions_to_grade:
                continue
            submission_name = submission.name
            if self.config.lower_source_filename:
                submission_name = submission_name.lower()
            if submission.suffix in self.config.testcase_types:
                if self.config.auto_source_file_name_enabled:
                    submissions.append(submission)
                elif self.config.source_file_name in submission_name:
                    submissions.append(submission)
                else:
                    self.logger(f"{submission} does not contain the required file name. Skipping it.")

        if not len(submissions):
            raise AutograderError(f"No student submissions found in '{self.paths.current_dir}'.")

        # Allows consistent output
        submissions.sort()
        return submissions

    def _import_formatters(self, path_to_output_formatters: Path) -> Dict[str, Callable[[str], str]]:
        if path_to_output_formatters.exists():
            module = import_from_path("output_formatters", path_to_output_formatters)
            self.per_char_formatting_enabled = hasattr(module, "per_char_formatter")
            self.full_output_formatting_enabled = hasattr(module, "full_output_formatter")
            if not self.per_char_formatting_enabled and not self.full_output_formatting_enabled:
                raise AutograderError("Formatter file does not contain the required functions.")
            return {k: v for k, v in module.__dict__.items() if callable(v)}
        else:
            self.per_char_formatting_enabled = False
            self.full_output_formatting_enabled = False
            return {}

    def _precompile_submission(self, submission: Path, student_dir: Path, logger):
        precompiled_submission = None
        try:
            arglists = self.config._generate_arglists(submission.name)
            testcase_type = self.config.testcase_types[submission.suffix]
            source_file_path = Path(self.config.source_file_name).with_suffix(testcase_type.source_suffix)
            precompiled_submission = testcase_type.precompile_submission(
                submission, student_dir, source_file_path.name, arglists[ArgList.SUBMISSION_PRECOMPILATION]
            )
            return precompiled_submission
        except sh.ErrorReturnCode_1 as e:  # type: ignore
            self.logger.print_precompilation_error_to_results_file(submission, e, logger)
            return None

    def _get_testcase_output(self, submission: Path, student_dir: Path, logger: BufferOutputLogger) -> float:
        """ Returns grading info as a dict """
        logger(f"Grading {get_submission_name(submission)}")
        precompiled_submission = self._precompile_submission(submission, student_dir, logger)

        if precompiled_submission is None:
            return 0
        total_testcase_score = 0
        testcase_results = []
        allowed_tests = [t for t in self.tests if t.source_suffix == submission.suffix]
        if any(isinstance(t, JavaTestCase) for t in allowed_tests):
            JavaTestCase.run_additional_testcase_operations_in_student_dir(student_dir)
        for test in allowed_tests:
            logger(f"Running '{test.name}'")
            testcase_score, message = test.run(precompiled_submission)

            logger(message)
            testcase_results.append((test.name, message))
            total_testcase_score += testcase_score
        raw_student_score = total_testcase_score / sum(t.weight for t in allowed_tests)
        normalized_student_score = raw_student_score * self.config.total_score_to_100_ratio
        self.logger.print_testcase_results_to_results_file(
            submission, testcase_results, normalized_student_score, logger
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
        "output_formatters",
        "default_output_formatters",
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
    output_formatters: Path
    default_output_formatters: Path
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

        self.output_formatters = self.tests_dir / "output_formatters.py"
        self.config = self.tests_dir / "config.ini"

        autograder_dir = Path(__file__).parent
        self.default_output_formatters = autograder_dir / "default_formatters.py"
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

    def __call__(self, submission):
        return self.grader.run_on_single_submission(submission, self.lock)


@contextmanager
def temporarily_change_dir(new_dir):
    old_dir = Path.cwd()
    os.chdir(new_dir)
    try:
        yield
    except Exception as e:
        raise e
    finally:
        os.chdir(old_dir)
