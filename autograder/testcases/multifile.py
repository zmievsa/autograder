from collections import namedtuple
from autograder.testcases.util.exit_codes import ExitCodeEventType
from pathlib import Path
import shutil
from typing import List

import sh
from .abstract_base_class import Command, TestCase, submission_is_allowed

POSSIBLE_MAKEFILE_NAMES = "GNUmakefile", "makefile", "Makefile"
DUMMY_SH_COMMAND_RESULT_CLASS = namedtuple("ShCommandResult", "exit_code")


def is_multifile_submission(submission_dir: Path, possible_source_file_stems, source_is_case_insensitive):
    contents = list(submission_dir.iterdir())
    while len(contents) == 1 and contents[0].is_dir():
        contents = list(contents[0].iterdir())

    for f in submission_dir.iterdir():
        if _is_makefile(f) or submission_is_allowed(f, possible_source_file_stems, source_is_case_insensitive):
            return True
    else:
        return False


def _is_makefile(path: Path):
    return not path.is_dir() and path.name in POSSIBLE_MAKEFILE_NAMES


class MultifileTestCase(TestCase):
    helper_module_name = ""
    compiler = Command("make")

    @classmethod
    def is_installed(cls) -> bool:
        """We assume all utilities necessary are installed because we can't possibly check for all of them."""
        return cls.compiler is not None

    @classmethod
    def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: str,
        source_is_case_insensitive: bool,
        arglist,
    ):
        """ pwd = temp/student_dir """
        _copy_submission_contents_into_student_dir(submission, student_dir)
        try:
            cls.compiler()
        except sh.ErrorReturnCode as e:
            if "no makefile found" in str(e):
                pass
            else:
                raise e
        return _find_submission_executable(student_dir, possible_source_file_stems, source_is_case_insensitive)

    def compile_testcase(self, precompiled_submission: Path):
        return lambda *a, **kw: _run_multifile_testcase(precompiled_submission, *a, **kw)

    def prepend_test_helper(self):
        """ We don't need TestHelper when we are only checking inputs/outputs """

    def prepend_test_helper(self):
        """We don't need test helper because we don't have a testcase file"""
        pass

    def delete_executable_files(self, precompiled_submission: Path):
        """ We don't compile each testcase separately so we don't need to clean up executable files """
        pass

    def delete_source_file(self, source_path: Path):
        """ There is no testcase file """
        pass


def _run_multifile_testcase(precompiled_submission: Path, *args, **kwargs):
    sh.Command(precompiled_submission)(*args, **kwargs)
    return DUMMY_SH_COMMAND_RESULT_CLASS(ExitCodeEventType.CHECK_STDOUT)


def _copy_submission_contents_into_student_dir(submission, student_dir):
    contents: List[Path] = list(submission.iterdir())
    while len(contents) == 1 and contents[0].is_dir():
        contents = list(contents[0].iterdir())
    for f in contents:
        new_path = student_dir / f.name
        if f.is_dir():
            shutil.copytree(f, new_path)
        else:
            shutil.copyfile(f, new_path)


def _find_submission_executable(student_dir: Path, possible_source_file_stems, source_is_case_insensitive):
    for f in student_dir.iterdir():
        if submission_is_allowed(f, possible_source_file_stems, source_is_case_insensitive):
            return f
