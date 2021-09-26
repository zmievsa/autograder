from pathlib import Path
from typing import List, Optional, Type, Dict, Tuple
import re

from .abstract_testcase import TestCase


def find_appropriate_source_file_stem(file: Path, possible_source_file_stems: List[str]) -> Optional[str]:
    for s in possible_source_file_stems:
        if s in file.stem:
            return s


STUDENT_NAME_MATCHER = re.compile(r"(?P<student_name>[A-Za-z]+)_\d+_\d+_.+")


def get_submission_name(submission: Path):
    match = STUDENT_NAME_MATCHER.match(submission.stem)
    return submission.name if match is None else match["student_name"]


class Submission:
    # Sowwy, dataclasses do not support slots until 3.10
    __slots__ = "path", "name", "type", "dir", "grades", "precompilation_error", "final_grade"

    path: Path
    name: str
    type: Type[TestCase]
    dir: Path
    grades: Dict[str, Tuple[float, float, str]]
    precompilation_error: str
    final_grade: int

    def __init__(self, file: Path, testcase_type: Type[TestCase], temp_dir: Path):
        self.path = file
        self.name = get_submission_name(file)
        self.type = testcase_type
        self.dir = temp_dir / file.name
        self.dir.mkdir()
        self.grades = {}
        self.precompilation_error = ""
        self.final_grade = -1

    def add_grade(self, test_name: str, testcase_score: float, testcase_weight: float, message: str):
        self.grades[test_name] = (testcase_score, testcase_weight, message)

    def register_precompilation_error(self, error: str) -> None:
        self.precompilation_error = error
        self.final_grade = 0

    def register_final_grade(self, total_score_to_100_ratio: float):
        self.final_grade = self._calculate_final_grade(total_score_to_100_ratio)

    def _calculate_final_grade(self, total_score_to_100_ratio: float) -> int:
        total_score = 0
        grades = self.grades.items()
        total_testcase_weight = 0
        for test_name, (test_grade, test_weight, test_message) in grades:
            total_score += test_grade
            total_testcase_weight += test_weight
        normalized_score = total_score / total_testcase_weight * total_score_to_100_ratio
        return round(normalized_score)
