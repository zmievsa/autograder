import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Type

from .abstract_testcase import TestCase


def find_appropriate_source_file_stem(file: Path, possible_source_file_stems: List[str]) -> Optional[str]:
    for s in possible_source_file_stems:
        if s.lower() in file.stem.lower():
            return s
    return None


STUDENT_NAME_MATCHER = re.compile(r"(?P<student_name>[A-Za-z]+)_\d+_\d+_.+")


def get_submission_name(submission: Path):
    match = STUDENT_NAME_MATCHER.match(submission.stem)
    return submission.name if match is None else match["student_name"]


@dataclass
class TestCaseGrade:
    testcase_score: float
    testcase_weight: float
    message: str
    extra_output_fields: Dict[str, str]


class Submission:
    # Sowwy, dataclasses do not support slots until 3.10
    __slots__ = (
        "old_path",
        "temp_path",
        "_temp_dir",
        "temp_dir",
        "name",
        "type",
        "grades",
        "precompilation_error",
        "final_grade",
    )

    old_path: Path
    temp_path: Path
    _temp_dir: TemporaryDirectory
    temp_dir: Path  # Personal temporary dir, not the root one
    name: str
    type: Type[TestCase]
    grades: Dict[str, TestCaseGrade]
    precompilation_error: str
    final_grade: int

    def __init__(self, file: Path, testcase_type: Type[TestCase]):
        self.old_path = file
        self._temp_dir = TemporaryDirectory(prefix="ag_hw_")
        self.temp_dir = Path(self._temp_dir.name)
        self.temp_path = self.temp_dir / file.name
        self.name = get_submission_name(file)
        self.type = testcase_type
        self.grades = {}
        self.precompilation_error = ""
        self.final_grade = -1

    def add_grade(
        self,
        test_name: str,
        testcase_score: float,
        testcase_weight: float,
        message: str,
        extra_output_fields: Dict[str, str],
    ):
        self.grades[test_name] = TestCaseGrade(testcase_score, testcase_weight, message, extra_output_fields)

    def register_precompilation_error(self, error: str) -> None:
        self.precompilation_error = error
        self.final_grade = 0

    def register_final_grade(self, total_score_to_100_ratio: float):
        self.final_grade = self._calculate_final_grade(total_score_to_100_ratio)

    def _calculate_final_grade(self, total_score_to_100_ratio: float) -> int:
        total_score = 0.0
        total_testcase_weight = 0.0
        for grade in self.grades.values():
            total_score += grade.testcase_score
            total_testcase_weight += grade.testcase_weight
        normalized_score = total_score / total_testcase_weight * total_score_to_100_ratio
        return round(normalized_score)
