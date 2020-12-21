import sh

from .c import CTestCase


class CPPTestCase(CTestCase):
    source_suffix = ".cpp"
    compiler = sh.Command("g++")
