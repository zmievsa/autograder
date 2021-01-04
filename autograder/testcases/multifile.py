from pathlib import Path
from .abstract_base_class import Command, TestCase


def is_multifile_submission(submission_dir: Path):
    contents = list(submission_dir.iterdir())
    while len(contents) == 1 and contents[0].is_dir():
        contents = list(contents[0].iterdir())
    return any(_is_makefile(f) for f in contents)


POSSIBLE_MAKEFILE_NAMES = "GNUmakefile", "makefile", "Makefile"


def _is_makefile(path: Path):
    return not path.is_dir() and path.name in POSSIBLE_MAKEFILE_NAMES


class MultifileTestCase(TestCase):
    helper_module_name = ""
    compiler = Command("make")

    @classmethod
    def is_installed(cls) -> bool:
        """We assume all utilities necessary are installed because we can't possibly check for all of them."""
        return cls.compiler is not None

    def prepend_test_helper(self):
        """ We don't need TestHelper when we are only checking inputs/outputs """

    @classmethod
    def precompile_submission(cls, submission, student_dir, source_file_name, arglist):
        """ pwd = temp/student_dir """
        pass

    def compile_testcase(self, precompiled_submission):
        pass

    @classmethod
    def run_additional_testcase_operations_in_student_dir(cls, student_dir: Path):
        pass

    def make_executable_path(self, submission: Path) -> Path:
        """ By combining test name and student name, it makes a unique path """
        return submission.with_name(self.path.stem + submission.stem + self.executable_suffix)

    def prepend_test_helper(self):
        """We don't need test helper because we don't have a testcase file"""
        pass

    def delete_executable_files(self, precompiled_submission: Path):
        """ We don't compile each testcase separately so we don't need to clean up executable files """
        pass

    def delete_source_file(self, source_path: Path):
        """ There is no testcase file """
        pass
