import os
import sys
import shutil
from pathlib import Path
from typing import List
import logging
import configparser

import sh  # type: ignore

from . import testcases
from .util import get_stderr, ARGUMENT_LIST_NAMES, PATH_TO_DEFAULT_CONFIG, AutograderError, import_from_path

DEFAULT_SOURCE_FILE_STEM = "Homework"
ALLOWED_LANGUAGES = {
    "c": testcases.CTestCase,
    "java": testcases.JavaTestCase,
    "python": testcases.PythonTestCase,
    "c++": testcases.CPPTestCase
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
    def __init__(
            self,
            current_dir,
            no_output=False,
            submissions=None,
    ):
        self.current_dir = current_dir
        self.temp_dir = current_dir / "temp"
        self.tests_dir = current_dir / "tests"
        self.testcases_dir = self.tests_dir / "testcases"
        self.results_dir = current_dir / "results"
        self.path_to_output_summary = current_dir / "grader_output.txt"
        self.no_output = no_output
        self.submissions = submissions
        self.filters = None
        self.tests = None

    def run(self):
        self.temp_dir.mkdir(exist_ok=True)
        required_dirs = (self.testcases_dir,)
        dir_not_found = "{} directory not found. It is required for the grader to function.\n" \
                        "Maybe you specified the incorrect directory? Use `autograder submission_directory_here`"
        for directory in required_dirs:
            if not directory.exists():
                raise AutograderError(dir_not_found.format(directory))
        self._configure_grading()
        self._configure_logging()
        self.filters = self._import_formatters(self.tests_dir / "output_formatters.py")
        self.tests = self._gather_testcases()
        self.submissions = self._gather_submissions(self.submissions)
        self._copy_extra_files_to_temp(self.tests_dir / "extra")
        if self.generate_results:
            self.results_dir.mkdir(exist_ok=True)
        old_dir = Path.cwd()
        os.chdir(self.temp_dir)
        total_class_points = sum(map(self._run_tests_on_submission, self.submissions))
        class_average = total_class_points / (len(self.submissions) or 1)
        self.logger.info(f"\nAverage score: {round(class_average)}/{self.total_points_possible}")
        self.logger.info(KEY)
        self.cleanup()
        os.chdir(str(old_dir))
        return class_average

    def generate_config(self):
        config = self.tests_dir / "config.ini"
        if not config.exists():
            shutil.copy(str(PATH_TO_DEFAULT_CONFIG), str(config))

    def cleanup(self):
        shutil.rmtree(self.temp_dir)

    def _configure_grading(self):
        cfg = self._read_config()

        self.timeouts = self._parse_timeouts(cfg['TIMEOUT'])
        self.generate_results = cfg.getboolean('GENERATE_RESULTS')
        self.precompile_testcases = cfg.getboolean('PRECOMPILE_TESTCASES')

        self.total_points_possible = cfg.getint('TOTAL_POINTS_POSSIBLE')
        self.total_score_to_100_ratio = self.total_points_possible / 100

        language = cfg['PROGRAMMING_LANGUAGE']
        if language == "AUTO":
            self.testcase_types = self._figure_out_testcase_types()
        else:
            testcase_type = ALLOWED_LANGUAGES[language.lower().strip()]
            self.testcase_types = {testcase_type.source_suffix: testcase_type}

        self.assignment_name = cfg['ASSIGNMENT_NAME']

        source = cfg['SOURCE_FILE_NAME']
        if source == "AUTO":
            source = DEFAULT_SOURCE_FILE_STEM
            self.auto_source_file_name_enabled = True
        else:
            self.auto_source_file_name_enabled = False
        self.lower_source_filename = cfg.getboolean('LOWER_SOURCE_FILENAME')
        if self.lower_source_filename:
            source = source.lower()
        self.source_file_name = source

        self.testcase_weights = self._parse_testcase_weights(cfg['TESTCASE_WEIGHTS'])

        self.dont_expose_testcases = cfg.getboolean('DONT_EXPOSE_TESTCASES')

        # TODO: Name me better. The name is seriously bad
        self.argument_lists = {n: {} for n in ARGUMENT_LIST_NAMES}
        for arg_list_index, arg_list_name in ARGUMENT_LIST_NAMES.items():
            args = cfg[arg_list_name].split(",")
            for arg in args:
                if arg.strip():
                    testcase_name, arg_value = arg.split(":")
                    self.argument_lists[arg_list_index][testcase_name.strip()] = arg_value.strip().split(" ")

    def _read_config(self) -> configparser.SectionProxy:
        default_parser = configparser.ConfigParser()
        default_parser.read(PATH_TO_DEFAULT_CONFIG)

        path_to_user_config = self.tests_dir / "config.ini"
        user_parser = configparser.ConfigParser()
        user_parser.read_dict(default_parser)
        user_parser.read(path_to_user_config)

        return user_parser['CONFIG']

    def _figure_out_testcase_types(self) -> dict:
        testcase_types = {}
        for testcase in self.testcases_dir.iterdir():
            testcase_type = get_testcase_type_by_suffix(testcase.suffix)
            if testcase_type is not None:
                testcase_types[testcase_type.source_suffix] = testcase_type

        if testcase_types:
            return testcase_types
        else:
            raise AutograderError(f"Couldn't discover a testcase with correct suffix in {self.testcases_dir}")

    @staticmethod
    def _parse_testcase_weights(raw_weights: str):
        weights = {}
        for raw_weight in raw_weights.split(","):
            if raw_weight:
                testcase_name, weight = raw_weight.strip().split(":")
                weights[testcase_name.strip()] = float(weight)
        return weights

    @staticmethod
    def _parse_timeouts(raw_timeouts: str):
        timeouts = {}
        for raw_timeout in raw_timeouts.split(","):
            if raw_timeout:
                testcase_name, timeout = raw_timeout.strip().split(":")
                timeouts[testcase_name.strip()] = float(timeout)
        return timeouts

    def _configure_logging(self):
        self.logger = logging.getLogger("Grader")
        self.logger.setLevel(logging.INFO)
        if not self.no_output:
            self.logger.addHandler(logging.StreamHandler(sys.stdout))
            if self.path_to_output_summary.exists():
                ans = input("Output summary file already exists. Would you like to override it? (Yes/No) ")
                if ans.lower().startswith("y"):
                    self.logger.addHandler(logging.FileHandler(self.path_to_output_summary, mode="w"))
                else:
                    print("If you don't want to remove the summary, simply use the --no_output command line option."
                          "which will remove all stdout and file output except for --generate_results directory.")
                    exit(0)

    def _gather_testcases(self) -> List[testcases.TestCase]:
        tests = []
        default_weight = self.testcase_weights.get("ALL", 1)
        default_timeout = self.timeouts.get("ALL", 1)
        for test in self.testcases_dir.iterdir():
            weight = self.testcase_weights.get(test.name, default_weight)
            timeout = self.timeouts.get(test.name, default_timeout)
            testcase_type = self.testcase_types.get(test.suffix, None)
            if not test.is_file():
                continue
            if testcase_type is None:
                self.logger.info(f"No appropriate language for {test} found.")
                continue
            arglist = self._generate_arglists(test)
            shutil.copy(test, self.temp_dir)
            tests.append(testcase_type(
                self.temp_dir / test.name,
                self.tests_dir,
                timeout,
                self.filters,
                arglist,
                self.precompile_testcases,
                weight,
                self.per_char_formatting_disabled,
                self.full_output_formatting_disabled,
                self.dont_expose_testcases
            ))
        return tests

    def _generate_arglists(self, test: Path):
        arglist = {}
        for arglist_index, arglists_per_testcase in self.argument_lists.items():
            if test.name in arglists_per_testcase:
                arglist[arglist_index] = arglists_per_testcase[test.name]
            elif "ALL" in arglists_per_testcase:
                arglist[arglist_index] = arglists_per_testcase["ALL"]
            else:
                arglist[arglist_index] = tuple()
        return arglist

    def _gather_submissions(self, submissions_to_grade):
        submissions_to_grade = set(submissions_to_grade)
        submissions = []
        for submission in self.current_dir.iterdir():
            if submissions_to_grade and submission.name not in submissions_to_grade:
                continue
            submission_name = submission.name
            if self.lower_source_filename:
                submission_name = submission_name.lower()
            if submission.suffix in self.testcase_types:
                if self.auto_source_file_name_enabled:
                    submissions.append(submission)
                elif self.source_file_name in submission_name:
                    submissions.append(submission)
                else:
                    self.logger.info(f"{submission} does not contain the required suffix. Skipping it.")
        return submissions

    def _copy_extra_files_to_temp(self, extra_file_dir: Path):
        if extra_file_dir.exists():
            for path in extra_file_dir.iterdir():
                shutil.copy(str(path), str(self.temp_dir))

    def _import_formatters(self, path_to_output_formatters: Path):
        if path_to_output_formatters.exists():
            module = import_from_path("output_formatters", path_to_output_formatters)
            if hasattr(module, "per_char_formatter") and hasattr(module, "full_output_formatter"):
                self.per_char_formatting_disabled = False
                self.full_output_formatting_disabled = False
            elif not hasattr(module, "per_char_formatter") and not hasattr(module, "full_output_formatter"):
                raise AutograderError("Formatter file does not contain the required functions.")
            elif hasattr(module, "per_char_formatter"):
                self.per_char_formatting_disabled = False
                self.full_output_formatting_disabled = True
            elif hasattr(module, "per_char_formatter"):
                self.full_output_formatting_disabled = False
                self.per_char_formatting_disabled = True
            return module
        else:
            self.per_char_formatting_disabled = True
            self.full_output_formatting_disabled = True
            return None



    def _run_tests_on_submission(self, submission: Path):
        if self.generate_results:
            with open(self.results_dir / submission.name, "w") as f:
                grader_output = self._get_testcase_output(submission)
                f.write(format_grader_output(grader_output))
        else:
            grader_output = self._get_testcase_output(submission)
        return grader_output['student_score']

    def _get_testcase_output(self, submission) -> dict:
        """ Returns grading info as a dict """
        if "_" in submission.name:
            student_name = submission.name[:submission.name.find("_")]
        else:
            student_name = submission.name
        self.logger.info(f"Grading {student_name}")
        precompiled_submission = None
        try:
            # TODO: Move half of this into precompile_submission or something
            testcase_type = self.testcase_types[submission.suffix]
            source_file_path = Path(self.source_file_name).with_suffix(testcase_type.source_suffix)
            precompiled_submission = testcase_type.precompile_submission(
                submission, self.current_dir, source_file_path
            )
        except sh.ErrorReturnCode_1 as e:
            stderr = get_stderr(self.current_dir, e, "Failed to precompile")
            self.logger.info(stderr + f"\nResult: 0/{self.total_points_possible}\n")
            if precompiled_submission is not None:
                precompiled_submission.unlink()
            return {
                'assignment_name': self.assignment_name,
                'precompilation_error': stderr.replace('Failed to precompile', ''),
                'student_score': 0
            }
        total_testcase_score = 0
        testcase_results = []
        allowed_tests = [t for t in self.tests if t.source_suffix == submission.suffix]
        for test in self.tests:
            if test.source_suffix == submission.suffix:
                self.logger.info(f"Running '{test.name}'")
                testcase_score, message = test.run(precompiled_submission)
                self.logger.info(message)
                testcase_results.append((test.name, message))
                total_testcase_score += testcase_score
        raw_student_score = total_testcase_score / sum(t.weight for t in allowed_tests)
        normalized_student_score = raw_student_score * self.total_score_to_100_ratio
        student_final_result = f"{round(normalized_student_score)}/{self.total_points_possible}"
        self.logger.info(f"Result: {student_final_result}\n")
        precompiled_submission.unlink()
        return {
            'assignment_name': self.assignment_name,
            'testcase_results': testcase_results,
            'formatted_student_score': student_final_result,
            'student_score': normalized_student_score
        }


def get_testcase_type_by_suffix(suffix: str):
    for testcase_type in ALLOWED_LANGUAGES.values():
        if testcase_type.source_suffix == suffix:
            return testcase_type


def format_grader_output(output: dict):
    """ Replace this function with anything else if you want the output
        to have a different style
    """
    s = f"{output['assignment_name']} Test Results\n\n"
    s += "%-40s%s" % ("TestCase", "Result")
    s += "\n================================================================"
    if "precompilation_error" in output:
        s += output['precompilation_error']
        return s
    for test_output in output['testcase_results']:
        s += "\n%-40s%s" % test_output
    s += "\n================================================================\n"
    s += "Result: " + output['formatted_student_score']
    s += KEY
    return s
