import configparser
import logging
import os
import shutil
import sys
from pathlib import Path
from stat import S_IRGRP, S_IROTH, S_IRUSR, S_IWUSR, S_IXUSR
from typing import List, Optional

import sh  # type: ignore

from .grading_output import BufferOutputLogger, GradingOutputLogger, format_output_for_student_file, get_submission_name
from . import testcases
from .util import (
    ARGUMENT_LIST_NAMES,
    PATH_TO_DEFAULT_CONFIG,
    AutograderError,
    get_stderr,
    import_from_path,
)

READ_EXECUTE_PERMISSION = S_IRUSR ^ S_IRGRP ^ S_IROTH ^ S_IXUSR
READ_EXECUTE_WRITE_PERMISSION = READ_EXECUTE_PERMISSION ^ S_IWUSR

DEFAULT_SOURCE_FILE_STEM = "Homework"
ALLOWED_LANGUAGES = {
    "c": testcases.CTestCase,
    "java": testcases.JavaTestCase,
    "python": testcases.PythonTestCase,
    "c++": testcases.CPPTestCase,
}


class Grader:
    current_dir: Path
    temp_dir: Path
    tests_dir: Path
    testcases_dir: Path
    results_dir: Path
    path_to_output_summary: Path
    no_output: bool
    submissions: List[Path]
    tests: List[testcases.TestCase]

    # TODO: Check that the types are the ones sent from CLI and test.py
    raw_submissions: Optional[List[Path]]

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
        self.filters = None
        self.raw_submissions = submissions

        self.required_dirs = (self.testcases_dir,)

    def run(self):
        old_dir = Path.cwd()
        try:
            self.filters = self._import_formatters(self.tests_dir / "output_formatters.py")
            self._configure_grading()
            self.logger = GradingOutputLogger(
                self.current_dir,
                self.path_to_output_summary,
                self.results_dir,
                self.assignment_name,
                self.total_points_possible,
                self.no_output,
                self.generate_results,
            )
            self.submissions = self._gather_submissions(self.raw_submissions)
            self._prepare_directory_structure()
            os.chdir(self.temp_dir)

            total_class_points = sum(map(self._run_tests_on_submission, self.submissions))

            class_average = total_class_points / len(self.submissions)
            self.logger(f"\nAverage score: {round(class_average)}/{self.total_points_possible}")
            self.logger.print_key()
        finally:
            self.cleanup()
            os.chdir(str(old_dir))
        return class_average

    def generate_config(self):
        config = self.tests_dir / "config.ini"
        if not config.exists():
            shutil.copy(str(PATH_TO_DEFAULT_CONFIG), str(config))

    def cleanup(self):
        # Not sure if we need this
        # for path in self.temp_dir.iterdir():
        #     os.chmod(path, READ_EXECUTE_WRITE_PERMISSION)
        shutil.rmtree(self.temp_dir)

    def _prepare_directory_structure(self):
        # Cleanup in case any error
        if self.temp_dir.exists():
            self.cleanup()
        self.temp_dir.mkdir()
        self._copy_extra_files_to_temp(self.tests_dir / "extra")
        self._check_required_directories_exist()
        self.tests = self._gather_testcases()
        if self.generate_results:
            self.results_dir.mkdir(exist_ok=True)

    def _check_required_directories_exist(self):
        for directory in self.required_dirs:
            if not directory.exists():
                raise AutograderError(
                    f"{directory} directory not found. It is required for the grader to function.\n"
                    "Maybe you specified the incorrect directory? Use `autograder submission_directory_here`"
                )

    def _configure_grading(self):
        cfg = self._read_config()

        self.timeouts = parse_config_list(cfg["TIMEOUT"], float)
        self.generate_results = cfg.getboolean("GENERATE_RESULTS")
        self.anti_cheat = cfg.getboolean("ANTI_CHEAT")

        self.total_points_possible = cfg.getint("TOTAL_POINTS_POSSIBLE")
        self.total_score_to_100_ratio = self.total_points_possible / 100

        language = cfg["PROGRAMMING_LANGUAGE"]
        if language == "AUTO":
            self.testcase_types = self._figure_out_testcase_types()
        else:
            testcase_type = ALLOWED_LANGUAGES[language.lower().strip()]
            self.testcase_types = {testcase_type.source_suffix: testcase_type}

        self.assignment_name = cfg["ASSIGNMENT_NAME"]

        source = cfg["SOURCE_FILE_NAME"]
        if source == "AUTO":
            source = DEFAULT_SOURCE_FILE_STEM
            self.auto_source_file_name_enabled = True
        else:
            self.auto_source_file_name_enabled = False
        self.lower_source_filename = cfg.getboolean("LOWER_SOURCE_FILENAME")
        if self.lower_source_filename:
            source = source.lower()
        self.source_file_name = source

        self.testcase_weights = parse_config_list(cfg["TESTCASE_WEIGHTS"], float)

        # TODO: Name me better. The name is seriously bad
        self.cli_argument_lists = self._parse_arglists(cfg)

    def _read_config(self) -> configparser.SectionProxy:
        default_parser = configparser.ConfigParser()
        default_parser.read(str(PATH_TO_DEFAULT_CONFIG))

        path_to_user_config = self.tests_dir / "config.ini"
        user_parser = configparser.ConfigParser()
        user_parser.read_dict(default_parser)
        user_parser.read(path_to_user_config)

        return user_parser["CONFIG"]

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
    def _parse_arglists(cfg):
        argument_lists = {n: {} for n in ARGUMENT_LIST_NAMES}
        for arg_list_index, arg_list_name in ARGUMENT_LIST_NAMES.items():
            arg_list = parse_config_list(cfg[arg_list_name], str)
            for testcase_name, args in arg_list.items():
                argument_lists[arg_list_index][testcase_name] = args.strip().split(" ")
        return argument_lists

    def _gather_testcases(self) -> List[testcases.TestCase]:
        """ Returns sorted list of testcases from tests/testcases """
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
                self.logger(f"No appropriate language for {test} found.")
                continue
            arglist = self._generate_arglists(test)
            shutil.copy(test, self.temp_dir)
            tests.append(
                testcase_type(
                    self.temp_dir / test.name,
                    self.tests_dir,
                    timeout,
                    self.filters,
                    arglist,
                    self.anti_cheat,
                    weight,
                    not self.per_char_formatting_enabled,
                    not self.full_output_formatting_enabled,
                )
            )
        # Allows consistent output
        tests.sort(key=lambda t: t.path.name)
        return tests

    def _generate_arglists(self, test: Path):
        arglist = {}
        for arglist_index, arglists_per_testcase in self.cli_argument_lists.items():
            if test.name in arglists_per_testcase:
                arglist[arglist_index] = arglists_per_testcase[test.name]
            elif "ALL" in arglists_per_testcase:
                arglist[arglist_index] = arglists_per_testcase["ALL"]
            else:
                arglist[arglist_index] = tuple()
        return arglist

    def _gather_submissions(self, submissions_to_grade) -> List[Path]:
        """ Returns sorted list of paths to submissions """
        submissions_to_grade = set(submissions_to_grade)
        submissions: List[Path] = []
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
                    self.logger(f"{submission} does not contain the required file name. Skipping it.")

        if not len(submissions):
            raise AutograderError(f"No student submissions found in '{self.current_dir}'.")

        # Allows consistent output
        submissions.sort()
        return submissions

    def _copy_extra_files_to_temp(self, extra_file_dir: Path):
        if extra_file_dir.exists():
            for path in extra_file_dir.iterdir():
                new_path = self.temp_dir / path.name
                shutil.copy(str(path), str(new_path))
                os.chmod(new_path, READ_EXECUTE_PERMISSION)

    def _import_formatters(self, path_to_output_formatters: Path):
        if path_to_output_formatters.exists():
            module = import_from_path("output_formatters", path_to_output_formatters)
            self.per_char_formatting_enabled = hasattr(module, "per_char_formatter")
            self.full_output_formatting_enabled = hasattr(module, "full_output_formatter")
            if not self.per_char_formatting_enabled and not self.full_output_formatting_enabled:
                raise AutograderError("Formatter file does not contain the required functions.")
            return module
        else:
            self.per_char_formatting_enabled = False
            self.full_output_formatting_enabled = False
            return None

    def _run_tests_on_submission(self, submission: Path):
        with self.logger.single_submission_output_logger() as logger:
            return self._get_testcase_output(submission, logger)

    def _get_testcase_output(self, submission, logger: BufferOutputLogger) -> float:
        """ Returns grading info as a dict """
        logger(f"Grading {get_submission_name(submission)}")
        precompiled_submission = self._precompile_submission(submission, logger)
        if precompiled_submission is None:
            return 0
        total_testcase_score = 0
        testcase_results = []
        allowed_tests = [t for t in self.tests if t.source_suffix == submission.suffix]
        for test in allowed_tests:
            logger(f"Running '{test.name}'")
            testcase_score, message = test.run(precompiled_submission)
            logger(message)
            testcase_results.append((test.name, message))
            total_testcase_score += testcase_score
        raw_student_score = total_testcase_score / sum(t.weight for t in allowed_tests)
        normalized_student_score = raw_student_score * self.total_score_to_100_ratio
        self.logger.print_testcase_results_to_results_file(
            submission, testcase_results, normalized_student_score, logger
        )

        precompiled_submission.unlink()
        return normalized_student_score

    def _precompile_submission(self, submission, logger):
        precompiled_submission = None
        try:
            # TODO: Move half of this into precompile_submission or something
            testcase_type = self.testcase_types[submission.suffix]
            source_file_path = Path(self.source_file_name).with_suffix(testcase_type.source_suffix)
            precompiled_submission = testcase_type.precompile_submission(submission, self.current_dir, source_file_path)
        except sh.ErrorReturnCode_1 as e:  # type: ignore
            self.logger.print_precompilation_error_to_results_file(submission, e, logger)
            # TODO: We should remove it with the entire student directory
            if precompiled_submission is not None:
                precompiled_submission.unlink()
                precompiled_submission = None
        return precompiled_submission


def get_testcase_type_by_suffix(suffix: str):
    for testcase_type in ALLOWED_LANGUAGES.values():
        if testcase_type.source_suffix == suffix:
            return testcase_type


def parse_config_list(config_line: str, value_type):
    """Reads in a config line in the format: 'file_name:value, file_name:value, ALL:value '
    ALL sets the default value for all other entries
    """
    config_entries = {}
    for config_entry in config_line.split(","):
        if config_entry.strip():
            testcase_name, value = config_entry.strip().split(":")
            config_entries[testcase_name.strip()] = value_type(value)
    return config_entries
