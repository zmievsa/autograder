import stat
from collections import namedtuple
from autograder.testcase_utils.exit_codes import ExitCodeEventType
from pathlib import Path
import shutil
from typing import List, Callable

import sh
from .abstract_testcase import TestCase
from .shell import Command
from .submission import SubmissionFormatChecker

POSSIBLE_MAKEFILE_NAMES = "GNUmakefile", "makefile", "Makefile"
DUMMY_SH_COMMAND_RESULT_CLASS = namedtuple("ShCommandResult", "exit_code")


def is_multifile_submission(submission_dir: Path, submission_is_allowed: Callable) -> bool:
    contents = list(submission_dir.iterdir())
    # Seek the innermost non-single-file directory
    # in case the directory contains another directory with the project (common issue when zipping directories)
    while len(contents) == 1 and contents[0].is_dir():
        contents = list(contents[0].iterdir())

    for f in submission_dir.iterdir():
        if _is_makefile(f) or submission_is_allowed(f):
            return True
    return False


def _is_makefile(path: Path):
    return not path.is_dir() and path.name in POSSIBLE_MAKEFILE_NAMES


def contains_shebang(path: Path) -> bool:
    if not path.is_file():
        return False
    with open(path) as f:
        return f.readline().startswith("#!")


class StdoutOnlyTestCase(TestCase):

    helper_module = ""
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
        possible_source_file_stems: List[str],
        submission_is_allowed: SubmissionFormatChecker,
        arglist,
    ):
        """pwd is temp/student_dir"""

        # Single-file with shebang
        if submission.is_file():
            destination = student_dir / submission.name
            shutil.copy(str(submission), str(destination))
            _make_executable(destination)
            return destination
        # A directory with a makefile
        else:
            _copy_multifile_submission_contents_into_student_dir(submission, student_dir)
            try:
                cls.compiler(*arglist)
            except sh.ErrorReturnCode as e:
                if "no makefile found" not in str(e):
                    raise e
            return _find_submission_executable(student_dir, submission_is_allowed)

    def compile_testcase(self, precompiled_submission: Path):
        return lambda *a, **kw: _run_multifile_testcase(precompiled_submission, *a, **kw)

    def prepend_test_helper(self):
        """We don't need TestHelper when we are only checking inputs/outputs"""

    def delete_executable_files(self, precompiled_submission: Path):
        """We don't compile each testcase separately so we don't need to clean up executable files"""

    def delete_source_file(self, source_path: Path):
        """There is no testcase file"""


def _run_multifile_testcase(precompiled_submission: Path, *args, **kwargs):

    sh.Command(precompiled_submission)(*args, **kwargs)
    return DUMMY_SH_COMMAND_RESULT_CLASS(ExitCodeEventType.CHECK_STDOUT)


def _copy_multifile_submission_contents_into_student_dir(submission: Path, student_dir: Path):
    contents: List[Path] = list(submission.iterdir())
    while len(contents) == 1 and contents[0].is_dir():
        contents = list(contents[0].iterdir())
    for f in contents:
        new_path = student_dir / f.name
        if f.is_dir():
            op = shutil.copytree
        else:
            op = shutil.copyfile
        op(str(f), new_path)


def _find_submission_executable(student_dir: Path, submission_is_allowed: SubmissionFormatChecker):
    for f in student_dir.iterdir():
        if submission_is_allowed(f):
            return f


def _make_executable(f: Path) -> None:
    f.chmod(f.stat().st_mode | stat.S_IEXEC)
