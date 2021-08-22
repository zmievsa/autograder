import re
import shutil
from pathlib import Path
from typing import List

from autograder.testcase_utils.abstract_testcase import ArgList, TestCase as AbstractTestCase
from autograder.testcase_utils.shell import Command
from autograder.testcase_utils.submission import find_appropriate_source_file_stem
from autograder.util import AutograderError

PUBLIC_CLASS_MATCHER = re.compile(r"public(?:\w|\s)+class(?:\w|\s)+({)")
EXTRA_DIR = Path(__file__).parent / "extra"
PATH_TO_JNA_FILE = EXTRA_DIR / "jna.jar"
PATH_TO_SECURITY_MANAGER_FILE = EXTRA_DIR / "NoReflectionAndEnvVarsSecurityManager.class"


class TestCase(AbstractTestCase):
    """Please, ask students to remove their main as it can theoretically
    generate errors (not sure how though).
    Java doesn't support testcase precompilation because it must always
    link files on compilation.
    """

    source_suffix = ".java"
    executable_suffix = ""
    helper_module = "TestHelper.java"
    compiler = Command("javac")
    virtual_machine = Command("java")

    @classmethod
    def is_installed(cls) -> bool:
        return cls.compiler is not None and cls.virtual_machine is not None

    @classmethod
    def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        arglist,
    ):
        stem = find_appropriate_source_file_stem(submission, possible_source_file_stems)
        if stem is None:
            raise AutograderError(
                f"Submission {submission} has an inappropriate file name. Please, specify POSSIBLE_SOURCE_FILE_STEMS in config.ini"
            )
        copied_submission = super().precompile_submission(submission, student_dir, [stem], arglist)
        try:
            cls.compiler(copied_submission, *arglist)
        finally:
            copied_submission.unlink()

        return copied_submission.with_suffix(".class")

    def compile_testcase(self, precompiled_submission: Path):
        new_self_path = precompiled_submission.with_name(self.path.name)
        self.compiler(
            new_self_path,
            "-cp",
            f".:*",
            *self.argument_lists[ArgList.TESTCASE_COMPILATION],
        )
        return lambda *args, **kwargs: self.virtual_machine("-cp", ".:*", self.path.stem, *args, **kwargs)

    @classmethod
    def run_additional_testcase_operations_in_student_dir(cls, student_dir: Path):
        shutil.copyfile(PATH_TO_JNA_FILE, student_dir / PATH_TO_JNA_FILE.name)
        shutil.copyfile(PATH_TO_SECURITY_MANAGER_FILE, student_dir / PATH_TO_SECURITY_MANAGER_FILE.name)

    def delete_executable_files(self, precompiled_submission: Path):
        for p in precompiled_submission.parent.iterdir():
            if p.suffix == ".class" and self.path.stem in p.stem:
                p.unlink()

    def prepend_test_helper(self):
        """Puts private TestHelper at the end of testcase class.
        This is quite a crude way to do it but it is the easiest
        I found so far.
        """
        with open(self.path) as f:
            content = f.read()
        final_content = self._add_at_the_beginning_of_public_class(self.get_formatted_test_helper(), content)
        final_content = (
            f"""import com.sun.jna.Library;
                import com.sun.jna.Native;
                import java.lang.reflect.Field;
                import java.util.Map;
                import java.util.HashMap;
            """
            + final_content
        )
        with open(self.path, "w") as f:
            f.write(final_content)

    def _add_at_the_beginning_of_public_class(self, helper_class: str, java_file: str):
        """Looks for the first bracket of the first public class and inserts test helper next to it"""
        # This way is rather crude and can be prone to errors if left untested,
        # but java does not really leave us any other way to do it.
        match = PUBLIC_CLASS_MATCHER.search(java_file)
        if match is None:
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
