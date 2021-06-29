from autograder.testcase_utils.shell import Command

from autograder.testcase_types.gcc.c import TestCase as CTestCase


class TestCase(CTestCase):
    source_suffix = ".cpp"
    compiler = Command("g++")
