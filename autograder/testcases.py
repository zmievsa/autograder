import shutil
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
import py_compile

import sh  # type: ignore

from .util import get_stderr, format_template, ArgList, AutograderError
from .exit_codes import ExitCodeEventType, ExitCodeHandler, ALL_USED_EXIT_CODES

GRADER_DIR = Path(__file__).resolve().parent


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
        tests_dir: Path,
        timeout: int,
        formatters,
        argument_lists: dict,
        precompile_testcase,
        weight,
        per_char_formatting_disabled,
        full_output_formatting_disabled,
        dont_expose_testcase
    ):
        self.path = path
        self.timeout = timeout
        self.formatters = formatters
        self.argument_lists = argument_lists
        self.need_precompile_testcase = precompile_testcase
        self.weight = weight
        self.max_score = int(weight * 100)
        output_dir = tests_dir / f"output/{path.stem}.txt"
        self.per_char_formatting_disabled = per_char_formatting_disabled
        self.full_output_formatting_disabled = full_output_formatting_disabled
        if output_dir.exists():
            with output_dir.open() as f:
                self.expected_output = self.format_output(f.read())
        else:
            self.expected_output = StringIO("")
        input_dir = tests_dir / f"input/{path.stem}.txt"
        if input_dir.exists():
            with input_dir.open() as f:
                self.input = StringIO(f.read().strip())
        else:
            self.input = StringIO("")

        # Only really works if test name is in snake_case
        self.name = path.stem.replace("_", " ").capitalize()

        self.prepend_test_helper()
        if precompile_testcase:
            self.precompile_testcase()

        self.dont_expose_testcase = dont_expose_testcase
        # This is done to hide the contents of testcases and exit codes to the student
        if dont_expose_testcase:
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
        if self.dont_expose_testcase:
            with self.path.open("wb") as f:
                f.write(self.source_contents)
        try:
            test_executable = self.compile_testcase(precompiled_submission)
        except sh.ErrorReturnCode as e:
            return 0, get_stderr(self.path.parent, e, "Failed to compile")
        self.delete_source_file()
        with StringIO() as runtime_output:
            try:
                result = test_executable(
                    _in=self.input,
                    _out=runtime_output,
                    _timeout=self.timeout,
                    _ok_code=ALL_USED_EXIT_CODES
                )
            except sh.TimeoutException:
                return 0, "Exceeded Time Limit"
            except sh.ErrorReturnCode as e:
                # http://man7.org/linux/man-pages/man7/signal.7.html
                return 0, f"Crashed due to signal {e.exit_code}:\n{e.stderr.decode('UTF-8', 'replace')}\n"
            # print(">>> Testcase output: " + runtime_output.getvalue())
            event = self.exit_code_handler.scan(result.exit_code)
            if event.type == ExitCodeEventType.CHECK_OUTPUT:
                if self.format_output(runtime_output.getvalue()) == self.expected_output:
                    return 100, f"{int(100 * self.weight)}/{self.max_score}"
                else:
                    return 0, f"0/{self.max_score} (Wrong answer)"
            elif event.type == ExitCodeEventType.RESULT:
                score = event.value
                message = f"{int(score * self.weight)}/{self.max_score}"
                if score == 0:
                    message += " (Wrong answer)"
                return score, message
            elif event.type == ExitCodeEventType.CHEAT_ATTEMPT:
                # This  means that either the student used built-in exit function himself
                # or some testcase helper is broken, or a testcase exits itself without
                # the use of helper functions.
                return 0, f"An invalid exit code '{result.exit_code}' has been supplied.\n" \
                           "It could indicate the student cheating or testcases being written incorrectly."
            elif event.type == ExitCodeEventType.SYSTEM_ERROR:
                # We should already handle this case in try, except block
                pass

    def make_executable_path(self, submission: Path):
        """ By combining test name and student name, it makes a unique path """
        return self.path.with_name(self.path.stem + submission.stem + self.executable_suffix)

    def format_output(self, output: str):
        formatted_output = output
        if not self.full_output_formatting_disabled:
            formatted_output = self.formatters.full_output_formatter(formatted_output)
        if not self.per_char_formatting_disabled:
            final_output = ""
            for c in formatted_output:
                final_output += self.formatters.per_char_formatter(c)
            formatted_output = final_output
        return formatted_output

    @classmethod
    def precompile_submission(cls, submission: Path, current_dir: Path, source_file_name) -> Path:
        """ Copies student submission into currect_dir and either precompiles
            it and returns the path to the precompiled submission or to the
            copied submission if no precompilation is necesessary
        """
        destination = current_dir / "temp" / source_file_name
        shutil.copy(str(submission), str(destination))
        return destination

    def precompile_testcase(self):
        """ Replaces the original testcase file with its compiled version,
            thus making reading its contents as plaintext harder.
            Useful in preventing cheating.
        """
        pass

    @abstractmethod
    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        """ Either precompiles student submission and returns the path to
            the precompiled submission or to original submission if no
            precompilation is necesessary
        """
        pass

    def prepend_test_helper(self):
        """ Prepends all of the associated test_helper code to test code """
        with self.path.open() as f, self.path_to_helper_module.open() as helper_file:
            formatted_helper_file = format_template(
                helper_file.read(),
                **self.exit_code_handler.get_formatted_exit_codes()
            )
            content = f.read()
            final_content = formatted_helper_file + "\n" + content
        with self.path.open("w") as f:
            f.write(final_content)

    def delete_executable_files(self, precompiled_submission):
        pass

    def delete_source_file(self):
        if self.dont_expose_testcase:
            self.path.unlink()

    def cleanup(self):
        self.input.close()
        self.path.unlink()


class CTestCase(TestCase):
    source_suffix = ".c"
    executable_suffix = ".out"
    path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.c"
    SUBMISSION_COMPILATION_ARGS = ("-Dscanf_s=scanf", "-Dmain=__student_main__")
    compiler = sh.gcc

    @classmethod
    def precompile_submission(cls, submission, current_dir, source_file_name):
        """ Links student submission without compiling it.
            It is done to speed up total compilation time
        """
        copied_submission = super().precompile_submission(submission, current_dir, submission.name)
        precompiled_submission = copied_submission.with_suffix(".o")
        cls.compiler(
            "-c", f"{copied_submission}",
            "-o", precompiled_submission,
            *cls.SUBMISSION_COMPILATION_ARGS
        )
        return precompiled_submission

    def precompile_testcase(self):
        self.compiler(
            "-c", self.path,
            "-o", self.path.with_suffix('.o'),
            *self.argument_lists[ArgList.testcase_precompilation],
        )
        self.path.unlink()
        self.path = self.path.with_suffix('.o')

    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        executable_path = self.make_executable_path(precompiled_submission)
        self.compiler(
            "-o",
            executable_path,
            self.path,
            precompiled_submission.name,
            *self.argument_lists[ArgList.testcase_compilation]
        )
        return sh.Command(executable_path)

    def delete_executable_files(self, precompiled_submission):
        if self.dont_expose_testcase:
            self.make_executable_path(precompiled_submission).unlink()


class CPPTestCase(CTestCase):
    source_suffix = ".cpp"
    # path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.cpp"
    compiler = sh.Command("g++")


class JavaTestCase(TestCase):
    """ Please, ask students to remove their main as it can theoretically
        generate errors (not sure how though).
        Java doesn't support precompilation yet. Read precompile_testcase()
        for more info.
    """
    source_suffix = ".java"
    executable_suffix = ""
    path_to_helper_module = GRADER_DIR / "test_helpers/TestHelper.java"
    parallel_execution_supported = False

    @classmethod
    def precompile_submission(cls, submission: Path, current_dir: Path, source_file_name: str):
        """ Renames submission to allow javac compilation """
        copied_submission = super().precompile_submission(submission, current_dir, submission.name)
        precompiled_submission = copied_submission.parent / source_file_name
        copied_submission.rename(precompiled_submission)
        return precompiled_submission

    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        sh.javac(self.path, precompiled_submission.name)
        return lambda *args, **kwargs: sh.java(
            self.path.stem, *args, *self.argument_lists[ArgList.testcase_compilation], **kwargs
        )

    def delete_executable_files(self, precompiled_submission):
        precompiled_submission.with_suffix(".class").unlink()
        str(self.path.with_suffix("")) + "$" + "TestHelper.class"

    def prepend_test_helper(self):
        """ Puts private TestHelper at the end of testcase class.
            This is quite a crude way to do it but it is the easiest
            I found so far.
        """
        with open(self.path) as f, open(self.path_to_helper_module) as helper_file:
            formatted_helper_class = format_template(
                helper_file.read(),
                **self.exit_code_handler.get_formatted_exit_codes()
            )
            content = f.read()
            final_content = self._add_at_the_end_of_public_class(formatted_helper_class, content)
        with open(self.path, "w") as f:
            f.write(final_content)

    def _add_at_the_end_of_public_class(self, helper_class: str, java_file: str):
        # TODO: Figure out a better way to do this
        main_class_index = java_file.find("public")
        file_starting_from_main_class = java_file[main_class_index:]
        closing_brace_index = self._find_closing_brace(file_starting_from_main_class)
        return ''.join([
            java_file[:main_class_index],
            file_starting_from_main_class[:closing_brace_index],
            "\n" + helper_class + "\n" + "}",
            java_file[closing_brace_index + 1:]
        ])

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
    """ A proof of concept of how easy it is to add new languages.
        Will only work if python is accessible via python3 alias for now.
    """
    source_suffix = ".py"
    executable_suffix = ".pyc"
    path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.py"

    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        # Argument lists do not seem to work here
        return lambda *args, **kwargs: sh.python3(
            self.path,
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
        py_compile.compile(file=self.path, cfile=executable_path, **kwargs)
        self.path.unlink()
        self.path = executable_path

    def delete_source_file(self):
        pass
