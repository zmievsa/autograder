# Controls output to stdout and to output file


import json
from collections import deque
from pathlib import Path
from typing import Any, Deque, Sequence

from .testcase_utils.submission import Submission, TestCaseGrade

KEY = """
\nKey:
\tFailed to Compile: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings: Your submission uses unchecked or unsafe operations
\tCrashed due to signal SIGNAL_CODE: Your submission threw an uncaught exception.
\tAll signal error codes are described here: https://man7.org/linux/man-pages/man7/signal.7.html
\tExceeded Time Limit: Your submission took too much time to run (probably an infinite loop)
"""


def _empty_func(*a: Any, **kw: Any):
    """Python can't pickle lambdas so we use this
    Edit: Now pickling is not necessary but who cares anymore?
    """
    pass


# TODO: Replace path_to_results_dir and generate_results with path_to_results_dir: Optional[Path]
class GradingOutputLogger:
    LOGGER_NAME = "Autograder"

    def __init__(
        self,
        path_to_results_dir: Path,
        assignment_name: str,
        total_points_possible: int,
        generate_results: bool,
    ):
        self.results_dir = path_to_results_dir
        self.assignment_name = assignment_name
        self.total_points_possible = total_points_possible

        if not generate_results:
            self._silence_generating_results()

    def print_single_student_grading_results(self, submission: Submission):
        student_final_result = f"{submission.final_grade}/{self.total_points_possible}"
        self._print_single_student_grading_results_to_stdout(submission, student_final_result)
        self._print_single_student_grading_results_to_file(submission, student_final_result)

    def print_final_score(self, submissions: Sequence[Submission], score: int):
        print(f"\nAverage score: {score}/{self.total_points_possible}")

    def print_key(self):
        print(KEY)

    def _print_single_student_grading_results_to_stdout(self, submission: Submission, formatted_student_score: str):
        print(f"Grading {submission.name}")
        if submission.precompilation_error:
            print(f"{submission.precompilation_error}")
        else:
            for test_name, grade in submission.grades.items():
                additional_output = self._generate_additional_output(grade)
                print(f"{test_name}: {grade.message}{additional_output}")
        print(f"\nResult: {formatted_student_score}\n\n")

    def _print_single_student_grading_results_to_file(self, submission: Submission, formatted_student_score: str):
        output_for_student_file = self._format_output_for_student_file(submission, formatted_student_score)
        (self.results_dir / submission.old_path.name).write_text(output_for_student_file)

    @staticmethod
    def _generate_additional_output(grade: TestCaseGrade) -> str:
        splitter = f'{35 * "="}\n'
        output = "\n".join([f"{k}:\n{splitter}{v}{splitter}" for k, v in grade.extra_output_fields.items()])
        if output:
            output = "\n" + output
        return output

    def _silence_generating_results(self):
        self._print_single_student_grading_results_to_stdout = _empty_func  # type: ignore

    def _format_output_for_student_file(self, submission: Submission, formatted_student_score: str):
        """Replace this function with anything else if you want the output to have a different style"""
        str_builder: Deque[str] = deque()
        b = str_builder.append
        b(f"{self.assignment_name} Test Results\n\n")
        if not submission.precompilation_error:
            b("%-40s%s\n" % ("TestCase", "Result"))
        b("================================================================")
        if submission.precompilation_error:
            b("\n")
            b(submission.precompilation_error)
        else:
            for test_name, grade in submission.grades.items():
                b("\n%-40s%s" % (test_name, grade.message))
                b(self._generate_additional_output(grade))
        b("\n================================================================\n")
        b("Result: " + formatted_student_score)
        b(KEY)
        return "".join(str_builder)


class JsonGradingOutputLogger(GradingOutputLogger):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._print_single_student_grading_results_to_stdout = _empty_func

    def print_key(self):
        pass

    def print_final_score(self, submissions: Sequence[Submission], score: int):

        submission_results = [
            {
                "submission": s.old_path.name,
                "final_grade": s.final_grade,
                "testcase_scores": [
                    {
                        "name": test_name,
                        "message": grade.message,
                        **grade.extra_output_fields,
                    }
                    for test_name, grade in s.grades.items()
                ],
                "precompilation_error": s.precompilation_error,
            }
            for s in submissions
        ]
        submission_results.sort(key=lambda v: v["final_grade"], reverse=True)
        output = {
            "average_score": score,
            "total_points_possible": self.total_points_possible,
            "submissions": submission_results,
        }
        print(json.dumps(output, indent=4))
