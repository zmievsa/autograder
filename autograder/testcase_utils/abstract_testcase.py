import asyncio
import dataclasses
import os
import shutil
import sys
from abc import ABC, ABCMeta, abstractmethod
from asyncio import TimeoutError
from inspect import getsourcefile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

from ..config_manager import GradingConfig
from .exit_codes import SYSTEM_RESERVED_EXIT_CODES, USED_EXIT_CODES, ExitCodeEventType
from .shell import ShellCommand, ShellError
from .test_helper_formatter import get_formatted_test_helper
from .testcase_io import TestCaseIO
from .testcase_result_validator import generate_validating_string, validate_output


@dataclasses.dataclass
class TestCaseResult:
    grade: float
    message: str
    extra_output_fields: Dict[str, str] = dataclasses.field(default_factory=dict)


class SourceDirSaver(ABCMeta, type):
    """Useful in getting the resources associated with each testcase type"""

    type_source_file: Path

    def __new__(mcs, name, bases, dct):  # type: ignore
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

    config: Mapping[str, Any]

    # Note that this structure will not work for any children of this class until 3.9
    # because classmethod does not wrap property correctly until then.
    # See https://bugs.python.org/issue19072
    @classmethod
    @property
    @abstractmethod
    def helper_module(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def is_installed(cls) -> bool:
        """Returns True if software necessary to run the testcase is installed on the system"""

    @classmethod
    def get_template_dir(cls):
        return cls.type_source_file.parent / "templates"

    @abstractmethod
    async def compile_testcase(self, precompiled_submission: Path, cli_args: str) -> ShellCommand:
        """Compiles student submission and testcase into a single executable
        (or simply returns the command to run the testcase if no further compilation is necessary)

        pwd = temp/student_dir
        """

    def __init__(
        self,
        path: Path,
        timeout: float,
        weight: float,
        io: TestCaseIO,
        config: Mapping[str, Any],
        testcase_picker,
        prepend_test_helper: bool = True,
    ):
        self.test_helpers_dir = self.type_source_file.parent / "helpers"
        self.path = path
        self.timeout = timeout
        self.weight = weight
        self.max_score = int(weight * 100)

        self.name = path.name

        self.io = io
        self.validating_string = generate_validating_string()

        self.config = config
        self.testcase_picker = testcase_picker
        if prepend_test_helper:
            self.prepend_test_helper()

    @classmethod
    async def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        cli_args: str,
        config: Mapping[str, Any],
        # Lock is used to allow for optimizations during precompilation.
        # For example, when all submissions share a single library that
        # needs to be precompiled only once.
        lock: asyncio.Lock,
        testcase_picker,
    ) -> Path:
        """Copies student submission into student_dir and either precompiles
        it and returns the path to the precompiled submission or to the
        copied submission if no precompilation is necessary

        pwd = temp/student_dir
        """
        destination = (student_dir / possible_source_file_stems[0]).with_suffix(cls.source_suffix)
        shutil.copy(str(submission), str(destination))
        return destination

    async def precompile_testcase(self, cli_args: str):
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
    def is_a_type_of(cls, file: Path, possible_source_file_stems: List[str], testcase_picker) -> bool:
        return file.suffix == cls.source_suffix

    def get_path_to_helper_module(self) -> Path:
        return self.test_helpers_dir / self.helper_module

    async def run(
        self,
        precompiled_submission: Path,
        testcase_compilation_args: str,
        testcase_runtime_args: str,
    ) -> TestCaseResult:
        """Returns student score and message to be displayed"""
        shutil.copy(self.path, precompiled_submission.with_name(self.path.name))
        try:
            test_executable = await self.compile_testcase(precompiled_submission, testcase_compilation_args)
        except ShellError as e:
            return TestCaseResult(0, e.format("Failed to compile"))

        result = await self._weightless_run(precompiled_submission, test_executable, testcase_runtime_args)
        result.grade *= self.weight

        self.delete_executable_files(precompiled_submission)
        return result

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

    def get_formatted_test_helper(self, **exta_format_kwargs: str) -> str:
        return get_formatted_test_helper(self.get_path_to_helper_module(), **exta_format_kwargs)

    def delete_executable_files(self, precompiled_submission: Path):
        path = self.make_executable_path(precompiled_submission)
        # Windows sucks at deleting such files
        if path.exists() and sys.platform != "win32":
            path.unlink()

    async def _weightless_run(
        self,
        precompiled_submission: Path,
        compiled_testcase: ShellCommand,
        testcase_runtime_args: str,
    ) -> TestCaseResult:
        """Returns student score (without applying testcase weight) and message to be displayed"""
        try:
            result = await compiled_testcase(
                *testcase_runtime_args.split(),
                stdin=self.io.input,
                timeout=self.timeout,
                cwd=precompiled_submission.parent,
                env={"VALIDATING_STRING": self.validating_string, **os.environ},
                allowed_exit_codes=USED_EXIT_CODES,
            )
            exit_code = result.returncode
        except TimeoutError:
            return TestCaseResult(0, f"Exceeded time limit of {self.timeout} seconds")
        except ShellError as e:
            return TestCaseResult(0, f"Crashed due to signal {e.returncode}:\n{e.stderr}\n")
        raw_output = result.stdout
        output, score, output_is_valid = validate_output(raw_output, self.validating_string)
        extra_output_fields = {"Student Stdout": output} if self.config["CONFIG"]["GENERATE_STUDENT_OUTPUTS"] else {}

        # This  means that either the student used built-in exit function himself
        # or some testcase helper is broken, or a testcase exits itself without
        # the use of helper functions.
        if not output_is_valid:
            print(self.config["CONFIG"]["GENERATE_STUDENT_OUTPUTS"])
            return TestCaseResult(
                0,
                "None of the helper functions have been called.\n"
                f"Instead, exit() has been called with exit_code {exit_code}.\n"
                "It could indicate student cheating or testcase_utils being written incorrectly.",
            )
        elif exit_code == ExitCodeEventType.CHECK_STDOUT:
            if self.io.expected_output_equals(output):
                return TestCaseResult(100, f"{int(100 * self.weight)}/{self.max_score}", extra_output_fields)
            else:
                return TestCaseResult(0, f"0/{self.max_score} (Wrong output)", extra_output_fields)
        elif exit_code == ExitCodeEventType.RESULT:
            weighted_score = round(score * self.weight, 2)
            # We do this to make output prettier in case the student gets full points
            if weighted_score == self.max_score:
                weighted_score = round(weighted_score)
            message = f"{weighted_score}/{self.max_score}"
            if score == 0:
                message += " (Wrong answer)"
            return TestCaseResult(score, message)
        elif exit_code in SYSTEM_RESERVED_EXIT_CODES or exit_code < 0:
            # We should already handle this case in try, except block. Maybe we need more info in the error?
            raise NotImplementedError(f"System error with exit code {exit_code} has not been handled.")
        else:
            raise ValueError(f"Unknown system code {exit_code} has not been handled.")
