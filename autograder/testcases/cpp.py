import shutil
import sh

from .c import CTestCase

if shutil.which("g++") is not None:
    COMPILER = sh.Command("g++")
else:
    COMPILER = None


class CPPTestCase(CTestCase):
    source_suffix = ".cpp"
    compiler = COMPILER
