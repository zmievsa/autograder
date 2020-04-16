import shutil
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path

import sh

from .util import get_stderr, format_template

GRADER_DIR = Path(__file__).resolve().parent


# These two cuties make it possible to give partial credit.
# Exit codes  1 - 2, 126 - 165, and 255 have special meaning and should NOT be used
# for anything besides their assigned meaning (1 is usually any exception).
# This is the reason we use exit codes [3, ..., 103], so to calculate student
# score (0 - 100), just add 3 to your calculated score.
# IMPORTANT: CHECKING OUTPUT AND RESULT NEED TO BE DONE SEPARATELY
# IF THE TEST CASE CHECKS OUTPUT, IT NEEDS TO RETURN THE RESULTLESS_EXIT_CODE
RESULTLESS_EXIT_CODE = 0
RESULT_EXIT_CODE_SHIFT = 3  # All exit codes that convey student score are shifted by this
ALLOWED_EXIT_CODES = (RESULTLESS_EXIT_CODE, *range(0 + RESULT_EXIT_CODE_SHIFT, 101 + RESULT_EXIT_CODE_SHIFT))
MAX_RESULT = ALLOWED_EXIT_CODES[-1]
MIN_RESULT = ALLOWED_EXIT_CODES[1]


class TestCase(ABC):
    SUBMISSION_COMPILATION_ARGUMENTS: tuple = tuple()  # Extra args you'd like to use during compilation
    COMPILATION_ARGUMENTS: tuple = tuple()
    source_suffix = ".source_suffix"
    executable_suffix = ".executable_suffix"
    path_to_helper_module: Path
    def __init__(self, path: Path, tests_dir: Path, timeout: int, filters):
        self.path = path
        self.timeout = timeout
        self.filters = filters
        with open(tests_dir / f"output/{path.stem}.txt") as f:
            self.expected_output = self.format_output(f.read())
        with open(tests_dir / f"input/{path.stem}.txt") as f:
            self.input = StringIO(f.read().strip())
        
        # Only really works if test name is in snake_case
        self.name = path.stem.replace("_", " ").capitalize()
        
        self.prepend_test_helper()

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
                    _ok_code=ALLOWED_EXIT_CODES
                )
            except sh.TimeoutException:
                return 0, "Exceeded Time Limit"
            except sh.ErrorReturnCode as e:
                # http://man7.org/linux/man-pages/man7/signal.7.html
                return 0, f"Crashed due to signal {e.exit_code}"
            if result.exit_code != RESULTLESS_EXIT_CODE:
                score = result.exit_code - RESULT_EXIT_CODE_SHIFT
                return score, f"{score}/100" + (" (Wrong answer)" if score == 0 else "")
            elif self.format_output(runtime_output.getvalue()) == self.expected_output:
                return 100, "100/100"
            else:
                return 0, "0/100 (Wrong answer)"

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
        """ Copies student submission into currect_dir and either precompiles it and returns the path to
            the precompiled submission or to the copied submission if no precompilation is necesessary
        """
        destination = current_dir / "temp" / source_file_name
        shutil.copy(submission, destination)
        return destination

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
                RESULTLESS_EXIT_CODE=RESULTLESS_EXIT_CODE,
                RESULT_EXIT_CODE_SHIFT=RESULT_EXIT_CODE_SHIFT,
                MAX_RESULT=MAX_RESULT,
                MIN_RESULT=MIN_RESULT
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
        generate errors.
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
        return lambda *args, **kwargs: sh.java(self.path.stem, *args, **kwargs)


class PythonTestCase(TestCase):
    """ A proof of concept of how easy it is to add new languages
        Will only work if python is accessible via python3 alias for now
    """
    source_suffix = ".py"
    executable_suffix = source_suffix
    path_to_helper_module = GRADER_DIR / "test_helpers/test_helper.py"

    def compile_testcase(self, precompiled_submission: Path) -> sh.Command:
        return lambda *args, **kwargs: sh.python3(self.path, precompiled_submission.stem, *args, **kwargs)
