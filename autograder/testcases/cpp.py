from .c import CTestCase
import sh


class CPPTestCase(CTestCase):
    source_suffix = ".cpp"
    compiler = sh.Command("g++")
