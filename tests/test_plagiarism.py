import json
from typing import Set, Tuple

from autograder.__main__ import main as autograder

from pytest import approx
from . import tools


def convert_to_comparable(result: dict) -> Tuple[Set[str], float]:
    return set([result["student1"], result["student2"]]), result["similarity_score"]


EXPECTED_PLAGIARISM_DATA = {
    "results": [
        {
            "student1": "student_with_wrong_assignment_name.c",
            "student2": "failing_student_homework.c",
            "similarity_score": approx(0.9736166048199649, 0.0001),
        },
        {
            "student1": "average_student_homework.c",
            "student2": "student_with_wrong_assignment_name.c",
            "similarity_score": approx(0.054649696848494515, 0.0001),
        },
        {
            "student1": "average_student_homework.c",
            "student2": "failing_student_homework.c",
            "similarity_score": approx(0.054453459283773556, 0.0001),
        },
        {
            "student1": "student_with_wrong_assignment_name.c",
            "student2": "perfect_student_homework.c",
            "similarity_score": approx(0.025879645605391466, 0.0001),
        },
        {
            "student1": "perfect_student_homework.c",
            "student2": "failing_student_homework.c",
            "similarity_score": approx(0.025804728949402153, 0.0001),
        },
        {
            "student1": "average_student_homework.c",
            "student2": "perfect_student_homework.c",
            "similarity_score": approx(0.024774982794116333, 0.0001),
        },
    ]
}


COMPARABLE_EXPECTED_PLAGIARISM_DATA = [convert_to_comparable(r) for r in EXPECTED_PLAGIARISM_DATA["results"]]


def test_fibonacci_example():
    with tools.silence_output() as buf:
        autograder(["plagiarism", "examples/fibonacci_c"])
        raw_real_result = json.loads(buf.getvalue())

    real_results = [convert_to_comparable(r) for r in raw_real_result["results"]]

    assert COMPARABLE_EXPECTED_PLAGIARISM_DATA == real_results
