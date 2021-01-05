from pathlib import Path
import shutil
from typing import List

import sh
from .abstract_base_class import Command, TestCase

POSSIBLE_MAKEFILE_NAMES = "GNUmakefile", "makefile", "Makefile"


def is_multifile_submission(submission_dir: Path, source_file_stem, lower_source_file_stem: bool):
    contents = list(submission_dir.iterdir())
    while len(contents) == 1 and contents[0].is_dir():
        contents = list(contents[0].iterdir())

    # TODO: Remove repetition of code piece below
    if lower_source_file_stem:
        source_file_stem = source_file_stem.lower()
    for f in submission_dir.iterdir():
        if (
            _is_makefile(f)
            or (lower_source_file_stem and f.stem.lower() == source_file_stem)
            or (not lower_source_file_stem and f.stem == source_file_stem)
        ):
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

    def prepend_test_helper(self):
        """ We don't need TestHelper when we are only checking inputs/outputs """

    @classmethod
    def precompile_submission(
        cls, submission: Path, student_dir: Path, source_file_stem: str, lower_source_filename: bool, arglist
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
        return _find_submission_executable(student_dir, source_file_stem, lower_source_filename)

    def compile_testcase(self, precompiled_submission: Path):
        return sh.Command(precompiled_submission)

    def prepend_test_helper(self):
        """We don't need test helper because we don't have a testcase file"""
        pass

    def delete_executable_files(self, precompiled_submission: Path):
        """ We don't compile each testcase separately so we don't need to clean up executable files """
        pass

    def delete_source_file(self, source_path: Path):
        """ There is no testcase file """
        pass


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


def _find_submission_executable(student_dir: Path, source_file_stem: str, lower_source_filename):
    if lower_source_filename:
        source_file_stem = source_file_stem.lower()
    for f in student_dir.iterdir():
        if lower_source_filename and f.stem.lower() == source_file_stem:
            return f
        elif not lower_source_filename and f.stem == source_file_stem:
            return f
