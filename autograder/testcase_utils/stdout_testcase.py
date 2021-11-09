import shutil
import stat
import sys
from pathlib import Path
from typing import Any, Callable, List


from ..config_manager import GradingConfig
from .abstract_testcase import TestCase
from .exit_codes import ExitCodeEventType
from .shell import ShellCommand, ShellError, get_shell_command
from .submission import find_appropriate_source_file_stem
from .testcase_result_validator import LAST_LINE_SPLITTING_CHARACTER

POSSIBLE_MAKEFILE_NAMES = "GNUmakefile", "makefile", "Makefile"


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
    # Windows does not support shebang lines
    if sys.platform.startswith("win32"):
        return False
    with open(path) as f:
        return f.readline().startswith("#!")


class StdoutOnlyTestCase(TestCase):

    helper_module = ""  # type: ignore
    compiler = get_shell_command("make")

    @classmethod
    def is_installed(cls) -> bool:
        """We assume all utilities necessary are installed because we can't possibly check for all of them."""
        return cls.compiler is not None

    @classmethod
    def is_a_type_of(cls, file: Path, possible_source_file_stems: List[str]) -> bool:
        return contains_shebang(file) or is_multifile_submission(file, possible_source_file_stems)

    @classmethod
    async def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        cli_args: str,
        config: GradingConfig,
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
                await cls.compiler(*cli_args.split(), cwd=student_dir)
            except ShellError as e:
                if "no makefile found" not in str(e):
                    raise e
            executable = _find_submission_executable(student_dir, possible_source_file_stems)
            if executable is None:
                raise ShellError(
                    -1,
                    "Submission was successfully precompiled but the executable could not be found. Most likely it was not in POSSIBLE_SOURCE_FILE_STEMS.",
                )
            return executable

    async def compile_testcase(self, precompiled_submission: Path, cli_args: str):
        return _add_args(self._run_stdout_only_testcase, precompiled_submission)

    def prepend_test_helper(self):
        """We don't need TestHelper when we are only checking inputs/outputs"""

    def delete_executable_files(self, precompiled_submission: Path):
        """We don't compile each testcase separately so we don't need to clean up executable files"""

    def delete_source_file(self, source_path: Path):
        """There is no testcase file"""

    async def _run_stdout_only_testcase(self, precompiled_submission: Path, *args: Any, **kwargs: Any):
        # Because student submissions do not play by our ExitCodeEventType rules,
        # we allow them to return 0 at the end.
        kwargs["allowed_exit_codes"] = (0,)
        result = await ShellCommand(precompiled_submission)(*args, **kwargs)

        # We fake the validation string because there is no way we can truly validate such testcases
        result.stdout += f"\n-1{LAST_LINE_SPLITTING_CHARACTER}{self.validating_string}"
        result.returncode = ExitCodeEventType.CHECK_STDOUT
        return result


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
    print(list(student_dir.iterdir()), "\n", possible_source_file_stems)
    for f in student_dir.iterdir():
        if find_appropriate_source_file_stem(f, possible_source_file_stems):
            return f


def _make_executable(f: Path) -> None:
    f.chmod(f.stat().st_mode | stat.S_IEXEC)


def _add_args(function: Callable[..., Any], *initial_args: Any) -> Callable[..., Any]:
    async def inner(*args: Any, **kwargs: Any):
        return await function(*initial_args, *args, **kwargs)

    return inner
