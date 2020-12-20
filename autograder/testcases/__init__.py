from .abstract_base_class import TestCase, ArgList
from .c import CTestCase
from .java import JavaTestCase
from .python import PythonTestCase
from .cpp import CPPTestCase

ALLOWED_LANGUAGES = {
    "c": CTestCase,
    "java": JavaTestCase,
    "python": PythonTestCase,
    "c++": CPPTestCase,
}