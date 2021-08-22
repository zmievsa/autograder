import enum
import shutil
from abc import ABC, abstractmethod, ABCMeta
from inspect import getsourcefile
from io import StringIO
from pathlib import Path
from typing import Dict
from typing import List, Tuple

import sh

from .exit_codes import ExitCodeEventType, USED_EXIT_CODES, SYSTEM_RESERVED_EXIT_CODES
from .shell import get_stderr, ShCommand
from .test_helper_formatter import get_formatted_test_helper
from .testcase_io import TestCaseIO
from .testcase_result_validator import generate_validating_string, validate_output


# TODO: Why is this not in config?
class ArgList(enum.Enum):
    SUBMISSION_PRECOMPILATION = "SUBMISSION_PRECOMPILATION_ARGS"
    TESTCASE_PRECOMPILATION = "TESTCASE_PRECOMPILATION_ARGS"
    TESTCASE_COMPILATION = "TESTCASE_COMPILATION_ARGS"


class SourceDirSaver(ABCMeta, type):
    """Useful in getting the resources associated with each testcase type"""

    type_source_file: Path

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        # We needed a way to get a source file based solely on __class__ to access its sibling directories
        source_file = getsourcefile(cls)
        if source_file is None:
            raise FileNotFoundError(f"Source file for class {cls} has not been found.")
        cls.type_source_file = Path(source_file)
        return cls


class TestCase(ABC, metaclass=SourceDirSaver):
    source_suffix = ".source_suffix"  # dummy value
    executable_suffix = ".executable_suffix"  # dummy value

    type_source_file: Path
    test_helpers_dir: Path
    path: Path
    weight: float
    max_score: int
    io: TestCaseIO
    validating_string: str

    @property
    @abstractmethod
    def helper_module(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def is_installed(cls) -> bool:
        """Returns True if software necessary to run the testcase is installed on the system"""

    @abstractmethod
    def compile_testcase(self, precompiled_submission: Path) -> ShCommand:
        """Compiles student submission and testcase into a single executable
        (or simply returns the command to run the testcase if no further compilation is necessary)

        pwd = temp/student_dir
        """

    @classmethod
    def get_template_dir(cls):
        return cls.type_source_file.parent / "templates"

    def __init__(
        self,
        path: Path,
        timeout: float,
        argument_lists: Dict[ArgList, List[str]],
        weight: float,
        io: TestCaseIO,
    ):
        self.test_helpers_dir = self.type_source_file.parent / "helpers"
        self.path = path
        self.timeout = timeout
        self.argument_lists = argument_lists
        self.weight = weight
        self.max_score = int(weight * 100)

        # Only really works if test name is in snake_case
        self.name = path.stem.replace("_", " ").capitalize()

        self.io = io
        self.validating_string = generate_validating_string()

        self.prepend_test_helper()
        self.precompile_testcase()

    @classmethod
    def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        arglist: List[str],
    ) -> Path:
        """Copies student submission into student_dir and either precompiles
        it and returns the path to the precompiled submission or to the
        copied submission if no precompilation is necessary

        pwd = temp/student_dir
        """
        destination = (student_dir / possible_source_file_stems[0]).with_suffix(cls.source_suffix)
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
        """Do nothing by default"""
        pass

    @classmethod
    def is_a_type_of(cls, file: Path, possible_source_file_stems: List[str]) -> bool:
        return file.suffix == cls.source_suffix

    def get_path_to_helper_module(self) -> Path:
        return self.test_helpers_dir / self.helper_module

    def run(self, precompiled_submission: Path) -> Tuple[float, str]:
        """Returns student score and message to be displayed"""
        result, message = self._weightless_run(precompiled_submission)

        self.delete_executable_files(precompiled_submission)
        return result * self.weight, message

    def make_executable_path(self, submission: Path) -> Path:
        """By combining test name and student name, it makes a unique path"""
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
        return get_formatted_test_helper(self.get_path_to_helper_module())

    def delete_executable_files(self, precompiled_submission: Path):
        path = self.make_executable_path(precompiled_submission)
        if path.exists():
            path.unlink()

    def delete_source_file(self, source_path: Path):
        if source_path.exists():
            source_path.unlink()

    def _weightless_run(self, precompiled_submission: Path) -> Tuple[float, str]:
        """Returns student score (without applying testcase weight) and message to be displayed"""
        testcase_copy_in_student_dir = precompiled_submission.with_name(self.path.name)
        shutil.copy(str(self.path), str(testcase_copy_in_student_dir))

        try:
            test_executable = self.compile_testcase(precompiled_submission)
        except sh.ErrorReturnCode as e:
            return 0, get_stderr(e, "Failed to compile")
        self.delete_source_file(testcase_copy_in_student_dir)

        with StringIO() as runtime_output, self.io.input() as runtime_input:
            try:
                result = test_executable(
                    _in=runtime_input,
                    _out=runtime_output,
                    _timeout=self.timeout,
                    _ok_code=USED_EXIT_CODES,
                    _env={"VALIDATING_STRING": self.validating_string},
                )
                if result is None:
                    raise NotImplementedError()
                exit_code = result.exit_code
            except sh.TimeoutException:
                return 0, "Exceeded Time Limit"
            except sh.ErrorReturnCode as e:
                return (
                    0,
                    f"Crashed due to signal {e.exit_code}:\n{e.stderr.decode('UTF-8', 'replace')}\n",
                )
            raw_output = runtime_output.getvalue()
            output, score, output_is_valid = validate_output(raw_output, self.validating_string)
            if not output_is_valid:
                # This  means that either the student used built-in exit function himself
                # or some testcase helper is broken, or a testcase exits itself without
                # the use of helper functions.
                return (
                    0,
                    "None of the helper functions have been called.\n"
                    f"Instead, exit() has been called with exit_code {exit_code}.\n"
                    "It could indicate student cheating or testcase_utils being written incorrectly.",
                )
            elif exit_code == ExitCodeEventType.CHECK_STDOUT:
                if self.io.expected_output_equals(output):
                    return 100, f"{int(100 * self.weight)}/{self.max_score}"
                else:
                    return 0, f"0/{self.max_score} (Wrong output)"
            elif exit_code == ExitCodeEventType.RESULT:
                message = f"{round(score * self.weight, 2)}/{self.max_score}"
                if score == 0:
                    message += " (Wrong answer)"
                return score, message
            elif exit_code in SYSTEM_RESERVED_EXIT_CODES or exit_code < 0:
                # We should already handle this case in try, except block. Maybe we need more info in the error?
                raise NotImplementedError(f"System error with exit code {exit_code} has not been handled.")
            else:
                raise ValueError(f"Unknown system code {exit_code} has not been handled.")
