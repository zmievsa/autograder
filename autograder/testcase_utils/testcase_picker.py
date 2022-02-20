import logging
from itertools import chain
from pathlib import Path
from typing import List, Optional, Sequence, Type

from autograder.util import AutograderError, import_from_path

from .abstract_testcase import TestCase
from .stdout_testcase import StdoutOnlyTestCase

L = logging.getLogger("AUTOGRADER.testcase_utils.testcase_picker")


class TestCasePicker:
    testcase_types: List[Type[TestCase]]

    def __init__(self, testcase_types_dir: Path):
        self.testcase_types = self.discover_testcase_types(testcase_types_dir)
        if not self.testcase_types:
            raise AutograderError("No acceptable testcase types were detected.\n")

    @classmethod
    def discover_testcase_types(cls, testcase_types_dir: Path) -> List[Type[TestCase]]:
        testcase_types: List[Type[TestCase]] = []
        for testcase_type_dir in testcase_types_dir.iterdir():
            for path in testcase_type_dir.iterdir():
                if path.is_file() and path.suffix == ".py":
                    module = import_from_path(f"testcase:{path.stem}{testcase_type_dir.name}", path)
                    testcase_type: Optional[Type[TestCase]] = getattr(module, "TestCase", None)
                    if testcase_type is None:
                        continue

                    if testcase_type.is_installed():
                        testcase_types.append(testcase_type)
        return testcase_types

    def pick(
        self,
        file: Path,
        possible_source_file_stems: List[str],
        extra_ttypes: Sequence[Type[TestCase]] = (),
    ) -> Optional[Type[TestCase]]:
        L.debug(f'Picking testcase type for "{file}"')
        for testcase_type in chain(extra_ttypes, self.testcase_types):
            if testcase_type.is_a_type_of(file, possible_source_file_stems, self):
                L.debug(f'Found the appropriate testcase type: "{repr(testcase_type)}"')
                return testcase_type
        return None
