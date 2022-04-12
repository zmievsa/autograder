import asyncio
import py_compile
import sys
from pathlib import Path
from typing import List

from autograder.testcase_utils.abstract_testcase import TestCase as AbstractTestCase
from autograder.testcase_utils.shell import EMPTY_COMMAND, ShellError, get_shell_command


class TestCase(AbstractTestCase):
    """A proof of concept of how easy it is to add new languages.
    Will only work if python is accessible via python3 alias for now.
    """

    source_suffix = ".py"
    executable_suffix = ".pyc"
    helper_module = "test_helper.py"  # type: ignore
    interpreter = get_shell_command(sys.executable)

    @classmethod
    def is_installed(cls) -> bool:
        return cls.interpreter is not EMPTY_COMMAND

    @classmethod
    async def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        cli_args: str,
        *args,
        **kwargs,
    ):
        copied_submission = await super().precompile_submission(
            submission, student_dir, [submission.stem], cli_args, *args, **kwargs
        )
        kwargs = {}
        if "-O" in cli_args:
            kwargs["optimize"] = 1
        executable_path = copied_submission.with_suffix(cls.executable_suffix)
        try:
            py_compile.compile(file=str(copied_submission), cfile=str(executable_path), doraise=True)
        except Exception as e:
            raise ShellError(1, str(e)) from e
        copied_submission.unlink()
        return executable_path

    async def compile_testcase(self, precompiled_submission: Path, cLi_args: str):
        return lambda *args, **kwargs: self.interpreter(
            self.make_executable_path(precompiled_submission),
            *args,
            env={
                "STUDENT_SUBMISSION": precompiled_submission.stem,
                **kwargs.pop("env"),
            },
            **kwargs,
        )

    async def precompile_testcase(self, cli_args: str):
        kwargs = {}
        if "-O" in cli_args:
            kwargs["optimize"] = 1
        executable_path = self.path.with_suffix(self.executable_suffix)
        py_compile.compile(file=str(self.path), cfile=str(executable_path), doraise=True, **kwargs)
        self.path.unlink()
        self.path = executable_path

    def delete_source_file(self, source_path: Path):
        """Source file is the same as executable file so we don't need to delete it"""

    def make_executable_path(self, submission: Path) -> Path:
        return submission.with_name(self.path.name)
