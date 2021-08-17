# TODO: Add a point in docs that ALLOWED_LANGUAGES does not affect stdout_only grading

from pathlib import Path
from typing import List, Type, Optional

from autograder.util import AutograderError, import_from_path
from .abstract_testcase import TestCase
from .stdout_testcase import StdoutOnlyTestCase
from .submission import SubmissionFormatChecker


class TestCasePicker:
    testcase_types: List[Type[TestCase]]

    def __init__(
        self,
        testcase_types_dir: Path,
        submission_is_allowed: SubmissionFormatChecker,
        allowed_languages: List[str] = None,
        stdout_only_grading_enabled: bool = False,
    ):
        self.submission_is_allowed = submission_is_allowed
        registered_ttypes = self.discover_testcase_types(testcase_types_dir)
        if allowed_languages is not None:
            self.testcase_types = [t for t in registered_ttypes if t.name() in allowed_languages]
        else:
            self.testcase_types = registered_ttypes
        if stdout_only_grading_enabled:
            self.testcase_types.append(StdoutOnlyTestCase)
        if not self.testcase_types:
            raise AutograderError(
                "No acceptable testcase types were detected.\n"
                f"Allowed languages: {allowed_languages}\n"
                f"Registered testcase types: {registered_ttypes}"
            )

    @classmethod
    def discover_testcase_types(cls, testcase_types_dir: Path) -> List[Type[TestCase]]:
        testcase_types = []
        for testcase_type in testcase_types_dir.iterdir():
            for path in testcase_type.iterdir():
                if path.is_file() and path.suffix == ".py":
                    testcase = import_from_path(f"testcase:{path.stem}{testcase_type.name}", path).TestCase
                    if cls._is_installed(testcase_type.name, testcase):
                        testcase_types.append(testcase)
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
            if testcase_type.is_a_type_of(file, self.submission_is_allowed):
                return testcase_type
