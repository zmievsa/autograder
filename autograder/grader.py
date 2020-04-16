import os
import sys
import shutil
from io import StringIO
from pathlib import Path
from typing import List
import logging
import configparser

import sh

from . import testcases
from .util import get_stderr, print_results
from .filters import ALLOWED_FILTERS

DEFAULT_SOURCE_FILE_STEM = "Homework"
PATH_TO_DEFAULT_CONFIG = Path(__file__).parent / "default_config.ini"
ALLOWED_LANGUAGES = {
    "c": testcases.CTestCase,
    "java": testcases.JavaTestCase,
    "python": testcases.PythonTestCase
}
# Constants
KEY = """
\nKey:
\tFailed to Compile: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings: Your submission uses unchecked or unsafe operations
\tCrashed due to signal SIGNAL_CODE: Your submission threw an uncaught exception.
\tAll signal error codes are described here: http://man7.org/linux/man-pages/man7/signal.7.html
\tExceeded Time Limit: Your submission took too much time to run (probably an infinite loop)
"""


class Grader:
    # TODO: Add config reading from ini
    def __init__(self, current_dir, generate_results=False):
        self.generate_results = generate_results
        self.current_dir = current_dir
        self.temp_dir = current_dir / "temp"
        self.tests_dir = current_dir / "tests"
        self.testcases_dir = self.tests_dir / "testcases"
        self.results_dir = current_dir / "results"
        self.path_to_output_summary = current_dir / "grader_output.txt"
        self._check_required_dirs_exist()
        self.temp_dir.mkdir(exist_ok=True)
        if generate_results:
            self.results_dir.mkdir(exist_ok=True)
        self._configure_grading()
        self._configure_logging()
        self.tests = self._gather_testcases()
        self.submissions = self._gather_submissions()

    def run(self):
        old_dir = Path.cwd()
        os.chdir(self.temp_dir)
        total_class_points = sum(map(self._run_tests_on_submission, self.submissions))
        class_average = total_class_points / (len(self.submissions) or 1)
        self.logger.info(f"\nAverage score: {round(class_average)}/{self.total_points_possible}")
        self.logger.info(KEY)
        self.cleanup()
        os.chdir(old_dir)
        return class_average

    def cleanup(self):
        shutil.rmtree(self.temp_dir)
    
    def _check_required_dirs_exist(self):
        REQUIRED_DIRS = (
            self.tests_dir, self.testcases_dir,
            self.tests_dir / "input", self.tests_dir / "output"
        )
        dir_not_found = "{} directory not found. It is required for the grader to function."
        for directory in REQUIRED_DIRS:
            if not directory.exists():
                raise FileNotFoundError(dir_not_found.format(directory))
    
    def _configure_grading(self):
        cfg = self._read_config()
        self.timeout = cfg.getint('TIMEOUT')
        self.total_points_possible = cfg.getint('TOTAL_POINTS_POSSIBLE')
        self.total_score_to_100_ratio = self.total_points_possible / 100
        language = cfg['PROGRAMMING_LANGUAGE']
        if language == "AUTO":
            self.TestCaseType = self._figure_out_testcase_type()
        else:
            self.TestCaseType = ALLOWED_LANGUAGES[language.lower().strip()]
        self.assignment_name = cfg['ASSIGNMENT_NAME']
        source = cfg['SOURCE_FILE_NAME']
        if source == "AUTO":
            source = DEFAULT_SOURCE_FILE_STEM + self.TestCaseType.source_suffix
        self.lower_source_filename = cfg.getboolean('LOWER_SOURCE_FILENAME')
        if self.lower_source_filename:
            source = source.lower()
        self.source_file_name = source
        self.filters = [ALLOWED_FILTERS[f.strip()] for f in cfg['FILTERS'].split(",") if f]
    
    def _read_config(self) -> configparser.ConfigParser:
        default_parser = configparser.ConfigParser()
        default_parser.read(PATH_TO_DEFAULT_CONFIG)
        user_parser = configparser.ConfigParser()
        user_parser.read_dict(default_parser)
        user_parser.read(self.tests_dir / "config.ini")
        return user_parser['CONFIG']
    
    def _figure_out_testcase_type(self):
        for testcase in self.testcases_dir.iterdir():
            testcase_type = get_testcase_type_by_suffix(testcase.suffix)
            if testcase_type is not None:
                return testcase_type
        raise FileNotFoundError(
            f"Couldn't discover a testcase with correct suffix in {self.testcases_dir}"
        )

    def _configure_logging(self):
        self.logger = logging.getLogger("Grader")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.logger.addHandler(logging.FileHandler(self.path_to_output_summary, mode="w"))
    
    def _gather_testcases(self) -> List[testcases.TestCase]:
        tests = []
        for test in (self.testcases_dir).iterdir():
            if not (test.is_file() and self.TestCaseType.source_suffix in test.name):
                continue
            shutil.copy(test, self.temp_dir)
            tests.append(self.TestCaseType(
                self.temp_dir / test.name,
                self.tests_dir,
                self.timeout,
                self.filters
            ))
        return tests
    
    def _gather_submissions(self):
        submissions = []
        for submission in self.current_dir.iterdir():
            submission_name = submission.name
            if self.lower_source_filename:
                submission_name = submission_name.lower()
            if self.source_file_name in submission_name:
                submissions.append(submission)
        return submissions
    
    def _run_tests_on_submission(self, submission: Path):
        if self.generate_results:
            with open(self.results_dir / submission.name, "w") as f:
                return self._run_tests_on_submission_with_log(submission, f.write)
        else:
            return self._run_tests_on_submission_with_log(submission, lambda s: 0)

    def _run_tests_on_submission_with_log(self, submission, log):
        # TODO: Maybe make this function return a dict that can be
        # used to format the final log file. This would make changing
        # the log file format SUPER easy.
        testcase_count = len(self.tests)
        if "_" in submission.name:
            student_name = submission.name[:submission.name.find("_")]
        else:
            student_name = submission.name
        self.logger.info(f"Grading {student_name}")
        log(f"{self.assignment_name} Test Results\n\n")
        log("%-40s%s" % ("TestCase", "Result"))
        log("\n================================================================")
        try:
            precompiled_submission = self.TestCaseType.precompile_submission(submission, self.current_dir, self.source_file_name)
        except sh.ErrorReturnCode_1 as e:
            stderr = get_stderr(e, "Failed to precompile")
            self.logger.info(stderr + f"\nResult: 0/{self.total_points_possible}\n")
            log(f"\nYour file failed to compile{stderr.replace('Failed to precompile', '')}")
            return 0
        total_testcase_score = 0
        for test in self.tests:
            self.logger.info(f"Running '{test.name}'")
            testcase_score, message = test.run(precompiled_submission)
            self.logger.info(message)
            log("\n%-40s%s" % (test.name, message))
            total_testcase_score += testcase_score
        student_score = total_testcase_score / testcase_count * self.total_score_to_100_ratio
        student_final_result = f"{round(student_score)}/{self.total_points_possible}"
        self.logger.info(f"Result: {student_final_result}\n")
        log("\n================================================================\n")
        log("Result: " + student_final_result)
        log(KEY)
        return student_score


def get_testcase_type_by_suffix(suffix: str):
    for testcase_type in ALLOWED_LANGUAGES.values():
        if testcase_type.source_suffix == suffix:
            return testcase_type
