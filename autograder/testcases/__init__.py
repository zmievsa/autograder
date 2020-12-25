from typing import Dict, Type

from .abstract_base_class import ArgList, TestCase
from .c import CTestCase
from .cpp import CPPTestCase
from .java import JavaTestCase
from .python import PythonTestCase


def _is_installed(language_name: str, testcase: TestCase) -> bool:
    """ Useful for logging """
    if testcase.is_installed():
        return True
    else:
        print(f"Utilities for running {language_name} are not installed. Disabling it.")
        return False


ALLOWED_LANGUAGES: Dict[str, Type[TestCase]] = {
    "c": CTestCase,
    "java": JavaTestCase,
    "python": PythonTestCase,
    "c++": CPPTestCase,
}

ALLOWED_LANGUAGES = {k: v for k, v in ALLOWED_LANGUAGES.items() if _is_installed(k, v)}
