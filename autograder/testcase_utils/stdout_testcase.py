import shutil
import stat
import traceback
from collections import namedtuple
from pathlib import Path
from typing import List

import sh

from autograder.testcase_utils.exit_codes import ExitCodeEventType
from .abstract_testcase import TestCase
from .shell import Command
from .submission import find_appropriate_source_file_stem
from .testcase_result_validator import LAST_LINE_SPLITTING_CHARACTER

POSSIBLE_MAKEFILE_NAMES = "GNUmakefile", "makefile", "Makefile"
DUMMY_SH_COMMAND_RESULT_CLASS = namedtuple("ShCommandResult", "exit_code")


def is_multifile_submission(submission_dir: Path, possible_source_file_stems: List[str]) -> bool:
    if not submission_dir.is_dir():
        return False
    contents = list(submission_dir.iterdir())
    # Seek the innermost non-single-file directory
    # in case the directory contains another directory with the project (common issue when zipping directories)
    while len(contents) == 1 and contents[0].is_dir():
        contents = list(contents[0].iterdir())

    for f in submission_dir.iterdir():
        if _is_makefile(f) or find_appropriate_source_file_stem(f, possible_source_file_stems) is not None:
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
    def is_a_type_of(cls, file: Path, possible_source_file_stems: List[str]) -> bool:
        return contains_shebang(file) or is_multifile_submission(file, possible_source_file_stems)

    @classmethod
    def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
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
            return _find_submission_executable(student_dir, possible_source_file_stems)

    def compile_testcase(self, precompiled_submission: Path):
        return lambda *a, **kw: self._run_stdout_only_testcase(precompiled_submission, *a, **kw)

    def prepend_test_helper(self):
        """We don't need TestHelper when we are only checking inputs/outputs"""

    def delete_executable_files(self, precompiled_submission: Path):
        """We don't compile each testcase separately so we don't need to clean up executable files"""

    def delete_source_file(self, source_path: Path):
        """There is no testcase file"""

    def _run_stdout_only_testcase(self, precompiled_submission: Path, *args, **kwargs):
        # Abstract testcase changes the default ok code from (0,) to (3, 4, 5),
        # making running any regular program viewed as crashing.
        if kwargs.get("_ok_code", None) is not None:
            kwargs.pop("_ok_code")
        try:
            sh.Command(precompiled_submission)(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            raise e

        # We fake the validation string because there is no way we can truly validate such testcases
        kwargs["_out"].write(f"\n-1{LAST_LINE_SPLITTING_CHARACTER}{self.validating_string}")
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


def _find_submission_executable(student_dir: Path, possible_source_file_stems: List[str]):
    for f in student_dir.iterdir():
        if find_appropriate_source_file_stem(f, possible_source_file_stems):
            return f


def _make_executable(f: Path) -> None:
    f.chmod(f.stat().st_mode | stat.S_IEXEC)
