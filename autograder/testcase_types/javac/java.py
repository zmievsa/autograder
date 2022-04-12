import asyncio
import re
import shutil
import sys
from pathlib import Path
from typing import Any, List, Mapping

from autograder.config_manager import GradingConfig
from autograder.testcase_utils.abstract_testcase import TestCase as AbstractTestCase
from autograder.testcase_utils.shell import EMPTY_COMMAND, ShellError, get_shell_command
from autograder.testcase_utils.submission import find_appropriate_source_file_stem
from autograder.util import AutograderError

PUBLIC_CLASS_MATCHER = re.compile(r"public(?:\w|\s)+class(?:\w|\s)+({)")

# Previously, we used SecurityManager to prevent reflection but now
# it's deprecated and we're forced to resort to this hack. It's not
# perfect but java does not leave us any other options.
REFLECTION_MATCHER = re.compile(r"import(\s+)java\.lang\.reflect\.")

# Java does not allow us to properly unset environment variables
# which is why we must use JNA to do so. However, because we are
# forced to insert our TestHelper into TestCase class, we cannot
# define any imports on top of it. Hence we have to use this hack.
LIBRARIES_REQUIRED_FOR_UNSETENV = """
import com.sun.jna.Library;
import com.sun.jna.Native;
import java.lang.reflect.Field;
import java.util.Map;
import java.util.HashMap;

"""
if sys.platform.startswith("win32"):
    ADDITIONAL_TEST_HELPER_KWARGS = {"SETENV": "_putenv", "C_LIBRARY": "msvcrt"}
    CLASSPATH = ".;jna.jar"
else:
    ADDITIONAL_TEST_HELPER_KWARGS = {"SETENV": "setenv", "C_LIBRARY": "c"}
    CLASSPATH = ".:*"


EXTRA_DIR = Path(__file__).parent / "extra"
PATH_TO_JNA_FILE = EXTRA_DIR / "jna.jar"


class TestCase(AbstractTestCase):
    """Please, ask students to remove their main as it can theoretically
    generate errors (not sure how though).
    Java doesn't support testcase precompilation because it must always
    link files on compilation.
    """

    source_suffix = ".java"
    executable_suffix = ""
    helper_module = "TestHelper.java"  # type: ignore
    compiler = get_shell_command("javac")
    virtual_machine = get_shell_command("java")

    @classmethod
    def is_installed(cls) -> bool:
        return cls.compiler is not EMPTY_COMMAND and cls.virtual_machine is not EMPTY_COMMAND

    @classmethod
    async def precompile_submission(
        cls, submission: Path, student_dir: Path, possible_source_file_stems: List[str], cli_args: str, *args, **kwargs
    ):
        stem = find_appropriate_source_file_stem(submission, possible_source_file_stems)
        if stem is None:
            raise AutograderError(
                f"Submission {submission} has an inappropriate file name. Please, specify POSSIBLE_SOURCE_FILE_STEMS in config.ini"
            )
        copied_submission = await super().precompile_submission(
            submission, student_dir, [stem], cli_args, *args, **kwargs
        )
        try:
            if not REFLECTION_MATCHER.search(copied_submission.read_text()):
                await cls.compiler(copied_submission, *cli_args.split(), cwd=student_dir)
            else:
                raise ShellError(1, "The use of reflection is forbidden in student submissions.")
        finally:
            copied_submission.unlink()

        return copied_submission.with_suffix(".class")

    async def compile_testcase(self, precompiled_submission: Path, cli_args: str):
        new_self_path = precompiled_submission.with_name(self.path.name)
        await self.compiler(
            new_self_path,
            "-cp",
            CLASSPATH,
            *cli_args.split(),
            cwd=precompiled_submission.parent,
        )
        return lambda *args, **kwargs: self.virtual_machine("-cp", CLASSPATH, self.path.stem, *args, **kwargs)

    @classmethod
    def run_additional_testcase_operations_in_student_dir(cls, student_dir: Path):
        shutil.copyfile(PATH_TO_JNA_FILE, student_dir / PATH_TO_JNA_FILE.name)

    def delete_executable_files(self, precompiled_submission: Path):
        for p in precompiled_submission.parent.iterdir():
            if p.suffix == ".class" and self.path.stem in p.stem:
                p.unlink()

    def prepend_test_helper(self):
        """Puts private TestHelper at the end of testcase class.
        This is quite a crude way to do it but it is the easiest
        I found so far.
        """
        content = self.path.read_text()
        formatted_test_helper = self.get_formatted_test_helper(**ADDITIONAL_TEST_HELPER_KWARGS)
        final_content = self._add_at_the_beginning_of_public_class(formatted_test_helper, content)
        self.path.write_text(LIBRARIES_REQUIRED_FOR_UNSETENV + final_content)

    def _add_at_the_beginning_of_public_class(self, helper_class: str, java_file: str):
        """Looks for the first bracket of the first public class and inserts test helper next to it"""
        # This way is rather crude and can be prone to errors if left untested,
        # but java does not really leave us any other way to do it.
        match = PUBLIC_CLASS_MATCHER.search(java_file)
        if not match:
            raise ValueError(f"Public class not found in {self.path}")
        else:
            main_class_index = match.end(1)

        return "".join(
            [
                java_file[:main_class_index],
                "\n" + helper_class + "\n",
                java_file[main_class_index:],
            ]
        )
