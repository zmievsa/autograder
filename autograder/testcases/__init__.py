# TODO: Make TestcasePicker class to allow for extensible extention picking and running
# TODO: Make STDOUT-ONLY class that applies to all submissions

from pathlib import Path
from typing import Dict, Iterable, Optional, Type

from .abstract_base_class import ArgList, TestCase
from .c import CTestCase
from .cpp import CPPTestCase
from .java import JavaTestCase
from .python import PythonTestCase


