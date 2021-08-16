from pathlib import Path
from typing import List, Optional, Type, Callable

from .abstract_testcase import TestCase

# SubmissionFormatChecker = Callable[[Path], Optional[str]]

class SubmissionFormatChecker:
    """ This could be done using a decorator instead but then it wouldn't pickle, and we need pickling """
    def __init__(self, possible_file_stems: List[str], name_is_case_insensitive: bool):
        self.possible_file_stems = possible_file_stems
        self.name_is_case_insensitive = name_is_case_insensitive

    def __call__(self, f: Path) -> Optional[str]:
        return find_appropriate_source_file_stem(f, self.possible_file_stems, self.name_is_case_insensitive)


def find_appropriate_source_file_stem(
    file: Path, possible_source_file_stems: List[str], source_is_case_insensitive: bool
) -> Optional[str]:
    file_stem = file.stem
    if source_is_case_insensitive:
        file_stem = file_stem.lower()
    for s in possible_source_file_stems:
        if source_is_case_insensitive:
            if s.lower() in file_stem:
                return s
        else:
            # FIXME: Wait... Is this a bug?
            if s in file_stem:
                return s


class Submission:
    # I wanted to use a dataclass but they do not work well with slots until 3.10
    __slots__ = "path", "type", "dir"

    file: Path
    type: Type[TestCase]
    dir: Path

    def __init__(self, file: Path, testcase_type: Type[TestCase], temp_dir: Path):
        self.path = file
        self.type = testcase_type
        self.dir = temp_dir / file.name
        self.dir.mkdir()
