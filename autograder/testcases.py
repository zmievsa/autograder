import py_compile
import shutil
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
from typing import Callable

import sh  # type: ignore

from .exit_codes import USED_EXIT_CODES, ExitCodeEventType, ExitCodeHandler
from .output_validator import generate_validating_string, validate_output
from .util import GRADER_DIR, ArgList, AutograderError, format_template, get_stderr


def get_allowed_languages():
    return {
        "c": CTestCase,
        "java": JavaTestCase,
        "python": PythonTestCase,
        "c++": CPPTestCase,
    }


# TODO: Rename-rewrite some methods in this class to make it easier to subclass
class TestCase(ABC):
    source_suffix = ".source_suffix"  # dummy value
    executable_suffix = ".executable_suffix"  # dummy value
    path_to_helper_module: Path
    exit_code_handler: ExitCodeHandler = ExitCodeHandler()
    weight: float
    per_char_formatting_disabled: bool
    full_output_formatting_disabled: bool

    def __init__(
        self,
        path: Path,
        input_dir: Path,
        output_dir: Path,
        timeout: int,
        formatters,
        argument_lists: dict,
        anti_cheat_enabled,
        weight,
        per_char_formatting_disabled,
        full_output_formatting_disabled,
    ):
        self.path = path
        self.timeout = timeout
        self.formatters = formatters
        self.argument_lists = argument_lists
        self.anti_cheat_enabled = anti_cheat_enabled
        self.weight = weight
        self.max_score = int(weight * 100)
        output_file = output_dir / f"{path.stem}.txt"
        self.per_char_formatting_disabled = per_char_formatting_disabled
        self.full_output_formatting_disabled = full_output_formatting_disabled
        if output_file.exists():
            with output_file.open() as f:
                self.expected_output = self.format_output(f.read())
        else:
            self.expected_output = StringIO("")
        input_file = input_dir / f"{path.stem}.txt"
        if input_file.exists():
            with input_file.open() as f:
                self.input = StringIO(f.read().strip())
        else:
            self.input = StringIO("")

        # Only really works if test name is in snake_case
        self.name = path.stem.replace("_", " ").capitalize()

        self.validating_string = generate_validating_string()

        self.prepend_test_helper()
        if anti_cheat_enabled:
            self.precompile_testcase()

        # This is done to hide the contents of testcases and exit codes to the student
        if anti_cheat_enabled:
            with self.path.open("rb") as f:
                self.source_contents = f.read()
            self.path.unlink()

    def run(self, precompiled_submission: Path):
        """ Returns student score and message to be displayed """
        result, message = self._weightless_run(precompiled_submission)
        self.delete_executable_files(precompiled_submission)
        return result * self.weight, message

    def _weightless_run(self, precompiled_submission: Path):
        """ Returns student score (without applying testcase weight) and message to be displayed """
        self.input.seek(0)
        testcase_path = precompiled_submission.with_name(self.path.name)
        if self.anti_cheat_enabled:
            with testcase_path.open("wb") as f:
                f.write(self.source_contents)
        else:
            shutil.copy(self.path, testcase_path)
        try:
            test_executable = self.compile_testcase(precompiled_submission)
        except sh.ErrorReturnCode as e:
            return 0, get_stderr(self.path.parent, e, "Failed to compile")
        self.delete_source_file(testcase_path)
        with StringIO() as runtime_output:
            try:
                # Useful during testing
                # input("Waiting...")
                # sleep(15)
                result = test_executable(
                    _in=self.input, _out=runtime_output, _timeout=self.timeout, _ok_code=USED_EXIT_CODES
                )
            except sh.TimeoutException:
                return 0, "Exceeded Time Limit"
            except sh.ErrorReturnCode as e:
                # http://man7.org/linux/man-pages/man7/signal.7.html
                exit_code = e.exit_code  # type: ignore
                return 0, f"Crashed due to signal {exit_code}:\n{e.stderr.decode('UTF-8', 'replace')}\n"
            # print(">>> Testcase output: " + runtime_output.getvalue())
            output, output_is_valid = validate_output(runtime_output.getvalue(), self.validating_string)
            event = self.exit_code_handler.scan(result.exit_code)
            if not output_is_valid:
                # This  means that either the student used built-in exit function himself
                # or some testcase helper is broken, or a testcase exits itself without
                # the use of helper functions.
                return (
                    0,
                    "None of the helper functions have been called.\n"
                    f"Instead, exit() has been called with exit_code {result.exit_code}.\n"
                    "It could indicate student cheating or testcases being written incorrectly.",
                )
            elif event.type == ExitCodeEventType.CHECK_OUTPUT:
                if self.format_output(output) == self.expected_output:
                    return 100, f"{int(100 * self.weight)}/{self.max_score}"
                else:
                    return 0, f"0/{self.max_score} (Wrong answer)"
            elif event.type == ExitCodeEventType.RESULT:
                score = event.value
                message = f"{int(score * self.weight)}/{self.max_score}"
                if score == 0:
                    message += " (Wrong answer)"
                return score, message
            elif event.type == ExitCodeEventType.SYSTEM_ERROR:
                # We should already handle this case in try, except block. Maybe we need more info in the error?
                raise NotImplementedError("System error has not been handled.")
            else:
                raise ValueError(f"Unknown system code {event.type} has not been handled.")

    def make_executable_path(self, submission: Path):
        """ By combining test name and student name, it makes a unique path """
        return submission.with_name(self.path.stem + submission.stem + self.executable_suffix)

    def format_output(self, output: str):
        formatted_output = output
        if not self.full_output_formatting_disabled:
            formatted_output = self.formatters["full_output_formatter"](formatted_output)
        if not self.per_char_formatting_disabled:
            formatted_output = "".join(self.formatters["per_char_formatter"](c) for c in formatted_output)
        return formatted_output

    @classmethod
    def precompile_submission(cls, submission: Path, student_dir: Path, source_file_name) -> Path:
        """Copies student submission into currect_dir and either precompiles
        it and returns the path to the precompiled submission or to the
        copied submission if no precompilation is necesessary

        pwd = temp/student_dir
        """
        destination = student_dir / source_file_name
        shutil.copy(str(submission), str(destination))
        return destination

    def precompile_testcase(self):
        """Replaces the original testcase file with its compiled version,
        thus making reading its contents as plaintext harder.
        Useful in preventing cheating.

        pwd = AutograderPaths.current_dir (i.e. the directory with all submissions)
        """
        pass

    @abstractmethod
    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        """Either precompiles student submission and returns the path to
        the precompiled submission or to original submission if no
        precompilation is necesessary

        pwd = temp/student_dir
        """
        pass

    def prepend_test_helper(self):
        """Prepends all of the associated test_helper code to test code

        pwd = AutograderPaths.current_dir (i.e. the directory with all submissions)
        """
        with self.path.open() as f:
            content = f.read()
            final_content = self.get_formatted_test_helper() + "\n" + content
        with self.path.open("w") as f:
            f.write(final_content)

    def get_formatted_test_helper(self) -> str:
        with self.path_to_helper_module.open() as helper_file:
            kwargs = {"VALIDATING_STRING": self.validating_string, **self.exit_code_handler.get_formatted_exit_codes()}
            return format_template(helper_file.read(), **kwargs)

    def delete_executable_files(self, precompiled_submission):
        pass

    def delete_source_file(self, source_path):
        source_path.unlink()

    def cleanup(self):
        self.input.close()
        self.path.unlink()


class CTestCase(TestCase):
    source_suffix = ".c"
    executable_suffix = ".out"
    path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.c"
    SUBMISSION_COMPILATION_ARGS = ("-Dscanf_s=scanf", "-Dmain=__student_main__")
    compiler = sh.gcc  # type: ignore

    @classmethod
    def precompile_submission(cls, submission, student_dir, source_file_name):
        """Links student submission without compiling it.
        It is done to speed up total compilation time
        """
        copied_submission = super().precompile_submission(submission, student_dir, submission.name)
        precompiled_submission = copied_submission.with_suffix(".o")
        try:
            cls.compiler("-c", f"{copied_submission}", "-o", precompiled_submission, *cls.SUBMISSION_COMPILATION_ARGS)
        finally:
            copied_submission.unlink()
        return precompiled_submission

    def precompile_testcase(self):
        self.compiler(
            "-c",
            self.path,
            "-o",
            self.path.with_suffix(".o"),
            *self.argument_lists[ArgList.testcase_precompilation],
        )
        self.path.unlink()
        self.path = self.path.with_suffix(".o")

    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        executable_path = self.make_executable_path(precompiled_submission)
        self.compiler(
            "-o",
            executable_path,
            precompiled_submission.with_name(self.path.name),
            str(precompiled_submission),
            *self.argument_lists[ArgList.testcase_compilation],
        )
        return sh.Command(executable_path)

    def delete_executable_files(self, precompiled_submission):
        exec_path = self.make_executable_path(precompiled_submission)
        if exec_path.exists():
            exec_path.unlink()


class CPPTestCase(CTestCase):
    source_suffix = ".cpp"
    # path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.cpp"
    compiler = sh.Command("g++")


class JavaTestCase(TestCase):
    """Please, ask students to remove their main as it can theoretically
    generate errors (not sure how though).
    Java doesn't support precompilation yet. Read precompile_testcase()
    for more info.
    """

    source_suffix = ".java"
    executable_suffix = ""
    path_to_helper_module = GRADER_DIR / "test_helpers/TestHelper.java"
    parallel_execution_supported = False
    compiler = sh.javac  # type: ignore
    virtual_machine = sh.java  # type: ignore

    @classmethod
    def precompile_submission(cls, submission: Path, student_dir: Path, source_file_name: str):
        """ Renames submission to allow javac compilation """
        copied_submission = super().precompile_submission(submission, student_dir, submission.name)
        precompiled_submission = copied_submission.parent / source_file_name
        copied_submission.rename(precompiled_submission)
        return precompiled_submission

    def compile_testcase(self, precompiled_submission: Path) -> Callable:
        new_self_path = precompiled_submission.with_name(self.path.name)
        self.compiler(precompiled_submission, new_self_path, *self.argument_lists[ArgList.testcase_compilation])
        return lambda *args, **kwargs: self.virtual_machine(self.path.stem, *args, **kwargs)

    def delete_executable_files(self, precompiled_submission: Path):
        for p in precompiled_submission.parent.iterdir():
            if p.suffix == ".class":
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
            raise AutograderError(f"Braces in testcase '{self.name}' don't match.")


class PythonTestCase(TestCase):
    """A proof of concept of how easy it is to add new languages.
    Will only work if python is accessible via python3 alias for now.
    """

    source_suffix = ".py"
    executable_suffix = ".pyc"
    path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.py"
    interpreter = sh.python3  # type: ignore

    def compile_testcase(self, precompiled_submission: Path) -> Callable:
        # Argument lists do not seem to work here
        # Test it, plz.
        return lambda *args, **kwargs: self.interpreter(
            precompiled_submission.with_name(self.path.name),
            precompiled_submission.stem,
            *self.argument_lists[ArgList.testcase_compilation],
            **kwargs,
        )

    def precompile_testcase(self):
        kwargs = {}
        if "-O" in self.argument_lists[ArgList.testcase_precompilation]:
            kwargs["optimize"] = 1
        if "-OO" in self.argument_lists[ArgList.testcase_precompilation]:
            kwargs["optimize"] = 2
        executable_path = self.path.with_suffix(self.executable_suffix)
        py_compile.compile(file=str(self.path), cfile=str(executable_path), **kwargs)
        self.path.unlink()
        self.path = executable_path

    def delete_source_file(self, source_path):
        pass
