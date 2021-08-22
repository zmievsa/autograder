from pathlib import Path
from typing import List, Type, Optional

from autograder.util import AutograderError, import_from_path
from .abstract_testcase import TestCase
from .stdout_testcase import StdoutOnlyTestCase


class TestCasePicker:
    testcase_types: List[Type[TestCase]]

    def __init__(
        self,
        testcase_types_dir: Path,
        possible_source_file_stems: List[str],
        stdout_only_grading_enabled: bool = False,
    ):
        self.possible_source_file_stems = possible_source_file_stems
        self.testcase_types = self.discover_testcase_types(testcase_types_dir)
        if stdout_only_grading_enabled:
            self.testcase_types.insert(0, StdoutOnlyTestCase)
        if not self.testcase_types:
            raise AutograderError("No acceptable testcase types were detected.\n")

    @classmethod
    def discover_testcase_types(cls, testcase_types_dir: Path) -> List[Type[TestCase]]:
        testcase_types = []
        for testcase_type_dir in testcase_types_dir.iterdir():
            for path in testcase_type_dir.iterdir():
                if path.is_file() and path.suffix == ".py":
                    module = import_from_path(f"testcase:{path.stem}{testcase_type_dir.name}", path)
                    testcase_type = getattr(module, "TestCase", None)
                    if testcase_type is None:
                        print(f"Testcase type '{path}' does not define a 'TestCase' class, skipping.")
                        continue

                    if cls._is_installed(testcase_type_dir.name, testcase_type):
                        testcase_types.append(testcase_type)
        return testcase_types

    @staticmethod
    def _is_installed(language_name: str, testcase: Type[TestCase]) -> bool:
        """Useful for logging"""
        if testcase.is_installed():
            return True
        else:
            print(f"Utilities for running {language_name} are not installed. Disabling it.")
            return False

    def pick(self, file: Path) -> Optional[Type[TestCase]]:
        for testcase_type in self.testcase_types:
            if testcase_type.is_a_type_of(file, self.possible_source_file_stems):
                return testcase_type
