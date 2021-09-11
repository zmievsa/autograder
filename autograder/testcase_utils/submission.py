from pathlib import Path
from typing import List, Optional, Type, Dict, Tuple

from .abstract_testcase import TestCase


def find_appropriate_source_file_stem(file: Path, possible_source_file_stems: List[str]) -> Optional[str]:
    for s in possible_source_file_stems:
        if s in file.stem:
            return s


class Submission:
    # I wanted to use a dataclass but they do not work well with slots until 3.10
    __slots__ = "path", "type", "dir", "grades"

    file: Path
    type: Type[TestCase]
    dir: Path

    grades: Dict[str, Tuple[float, str]]

    def __init__(self, file: Path, testcase_type: Type[TestCase], temp_dir: Path):
        self.path = file
        self.type = testcase_type
        self.dir = temp_dir / file.name
        self.dir.mkdir()
        self.grades = {}

    def add_grade(self, test_name: str, testcase_score: float, message: str):
        self.grades[test_name] = (testcase_score, message)
