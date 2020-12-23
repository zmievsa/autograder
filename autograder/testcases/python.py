import py_compile
from pathlib import Path
import shutil

import sh

from .abstract_base_class import ArgList, TestCase

import sys

PYTHON_VERSION_MAJOR_RELEASE, PYTHON_VERSION_MINOR_RELEASE, *_ = sys.version_info
PYTHON_VERSION = f"{PYTHON_VERSION_MAJOR_RELEASE}.{PYTHON_VERSION_MINOR_RELEASE}"
PYTHON_EXECUTABLE_NAME = f"python{PYTHON_VERSION}"

if shutil.which(PYTHON_EXECUTABLE_NAME) is None:
    PYTHON_EXECUTABLE_NAME = "python3"


class PythonTestCase(TestCase):
    """A proof of concept of how easy it is to add new languages.
    Will only work if python is accessible via python3 alias for now.
    """

    source_suffix = ".py"
    executable_suffix = ".pyc"
    helper_module_name = "test_helper.py"
    interpreter = sh.Command(PYTHON_EXECUTABLE_NAME)

    @classmethod
    def precompile_submission(cls, submission: Path, student_dir: Path, source_file_name, arglist) -> Path:
        copied_submission = super().precompile_submission(submission, student_dir, source_file_name, arglist)
        kwargs = {}
        if "-O" in arglist:
            kwargs["optimize"] = 1
        executable_path = copied_submission.with_suffix(cls.executable_suffix)
        py_compile.compile(file=str(copied_submission), cfile=str(executable_path), doraise=True)
        copied_submission.unlink()
        return executable_path

    def compile_testcase(self, precompiled_submission: Path):
        # Argument lists do not seem to work here
        # Test it, plz.
        return lambda *args, **kwargs: self.interpreter(
            self.make_executable_path(precompiled_submission),
            precompiled_submission.stem,
            *self.argument_lists[ArgList.TESTCASE_COMPILATION],
            *args,
            **kwargs,
        )

    def precompile_testcase(self):
        kwargs = {}
        if "-O" in self.argument_lists[ArgList.TESTCASE_PRECOMPILATION]:
            kwargs["optimize"] = 1
        executable_path = self.path.with_suffix(self.executable_suffix)
        py_compile.compile(file=str(self.path), cfile=str(executable_path), doraise=True, **kwargs)
        self.path.unlink()
        self.path = executable_path

    def delete_source_file(self, source_path: Path):
        """ Source file is the same as executable file so we don't need to delete it """

    def make_executable_path(self, submission: Path) -> Path:
        return submission.with_name(self.path.name)