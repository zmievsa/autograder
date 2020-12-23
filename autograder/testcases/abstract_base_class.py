import enum
import shutil
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import sh
from typing_extensions import Protocol

# TODO: I hate these imports. We should only use relative imports because these imports indicate architectural problems.
from autograder.util import format_template, get_stderr

from .util.exit_codes import USED_EXIT_CODES, ExitCodeEventType, ExitCodeHandler
from .util.testcase_result_validator import generate_validating_string, validate_output

TEST_HELPERS_DIR = Path(__file__).resolve().parent / "test_helpers"


class ShCommand(Protocol):
    """ We use this to imitate sh.Command by ducktyping it """

    def __call__(self, *args: str, **kwargs: Any) -> Optional[sh.RunningCommand]:
        raise NotImplementedError()


class ArgList(enum.Enum):
    SUBMISSION_PRECOMPILATION = "SUBMISSION_PRECOMPILATION_ARGS"
    TESTCASE_PRECOMPILATION = "TESTCASE_PRECOMPILATION_ARGS"
    TESTCASE_COMPILATION = "TESTCASE_COMPILATION_ARGS"


class TestCase(ABC):
    source_suffix = ".source_suffix"  # dummy value
    executable_suffix = ".executable_suffix"  # dummy value
    exit_code_handler: ExitCodeHandler = ExitCodeHandler()
    path: Path
    source_file_name: Path
    weight: float
    per_char_formatting_enabled: bool
    full_output_formatting_enabled: bool

    @property
    @abstractmethod
    def helper_module_name(self) -> str:
        pass

    @abstractmethod
    def compile_testcase(self, precompiled_submission: Path) -> ShCommand:
        """Compiles student submission and testcase into a single executable
        (or simply returns the command to run the testcase if no further compilation is necessary)

        pwd = temp/student_dir
        """

    def __init__(
        self,
        path: Path,
        source_file_name: str,
        input_dir: Path,
        output_dir: Path,
        timeout: float,
        formatters: Dict[str, Callable[[str], str]],
        argument_lists: Dict[ArgList, List[str]],
        anti_cheat_enabled: bool,
        weight: float,
        per_char_formatting_enabled: bool,
        full_output_formatting_enabled: bool,
    ):
        self.path = path
        self.source_file_name = Path(source_file_name)
        self.timeout = timeout
        self.formatters = formatters
        self.argument_lists = argument_lists
        self.anti_cheat_enabled = anti_cheat_enabled
        self.weight = weight
        self.max_score = int(weight * 100)
        output_file = output_dir / f"{path.stem}.txt"
        self.per_char_formatting_enabled = per_char_formatting_enabled
        self.full_output_formatting_enabled = full_output_formatting_enabled

        # Only really works if test name is in snake_case
        self.name = path.stem.replace("_", " ").capitalize()

        if output_file.exists():
            with output_file.open() as f:
                self.expected_output = self.__format_output(f.read())
        else:
            self.expected_output = StringIO("")
        input_file = input_dir / f"{path.stem}.txt"
        if input_file.exists():
            with input_file.open() as f:
                self.input = StringIO(f.read().strip())
        else:
            self.input = StringIO("")

        self.validating_string = generate_validating_string()

        self.prepend_test_helper()
        # with self.path.open() as f:
        #     print(f.read())
        if anti_cheat_enabled:
            self.precompile_testcase()

        # This is done to hide the contents of testcases and exit codes to the student
        if anti_cheat_enabled:
            with self.path.open("rb") as f:
                self.source_contents = f.read()
            self.path.unlink()

    @classmethod
    def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        source_file_name: str,
        arglist: List[str],
    ) -> Path:
        """Copies student submission into student_dir and either precompiles
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

    @classmethod
    def run_additional_testcase_operations_in_student_dir(cls, student_dir: Path):
        pass

    def get_path_to_helper_module(self):
        return TEST_HELPERS_DIR / self.helper_module_name

    def run(self, precompiled_submission: Path) -> Tuple[float, str]:
        """ Returns student score and message to be displayed """
        result, message = self.__weightless_run(precompiled_submission)

        self.delete_executable_files(precompiled_submission)
        return result * self.weight, message

    def make_executable_path(self, submission: Path) -> Path:
        """ By combining test name and student name, it makes a unique path """
        return submission.with_name(self.path.stem + submission.stem + self.executable_suffix)

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
        with self.get_path_to_helper_module().open() as helper_file:
            return format_template(helper_file.read(), **self.exit_code_handler.get_formatted_exit_codes())

    def delete_executable_files(self, precompiled_submission: Path):
        path = self.make_executable_path(precompiled_submission)
        if path.exists():
            path.unlink()

    def delete_source_file(self, source_path: Path):
        if source_path.exists():
            source_path.unlink()

    def __weightless_run(self, precompiled_submission: Path):
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
                result = test_executable(
                    _in=self.input,
                    _out=runtime_output,
                    _timeout=self.timeout,
                    _ok_code=USED_EXIT_CODES,
                    _env={"VALIDATING_STRING": self.validating_string},
                )
                if result is None:
                    raise NotImplementedError()
            except sh.TimeoutException:
                return 0, "Exceeded Time Limit"
            except sh.ErrorReturnCode as e:
                # http://man7.org/linux/man-pages/man7/signal.7.html
                return 0, f"Crashed due to signal {e.exit_code}:\n{e.stderr.decode('UTF-8', 'replace')}\n"
            raw_output = runtime_output.getvalue()
            # print(raw_output)
            output, output_is_valid = validate_output(raw_output, self.validating_string)
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
                if self.__format_output(output) == self.expected_output:
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

    def __format_output(self, output: str) -> str:
        if self.full_output_formatting_enabled:
            output = self.formatters["full_output_formatter"](output)
        if self.per_char_formatting_enabled:
            output = "".join(self.formatters["per_char_formatter"](c) for c in output)
        return output
