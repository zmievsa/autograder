from pathlib import Path
from typing import Dict, Iterable, Optional, Type

from .abstract_base_class import ArgList, TestCase
from .c import CTestCase
from .cpp import CPPTestCase
from .java import JavaTestCase
from .python import PythonTestCase


def _is_installed(language_name: str, testcase: Type[TestCase]) -> bool:
    """ Useful for logging """
    if testcase.is_installed():
        return True
    else:
        print(f"Utilities for running {language_name} are not installed. Disabling it.")
        return False


class Submission:
    __slots__ = "path", "type", "dir"

    def __init__(self, file: Path, testcase_type: Type[TestCase], temp_dir: Path):
        self.path = file
        self.type = testcase_type
        self.dir = temp_dir / file.name
        self.dir.mkdir()


ALLOWED_LANGUAGES: Dict[str, Type[TestCase]] = {
    "c": CTestCase,
    "java": JavaTestCase,
    "python": PythonTestCase,
    "c++": CPPTestCase,
}

ALLOWED_LANGUAGES = {k: v for k, v in ALLOWED_LANGUAGES.items() if _is_installed(k, v)}


def get_testcase_type(
    file: Path, allowed_types: Iterable[Type[TestCase]] = ALLOWED_LANGUAGES.values()
) -> Optional[Type[TestCase]]:
    for testcase_type in allowed_types:
        if testcase_type.is_a_type_of(file):
            return testcase_type