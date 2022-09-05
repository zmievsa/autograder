import asyncio
import mimetypes
import os
import shutil
import stat
import sys
from enum import Enum
from os import PathLike
from pathlib import Path, PosixPath, WindowsPath
from typing import TYPE_CHECKING, Any, Callable, List, Mapping, Optional, Type

from .testcase_io import EMPTY_TESTCASE_IO

from ..config_manager import GradingConfig
from .abstract_testcase import TestCase, TestCaseResult
from .exit_codes import ExitCodeEventType
from .shell import ShellCommand, ShellError, get_shell_command
from .submission import find_appropriate_source_file_stem
from .testcase_io import TestCaseIO
from .testcase_result_validator import LAST_LINE_SPLITTING_CHARACTER

POSSIBLE_MAKEFILE_NAMES = "GNUmakefile", "makefile", "Makefile"
MULTIFILE_SUBMISSION_NAME = "<<<Makefile>>>"  # This is a hack to give a semi-unique name to multifile submissions

if TYPE_CHECKING:
    from .testcase_picker import TestCasePicker


class PathWithStdoutOnlyInfo(type(Path())):
    """This abomination is a hack to supply more info when running stdout only
    submissions. To prevent hacks like this, the architecture will need to be
    restructured to allow for things like stdout-only submissions.

    I have a feeling we needed to focus on composition instead of inheritance (arguably)
    and implement a different grader class for stdout submissions (definitely).
    """

    compiled_submission: Optional[ShellCommand]
    picked_testcase_type: Optional[Type[TestCase]]

    def __new__(
        cls,
        *args,
        compiled_submission: Optional[ShellCommand] = None,
        picked_testcase_type: Optional[Type[TestCase]] = None,
    ):
        self = cls._from_parts(args, init=False)  # type: ignore
        if not self._flavour.is_supported:
            raise NotImplementedError(f"cannot instantiate {cls.__name__} on your system")
        self._init()
        self.compiled_submission = compiled_submission
        self.picked_testcase_type = picked_testcase_type
        return self


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
    return path.is_file() and path.name in POSSIBLE_MAKEFILE_NAMES


def contains_shebang(path: Path) -> bool:
    guessed_type = mimetypes.guess_type(str(path))[0]
    if not path.is_file() or guessed_type is None or not guessed_type.startswith("text/"):
        return False
    # Windows does not support shebang lines
    if sys.platform.startswith("win32"):
        return False
    with open(path) as f:
        return f.readline().startswith("#!")


def has_supported_testcase_type(
    path: Path,
    possible_source_file_stems: List[str],
    testcase_picker: "TestCasePicker",
) -> bool:
    return path.is_file() and testcase_picker.pick(path, possible_source_file_stems) is not None


class StdoutOnlyTestCase(TestCase):

    helper_module = ""  # type: ignore
    compiler = get_shell_command("make")

    @classmethod
    def is_installed(cls) -> bool:
        """We assume all utilities necessary are installed because we can't possibly check for all of them."""
        return cls.compiler is not None

    @classmethod
    def is_a_type_of(cls, path: Path, possible_source_file_stems: List[str], testcase_picker: "TestCasePicker") -> bool:
        return (
            contains_shebang(path)
            or has_supported_testcase_type(path, possible_source_file_stems, testcase_picker)
            or is_multifile_submission(path, possible_source_file_stems)
        )

    @classmethod
    async def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        cli_args: str,
        config: GradingConfig,
        lock: asyncio.Lock,
        testcase_picker: "TestCasePicker",
    ):
        """pwd is temp/student_dir"""

        # Single-file with shebang
        if contains_shebang(submission):
            destination = student_dir / submission.name
            shutil.copy(str(submission), str(destination))
            _make_executable(destination)
            return PathWithStdoutOnlyInfo(destination)
        # A directory with a makefile
        elif submission.is_dir():
            _copy_multifile_submission_contents_into_student_dir(submission, student_dir)
            try:
                await cls.compiler("compile", "--silent", *cli_args.split(), cwd=student_dir)
            except ShellError as e:
                # Wat. Why? TODO: Why did I do this?
                if "no makefile found" not in str(e):
                    raise e
            return PathWithStdoutOnlyInfo(student_dir / MULTIFILE_SUBMISSION_NAME)
        else:
            ttype = testcase_picker.pick(submission, possible_source_file_stems)
            # FIXME: This should be a part of the TestCasePicker.pick() method. Or not?
            stem = find_appropriate_source_file_stem(submission, possible_source_file_stems)
            if ttype is None:
                raise ShellError(1, f"Failed to find a testcase type for submission {submission.name}")
            if stem is not None:
                stems = [stem]
            else:
                stems = possible_source_file_stems
            precompiled_submission = await ttype.precompile_submission(
                submission,
                student_dir,
                stems,
                cli_args,
                config,
                lock,
                testcase_picker,
                remove_student_main=False,
            )
            final_executable = await ttype(
                precompiled_submission,
                0,
                0,
                EMPTY_TESTCASE_IO,
                config.file,
                testcase_picker,
                prepend_test_helper=False,
            ).compile_testcase(precompiled_submission, cli_args)
            return PathWithStdoutOnlyInfo(
                precompiled_submission,
                compiled_submission=final_executable,
                picked_testcase_type=ttype,
            )

    async def compile_testcase(self, precompiled_submission: PathWithStdoutOnlyInfo, cli_args: str) -> ShellCommand:
        return _add_args(self._run_stdout_only_testcase, precompiled_submission, cli_args)

    def prepend_test_helper(self):
        """We don't need TestHelper when we are only checking inputs/outputs"""

    def delete_executable_files(self, precompiled_submission: Path):
        """We don't compile each testcase separately so we don't need to clean up executable files"""

    def delete_source_file(self, source_path: Path):
        """There is no testcase file"""

    async def _run_stdout_only_testcase(
        self,
        precompiled_submission: PathWithStdoutOnlyInfo,
        cli_args: str,
        *args: Any,
        **kwargs: Any,
    ):
        # Because student submissions do not play by our ExitCodeEventType rules,
        # we allow them to return 0 at the end.
        kwargs["allowed_exit_codes"] = (0,)
        compiled_submission = precompiled_submission.compiled_submission
        if compiled_submission is not None:
            result = await compiled_submission(*args, **kwargs)
        elif precompiled_submission.name == MULTIFILE_SUBMISSION_NAME:
            result = await self.compiler("run", "--silent", *args, **kwargs)
        else:
            result = await ShellCommand(precompiled_submission)(*args, **kwargs)

        # We fake the validation string because there is no way we can truly validate such testcases
        result.stdout += f"\n-1{LAST_LINE_SPLITTING_CHARACTER}{self.validating_string}"
        result.returncode = ExitCodeEventType.CHECK_STDOUT
        return result

    async def _weightless_run(
        self,
        precompiled_submission: PathWithStdoutOnlyInfo,
        compiled_testcase: ShellCommand,
        testcase_runtime_args: str,
    ) -> TestCaseResult:
        if precompiled_submission.picked_testcase_type is not None:
            return await precompiled_submission.picked_testcase_type._weightless_run(
                self,
                precompiled_submission,
                compiled_testcase,
                testcase_runtime_args,
            )
        else:
            return await super(type(self), self)._weightless_run(
                precompiled_submission, compiled_testcase, testcase_runtime_args
            )


def _copy_multifile_submission_contents_into_student_dir(submission: Path, student_dir: Path):
    contents: List[Path] = list(submission.iterdir())
    while len(contents) == 1 and contents[0].is_dir():
        contents = list(contents[0].iterdir())
    for f in contents:
        new_path = student_dir / f.name
        op: Callable[[PathLike, PathLike], Any]
        if f.is_dir():
            op = shutil.copytree
        else:
            op = shutil.copyfile
        op(f, new_path)


def _make_executable(f: Path) -> None:
    f.chmod(f.stat().st_mode | stat.S_IEXEC)


def _add_args(function: Callable[..., Any], *initial_args: Any) -> Callable[..., Any]:
    async def inner(*args: Any, **kwargs: Any):
        return await function(*initial_args, *args, **kwargs)

    return inner
