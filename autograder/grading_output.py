from .util import get_stderr
from contextlib import contextmanager
import logging
import sys
from pathlib import Path
import re
from collections import deque
from typing import Deque


KEY = """
\nKey:
\tFailed to Compile: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings: Your submission uses unchecked or unsafe operations
\tCrashed due to signal SIGNAL_CODE: Your submission threw an uncaught exception.
\tAll signal error codes are described here: http://man7.org/linux/man-pages/man7/signal.7.html
\tExceeded Time Limit: Your submission took too much time to run (probably an infinite loop)
"""
STUDENT_NAME_MATCHER = re.compile(r"(?P<student_name>[A-Za-z]+)_\d+_\d+_\w+")


def get_submission_name(submission: Path):
    match = STUDENT_NAME_MATCHER.match(submission.stem)
    return submission.name if match is None else match["student_name"]


# Composition is used instead of inheritance for simpler API
class GradingOutputLogger:
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
        self.current_dir = current_dir
        self.results_dir = path_to_results_dir
        self.assignment_name = assignment_name
        self.total_points_possible = total_points_possible
        self.logger = logging.getLogger("Grader")
        self.logger.setLevel(logging.INFO)
        if not no_output:
            self.logger.addHandler(logging.StreamHandler(sys.stdout))
            file_handler = logging.FileHandler(path_to_output_summary, mode="w")
            if path_to_output_summary.exists():
                # TODO: Input should be optional because we might ask this question in GUI.
                #   Or not? Maybe we just check it to exist separately in GUI?
                ans = input("Output summary file already exists. Would you like to overwrite it? (Yes/No) ")
                if ans.lower().startswith("y"):
                    self.logger.addHandler(file_handler)
                else:
                    print(
                        "If you don't want to remove the summary, simply use the --no_output command line option "
                        "which will remove all stdout and file output except for --generate_results directory."
                    )
                    exit(0)
            else:
                self.logger.addHandler(file_handler)
        if not generate_results:
            self._silence_generating_results()

    def __call__(self, s: str) -> None:
        self.logger.info(s)

    @contextmanager
    def single_submission_output_logger(self):
        try:
            buffer = BufferOutputLogger()
            yield buffer
            self("\n".join(buffer.output))
        except Exception as e:
            raise e

    def print_precompilation_error_to_results_file(self, submission, error, buffer_logger):
        stderr = get_stderr(self.current_dir, error, "Failed to precompile")
        buffer_logger(stderr + f"\nResult: 0/{self.total_points_possible}\n")
        precompilation_error = stderr.replace("Failed to precompile", "")
        self._print_single_student_output_to_results_file(
            submission,
            assignment_name=self.assignment_name,
            precompilation_error=precompilation_error,
        )

    def print_testcase_results_to_results_file(
        self,
        submission,
        testcase_results,
        normalized_student_score,
        buffer_logger,
    ):
        student_final_result = f"{round(normalized_student_score)}/{self.total_points_possible}"
        buffer_logger(f"Result: {student_final_result}\n")
        self._print_single_student_output_to_results_file(
            submission,
            assignment_name=self.assignment_name,
            testcase_results=testcase_results,
            formatted_student_score=student_final_result,
        )

    def _print_single_student_output_to_results_file(self, submission, **kwargs):
        with open(self.results_dir / submission.name, "w") as f:
            f.write(format_output_for_student_file(**kwargs))

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


def format_output_for_student_file(**output_info):
    """Replace this function with anything else if you want the output
    to have a different style
    """
    str_builder = deque()
    str_builder.append(f"{output_info['assignment_name']} Test Results\n\n")
    str_builder.append("%-40s%s" % ("TestCase", "Result"))
    str_builder.append("\n================================================================")
    if "precompilation_error" in output_info:
        str_builder.append(output_info["precompilation_error"])
        return "".join(str_builder)
    for test_output in output_info["testcase_results"]:
        str_builder.append("\n%-40s%s" % test_output)
    str_builder.append("\n================================================================\n")
    str_builder.append("Result: " + output_info["formatted_student_score"])
    str_builder.append(KEY)
    return "".join(str_builder)