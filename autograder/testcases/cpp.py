from autograder.testcases.abstract_base_class import Command
import shutil
import sh

from .c import CTestCase


class CPPTestCase(CTestCase):
    source_suffix = ".cpp"
    compiler = Command("g++")
