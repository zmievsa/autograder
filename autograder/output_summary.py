# Controls output to stdout and to output file


import logging
import re
import sys
from collections import deque
from contextlib import contextmanager
from pathlib import Path
from typing import Deque

import sh

from .testcase_utils.shell import get_stderr
from .testcase_utils.submission import Submission

KEY = """
\nKey:
\tFailed to Compile: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings: Your submission uses unchecked or unsafe operations
\tCrashed due to signal SIGNAL_CODE: Your submission threw an uncaught exception.
\tAll signal error codes are described here: https://man7.org/linux/man-pages/man7/signal.7.html
\tExceeded Time Limit: Your submission took too much time to run (probably an infinite loop)
"""
STUDENT_NAME_MATCHER = re.compile(r"(?P<student_name>[A-Za-z]+)_\d+_\d+_.+")


def get_submission_name(submission: Path):
    match = STUDENT_NAME_MATCHER.match(submission.stem)
    return submission.name if match is None else match["student_name"]


# Composition is used instead of inheritance for simpler API.
class SynchronizedLogger:
    LOGGER_NAME = "SynchronizedLogger"

    def __init__(self, enable_stdout):
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.logger.setLevel(logging.INFO)
        if enable_stdout:
            self.logger.addHandler(logging.StreamHandler(sys.stdout))

    def __call__(self, s: str) -> None:
        self.logger.info(s)

    @contextmanager
    def single_submission_output_logger(self, lock):
        buffer = BufferOutputLogger()
        yield buffer
        with lock:
            self("\n".join(buffer.output))


# Yes, it does break Liskov's principle and I don't care
class GradingOutputLogger(SynchronizedLogger):
    LOGGER_NAME = "Autograder"

    def __init__(
        self,
        current_dir: Path,
        path_to_output_summary: Path,
        path_to_results_dir: Path,
        assignment_name: str,
        total_points_possible: int,
        no_output: bool,
        generate_results: bool,
    ):
        super().__init__(enable_stdout=(not no_output))
        self.current_dir = current_dir
        self.results_dir = path_to_results_dir
        self.assignment_name = assignment_name
        self.total_points_possible = total_points_possible
        if not no_output:
            if path_to_output_summary.exists():
                # TODO: Input should be optional because we might ask this question in GUI.
                #   Or not? Maybe we just check it to exist separately in GUI?
                ans = input("Output summary file already exists. Would you like to overwrite it? (Yes/No) ")
                if ans.lower().startswith("y"):
                    self.logger.addHandler(logging.FileHandler(str(path_to_output_summary), mode="w"))
                else:
                    print(
                        "If you don't want to remove the summary, simply use the --no_output command line option "
                        "which will remove all stdout and file output except for --generate_results directory."
                    )
                    exit(0)
            else:
                self.logger.addHandler(logging.FileHandler(str(path_to_output_summary), mode="w"))
        if not generate_results:
            self._silence_generating_results()

    def print_precompilation_error_to_results_file(
        self,
        submission: Submission,
        error: Exception,
        buffer_logger: "BufferOutputLogger",
    ):
        if isinstance(error, sh.ErrorReturnCode):
            stderr = get_stderr(error, "Failed to precompile")
        else:
            stderr = "Failed to precompile: " + str(error)
        # Hide path to current dir
        precompilation_error = stderr.strip().replace(str(submission.dir), "...")
        buffer_logger(stderr + f"\nResult: 0/{self.total_points_possible}\n")
        self._print_single_student_output_to_results_file(
            submission,
            f"0/{self.total_points_possible}",
            precompilation_error=precompilation_error,
        )

    def print_testcase_results_to_results_file(
        self,
        submission: Submission,
        normalized_student_score: float,
        buffer_logger: "BufferOutputLogger",
    ):
        student_final_result = f"{round(normalized_student_score)}/{self.total_points_possible}"
        buffer_logger(f"Result: {student_final_result}\n")
        self._print_single_student_output_to_results_file(submission, student_final_result)

    # FIXME: This needs better naming...
    def _print_single_student_output_to_results_file(
        self,
        submission: Submission,
        formatted_student_score: str,
        precompilation_error: str = "",
    ):
        with open(self.results_dir / submission.path.name, "w") as f:
            f.write(
                format_output_for_student_file(
                    submission,
                    self.assignment_name,
                    formatted_student_score,
                    precompilation_error,
                )
            )

    def _silence_generating_results(self):
        self.print_precompilation_error_to_results_file = lambda *a, **kw: None  # type: ignore
        self.print_testcase_results_to_results_file = lambda *a, **kw: None  # type: ignore

    def print_key(self):
        self(KEY)


# We use this to efficiently synchronize logger output
# to make it thread-safe.
class BufferOutputLogger:
    output: Deque[str]

    def __init__(self):
        self.output = deque()

    def __call__(self, s: str) -> None:
        self.output.append(s)


def format_output_for_student_file(
    submission: Submission,
    assignment_name: str,
    formatted_student_score: str,
    precompilation_error: str = "",
):
    """Replace this function with anything else if you want the output
    to have a different style
    """
    str_builder = deque()
    b = str_builder.append
    b(f"{assignment_name} Test Results\n\n")
    if not precompilation_error:
        b("%-40s%s\n" % ("TestCase", "Result"))
    b("================================================================")
    if precompilation_error:
        b("\n")
        b(precompilation_error)
    else:
        for test_name, (test_grade, test_message) in submission.grades.items():
            b("\n%-40s%s" % (test_name, test_message))
    b("\n================================================================\n")
    b("Result: " + formatted_student_score)
    b(KEY)
    return "".join(str_builder)
