from autograder.util import AutograderError
from pathlib import Path
from typing import Callable
from .abstract_base_class import ArgList, TestCase
import sh


class JavaTestCase(TestCase):
    """Please, ask students to remove their main as it can theoretically
    generate errors (not sure how though).
    Java doesn't support testcase precompilation because it must always
    link files on compilation.
    """

    source_suffix = ".java"
    executable_suffix = ""
    helper_module_name = "TestHelper.java"
    parallel_execution_supported = False
    compiler = sh.javac  # type: ignore
    virtual_machine = sh.java  # type: ignore

    @classmethod
    def precompile_submission(cls, submission: Path, student_dir: Path, source_file_name: str):
        copied_submission = super().precompile_submission(submission, student_dir, submission.name)
        renamed_submission = copied_submission.parent / source_file_name
        copied_submission.rename(renamed_submission)
        # TODO: What about submission precompilation args? We can't pass them if it's a classmethod
        try:
            cls.compiler(renamed_submission)
        finally:
            renamed_submission.unlink()

        # What if there are multiple .class files after compilation? What do we do, then?
        return renamed_submission

    def compile_testcase(self, precompiled_submission: Path) -> Callable:
        new_self_path = precompiled_submission.with_name(self.path.name)
        self.compiler(new_self_path, *self.argument_lists[ArgList.TESTCASE_COMPILATION])
        return lambda *args, **kwargs: self.virtual_machine(self.path.stem, *args, **kwargs)

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
            final_content = self._add_at_the_end_of_public_class(self.get_formatted_test_helper(), content)
        with open(self.path, "w") as f:
            f.write(final_content)

    def _add_at_the_end_of_public_class(self, helper_class: str, java_file: str):
        # TODO: Figure out a better way to do this.
        # This way is rather crude and can be prone to errors,
        # but java does not really leave us any other way to do it.

        # Wait, what if there's a public method in private class? We should find the 'public .+ class' regex
        main_class_index = java_file.find("public")

        file_starting_from_main_class = java_file[main_class_index:]
        closing_brace_index = self._find_closing_brace(file_starting_from_main_class)
        return "".join(
            [
                java_file[:main_class_index],
                file_starting_from_main_class[:closing_brace_index],
                "\n" + helper_class + "\n" + "}",
                java_file[closing_brace_index + 1 :],
            ]
        )

    def _find_closing_brace(self, s: str):
        bracecount = 0
        for i in range(len(s)):
            if s[i] == "{":
                bracecount += 1
            elif s[i] == "}":
                bracecount -= 1
                if bracecount == 0:
                    return i
        else:
            raise AutograderError(f"Braces in testcase '{self.path.name}' don't match.")