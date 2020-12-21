from .abstract_base_class import ArgList, TestCase
from .c import CTestCase
from .cpp import CPPTestCase
from .java import JavaTestCase
from .python import PythonTestCase

ALLOWED_LANGUAGES = {
    "c": CTestCase,
    "java": JavaTestCase,
    "python": PythonTestCase,
    "c++": CPPTestCase,
}