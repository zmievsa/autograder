import enum
import shutil
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
from typing import List, Tuple, Callable
from typing import Optional, Type, Dict
from inspect import getsourcefile

import sh

# TODO: Get rid of this horrible import
from autograder.util import import_from_path, AutograderError
from .shell import get_stderr, ShCommand
from .exit_codes import ExitCodeEventType, USED_EXIT_CODES, SYSTEM_RESERVED_EXIT_CODES
from .test_helper_formatter import get_formatted_test_helper
from .testcase_io import TestCaseIO
from .testcase_result_validator import generate_validating_string, validate_output

EMPTY_TESTCASE_IO = TestCaseIO.get_empty_io()


class TestCasePicker:
    testcase_types: List[Type["TestCase"]]

    def __init__(self, testcase_types_dir: Path, allowed_languages: List[str] = None):
        registered_ttypes = self._discover_testcase_types(testcase_types_dir)
        if allowed_languages is not None:
            self.testcase_types = [t for t in registered_ttypes if t.name() in allowed_languages]
        else:
            self.testcase_types = registered_ttypes
        if not self.testcase_types:
            raise AutograderError(
                "No acceptable testcase types were detected.\n"
                f"Allowed languages: {allowed_languages}\n"
                f"Registered testcase types: {registered_ttypes}"
            )

    def _discover_testcase_types(self, testcase_types_dir: Path) -> List[Type["TestCase"]]:
        testcase_types = []
        for testcase_type in testcase_types_dir.iterdir():
            for path in testcase_type.iterdir():
                if path.is_file() and path.suffix == ".py":
                    testcase = import_from_path("testcase", path).TestCase
                    if self._is_installed(testcase_type.name, testcase):
                        testcase_types.append(testcase)
        return testcase_types

    def pick(self, file: Path) -> Optional[Type["TestCase"]]:
        for testcase_type in self.testcase_types:
            if testcase_type.is_a_type_of(file):
                return testcase_type

    @staticmethod
    def _is_installed(language_name: str, testcase: Type["TestCase"]) -> bool:
        """Useful for logging"""
        if testcase.is_installed():
            return True
        else:
            print(f"Utilities for running {language_name} are not installed. Disabling it.")
            return False


# TODO: Why is this not in config?
class ArgList(enum.Enum):
    SUBMISSION_PRECOMPILATION = "SUBMISSION_PRECOMPILATION_ARGS"
    TESTCASE_PRECOMPILATION = "TESTCASE_PRECOMPILATION_ARGS"
    TESTCASE_COMPILATION = "TESTCASE_COMPILATION_ARGS"


class TestCase(ABC):
    source_suffix = ".source_suffix"  # dummy value
    executable_suffix = ".executable_suffix"  # dummy value

    test_helpers_dir: Path
    path: Path
    weight: float
    max_score: int
    name: str
    io: TestCaseIO
    testcase_picker: TestCasePicker
    validating_string: str

    # Useful in getting the resources associated with each testcase type
    _source_dir: Path

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

    @staticmethod
    def name() -> str:
        return Path().stem

    def __init__(
        self,
        path: Path,
        timeout: float,
        argument_lists: Dict[ArgList, List[str]],
        anti_cheat_enabled: bool,
        weight: float,
        io: Dict[str, TestCaseIO],
        testcase_picker: TestCasePicker,
    ):
        # We needed a way to get a source file based solely on __class__ to access its sibling directories
        self._source_dir = Path(getsourcefile(self.__class__)).parent
        self.test_helpers_dir = self._source_dir / "helpers"
        self.path = path
        self.timeout = timeout
        self.argument_lists = argument_lists
        self.anti_cheat_enabled = anti_cheat_enabled
        self.weight = weight
        self.max_score = int(weight * 100)
        self.testcase_picker = testcase_picker

        # Only really works if test name is in snake_case
        self.name = path.stem.replace("_", " ").capitalize()

        self.io = io.get(self.path.stem, EMPTY_TESTCASE_IO)
        self.validating_string = generate_validating_string()

        self.prepend_test_helper()
        if anti_cheat_enabled:
            self.precompile_testcase()

        # This is done to hide the contents of testcase_utils and exit codes to the student
        if anti_cheat_enabled:
            with self.path.open("rb") as f:
                self.source_contents = f.read()
            self.path.unlink()

    @classmethod
    def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        submission_is_allowed: Callable,  # FIXME: It's actually the SubmissionFormatChecker but Submission class depends on TestCase ABC
        arglist: List[str],
    ) -> Path:
        """Copies student submission into student_dir and either precompiles
        it and returns the path to the precompiled submission or to the
        copied submission if no precompilation is necesessary

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
    def is_a_type_of(cls, file: Path):
        return file.suffix == cls.source_suffix

    def get_path_to_helper_module(self):
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
        testcase_path = precompiled_submission.with_name(self.path.name)
        if self.anti_cheat_enabled:
            with testcase_path.open("wb") as f:
                f.write(self.source_contents)
        else:
            shutil.copy(str(self.path), str(testcase_path))

        try:
            test_executable = self.compile_testcase(precompiled_submission)
        except sh.ErrorReturnCode as e:
            return 0, get_stderr(e, "Failed to compile")
        self.delete_source_file(testcase_path)

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
