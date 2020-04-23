import shutil
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
import py_compile

import sh  # type: ignore

from .util import get_stderr, format_template, generate_random_string
from .exit_codes import ExitCodeEventType, ExitCodeHandler

GRADER_DIR = Path(__file__).resolve().parent


class TestCase(ABC):
    # Extra args you'd like to use during compilation
    SUBMISSION_COMPILATION_ARGUMENTS: tuple = tuple()
    COMPILATION_ARGUMENTS: tuple = tuple()
    source_suffix = ".source_suffix"
    executable_suffix = ".executable_suffix"
    path_to_helper_module: Path
    exit_code_handler: ExitCodeHandler = ExitCodeHandler()

    def __init__(
        self,
        path: Path,
        tests_dir: Path,
        timeout: int,
        filters,
        precompile_testcase=False
    ):
        self.path = path
        self.timeout = timeout
        self.filters = filters
        self.need_precompile_testcase = precompile_testcase
        output_dir = tests_dir / f"output/{path.stem}.txt"
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

    def run(self, precompiled_submission: Path):
        """ Returns student score and message to be displayed """
        self.input.seek(0)
        try:
            test_executable = self.compile_testcase(precompiled_submission)
        except sh.ErrorReturnCode as e:
            return 0, get_stderr(self.path.parent, e, "Failed to compile")
        with StringIO() as runtime_output:
            try:
                result = test_executable(
                    _in=self.input,
                    _out=runtime_output,
                    _timeout=self.timeout,
                    _ok_code=self.exit_code_handler.allowed_exit_codes
                )
            except sh.TimeoutException:
                return 0, "Exceeded Time Limit"
            except sh.ErrorReturnCode as e:
                # http://man7.org/linux/man-pages/man7/signal.7.html
                return 0, f"Crashed due to signal {e.exit_code}"
            event = self.exit_code_handler.scan(result.exit_code)
            if event.type == ExitCodeEventType.CHECK_OUTPUT:
                if self.format_output(runtime_output.getvalue()) == self.expected_output:
                    return 100, "100/100"
                else:
                    return 0, "0/100 (Wrong answer)"
            elif event.type == ExitCodeEventType.RESULT:
                score = event.value
                message = f"{score}/100"
                if score == 0:
                    message += " (Wrong answer)"
                return score, message
            elif event.type == ExitCodeEventType.CHEAT_ATTEMPT:
                # This  means that either the student used built-in exit function himself
                # or some testcase helper is broken, or a testcase exits itself without
                # the use of helper functions.
                return 0, f"An invalid exit code '{result.exit_code}' has been supplied"
            elif event.type == ExitCodeEventType.SYSTEM_ERROR:
                # We should already handle this case in try, except block
                pass

    def make_executable_path(self, submission: Path):
        """ By combining test name and student name, it makes a unique path """
        return self.path.with_name(self.path.stem + submission.stem + self.executable_suffix)

    def format_output(self, output: str):
        output = output.lower()
        for filter_function in self.filters:
            output = "".join(filter(filter_function, output))
        return output

    @classmethod
    def precompile_submission(cls, submission: Path, current_dir: Path, source_file_name) -> Path:
        """ Copies student submission into currect_dir and either precompiles
            it and returns the path to the precompiled submission or to the
            copied submission if no precompilation is necesessary
        """
        destination = current_dir / "temp" / source_file_name
        shutil.copy(submission, destination)
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
        with open(self.path) as f, open(self.path_to_helper_module) as helper_file:
            formatted_helper_file = format_template(
                helper_file.read(),
                **self.exit_code_handler.get_formatted_exit_codes()
            )
            content = f.read()
            final_content = formatted_helper_file + "\n" + content
        with open(self.path, "w") as f:
            f.write(final_content)

    def cleanup(self):
        self.input.close()
        self.path.unlink()


class CTestCase(TestCase):
    source_suffix = ".c"
    executable_suffix = ".out"
    path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.c"
    SUBMISSION_COMPILATION_ARGS = ("-Dscanf_s=scanf", "-Dmain=__student_main__")

    @classmethod
    def precompile_submission(cls, submission, current_dir, source_file_name):
        """ Links student submission without compiling it.
            It is done to speed up total compilation time
        """
        copied_submission = super().precompile_submission(submission, current_dir, submission.name)
        precompiled_submission = copied_submission.with_suffix(".o")
        sh.gcc(
            "-c", f"{copied_submission}",
            "-o", precompiled_submission,
            *cls.SUBMISSION_COMPILATION_ARGS
        )
        return precompiled_submission

    def precompile_testcase(self):
        sh.gcc(
            "-c", self.path,
            "-o", self.path.with_suffix('.o')
        )
        self.path.unlink()
        self.path = self.path.with_suffix('.o')

    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        executable_path = self.make_executable_path(precompiled_submission)
        sh.gcc(
            "-o",
            executable_path,
            self.path,
            precompiled_submission.name
        )
        return sh.Command(executable_path)


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

    def precompile_testcase(self):
        """ Sadly, java doesn't allow to compile files before their dependencies
            have compiled.
            Instead, we hide test names. It is not super safe but better than nothing.
            We could, instead, encrypt each test file and decrypt at compilation.
        """
        self.original_path = self.path
        new_name = generate_random_string(15)
        new_path = self.path.with_name(new_name)
        self.path.rename(new_path)
        self.path = self.path.with_name(new_name)

        # This method didn't work but might prove useful in the future
        # sh.javac(self.path, "-implicit:none")
        # self.path.unlink()

    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        if self.need_precompile_testcase:
            self.path.rename(self.original_path)
            path = self.original_path
        else:
            path = self.path
        sh.javac(path, precompiled_submission.name)
        if self.need_precompile_testcase:
            path.rename(self.path)
        return lambda *args, **kwargs: sh.java(path.stem, *args, **kwargs)

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
            raise ValueError(f"Braces in testcase '{self.name}' don't match.")


class PythonTestCase(TestCase):
    """ A proof of concept of how easy it is to add new languages.
        Will only work if python is accessible via python3 alias for now.
    """
    source_suffix = ".py"
    executable_suffix = source_suffix
    path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.py"

    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        return lambda *args, **kwargs: sh.python3(
            self.path,
            precompiled_submission.stem,
            *args,
            **kwargs
        )

    def precompile_testcase(self):
        py_compile.compile(file=self.path, cfile=self.path)
