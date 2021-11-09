import asyncio
import itertools
import shutil
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Dict, List, Optional, Set, Tuple, Type, Union

from .config_manager import GradingConfig
from .output_summary import GradingOutputLogger, JsonGradingOutputLogger
from .testcase_utils.abstract_testcase import TestCase
from .testcase_utils.shell import ShellError
from .testcase_utils.stdout_testcase import StdoutOnlyTestCase
from .testcase_utils.submission import Submission, find_appropriate_source_file_stem
from .testcase_utils.testcase_io import TestCaseIO
from .testcase_utils.testcase_picker import TestCasePicker
from .util import AutograderError, get_file_names, hide_path_to_directory, import_from_path

EMPTY_TESTCASE_IO = TestCaseIO.get_empty_io()


# TODO: What if grader built a less complex object whose only purpose is actually grading? Should improve complexity.
class Grader:
    json_output: bool
    submissions: List[Submission]
    tests: Dict[Type[TestCase], List[TestCase]]
    raw_submissions: List[str]
    paths: "AutograderPaths"
    temp_dir: Path
    _temp_dir: TemporaryDirectory

    logger: GradingOutputLogger
    config: GradingConfig
    testcase_picker: TestCasePicker

    def __init__(self, current_dir: Path, json_output: bool = False, submissions: Optional[List[str]] = None):
        if submissions is None:
            submissions = []
        self.json_output = json_output
        self.raw_submissions = submissions
        self.stdout_formatters = {}
        self.paths = AutograderPaths(current_dir)

    def run(self):
        io_choices = {}
        try:
            self.stdout_formatters = self._import_formatters(self.paths.stdout_formatters)
            self.config = GradingConfig(self.paths.config, self.paths.default_config)
            self.testcase_picker = TestCasePicker(
                self.paths.testcase_types_dir,
                self.config.possible_source_file_stems,
                self.config.stdout_only_grading_enabled,
            )
            logger_type = JsonGradingOutputLogger if self.json_output else GradingOutputLogger
            self.logger = logger_type(
                self.paths.results_dir,
                self.config.assignment_name,
                self.config.total_points_possible,
                self.config.generate_results,
            )
            self._prepare_directory_structure()
            self.submissions = self._gather_submissions()
            io_choices = self._gather_io()
            # also copies testcase_utils to temp dir
            self.tests, unused_io_choices = self._gather_testcases(io_choices.copy())
            if self.config.stdout_only_grading_enabled:
                self.tests[StdoutOnlyTestCase] = self._generate_stdout_only_testcases(unused_io_choices)

            # Allows for consistent output
            for test_list in self.tests.values():
                test_list.sort(key=lambda t: t.path.name)

            precompilation_tasks = itertools.chain.from_iterable(
                (t.precompile_testcase(self.config.testcase_precompilation_args[t.name]) for t in t_lst)
                for t_lst in self.tests.values()
            )
            tasks = map(Runner(self, asyncio.Lock()), self.submissions)

            if sys.platform == "win32":
                loop = asyncio.ProactorEventLoop()
                asyncio.set_event_loop(loop)
            asyncio.get_event_loop().run_until_complete(asyncio.gather(*precompilation_tasks))
            modified_submissions = asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
            total_class_points = sum(s.final_grade for s in modified_submissions)
            class_average = round(total_class_points / len(self.submissions))
            self.logger.print_final_score(modified_submissions, class_average)
            self.logger.print_key()
        finally:
            for io in io_choices.values():
                io.cleanup()
            self.cleanup()
        return class_average

    def cleanup(self):
        if self.temp_dir.exists():
            # Windows doesn't know how to clean processes in time...
            if sys.platform == "win32":
                time.sleep(1)
            self._temp_dir.cleanup()

    def _prepare_directory_structure(self):
        self._temp_dir = TemporaryDirectory()
        self.temp_dir = Path(self._temp_dir.name)
        self._check_required_directories_exist()
        if self.config.generate_results:
            self.paths.results_dir.mkdir(exist_ok=True)

    def _check_required_directories_exist(self):
        for directory in self.paths.required_dirs:
            if not directory.exists():
                raise AutograderError(
                    f"{directory} directory not found. It is required for the grader to function.\n"
                    "Maybe you specified the incorrect directory? Use `autograder submission_directory_here`"
                )

    def _gather_submissions(self) -> List[Submission]:
        """Returns sorted list of paths to submissions"""
        submissions_to_grade = set(self.raw_submissions)
        submissions: List[Submission] = []
        for submission_path in self.paths.current_dir.iterdir():
            if submissions_to_grade and submission_path.name not in submissions_to_grade:
                continue

            testcase_type = self.testcase_picker.pick(submission_path)
            if testcase_type is not None:
                if (
                    self.config.any_submission_file_name_is_allowed
                    or find_appropriate_source_file_stem(submission_path, self.config.possible_source_file_stems)
                    is not None
                ):
                    submissions.append(Submission(submission_path, testcase_type, self.temp_dir))
                else:
                    pass

        if not len(submissions):
            raise AutograderError(f"No student submissions found in '{self.paths.current_dir}'.")

        # Allows consistent output
        submissions.sort(key=lambda s: s.old_path)
        return submissions

    def _gather_io(self) -> Dict[str, TestCaseIO]:
        outputs = get_file_names(self.paths.output_dir)
        inputs = get_file_names(self.paths.input_dir)
        io: Set[str] = set().union(outputs, inputs)
        io_set = {Path(i) for i in io}
        dict_io = {
            p.stem: TestCaseIO(
                p,
                self.stdout_formatters,
                self.paths.input_dir,
                self.paths.output_dir,
            )
            for p in io_set
        }
        return dict_io

    def _generate_stdout_only_testcases(self, io_choices: Dict[str, TestCaseIO]) -> List[TestCase]:
        return [
            StdoutOnlyTestCase(
                io.output_file,
                self.config.timeouts[io.name],
                self.config.testcase_weights[io.name],
                io,
                self.config,
            )
            for io in io_choices.values()
            if io.expected_output
        ]

    def _gather_testcases(
        self,
        io: Dict[str, TestCaseIO],
    ) -> Tuple[Dict[Type[TestCase], List[TestCase]], Dict[str, TestCaseIO]]:
        """Returns sorted list of testcase_types from tests/testcases"""
        if not self.paths.testcases_dir.exists():
            return {}, io
        tests: Dict[Type[TestCase], List[TestCase]]
        tests = {t: [] for t in self.testcase_picker.testcase_types}
        for test in self.paths.testcases_dir.iterdir():
            if not test.is_file():
                continue
            testcase_type = self.testcase_picker.pick(test)
            if testcase_type is None:
                continue
            shutil.copy(str(test), str(self.temp_dir))
            tests[testcase_type].append(
                testcase_type(
                    self.temp_dir / test.name,
                    self.config.timeouts[test.name],
                    self.config.testcase_weights[test.name],
                    io.pop(test.stem, EMPTY_TESTCASE_IO),
                    self.config,
                )
            )
        return tests, io

    @staticmethod
    def _import_formatters(path_to_stdout_formatters: Path) -> Dict[str, Callable[[str], str]]:
        if path_to_stdout_formatters.exists():
            module = import_from_path("stdout_formatters", path_to_stdout_formatters)
            return {k: v for k, v in module.__dict__.items() if callable(v)}
        else:
            return {}


class AutograderPaths:
    __slots__ = (
        "current_dir",
        "results_dir",
        "output_summary",
        "tests_dir",
        "testcases_dir",
        "extra_dir",
        "input_dir",
        "output_dir",
        "stdout_formatters",
        "testcase_types_dir",
        "default_stdout_formatters",
        "config",
        "default_config",
        "required_dirs",
    )
    current_dir: Path
    results_dir: Path
    output_summary: Path
    tests_dir: Path

    testcases_dir: Path
    extra_dir: Path
    input_dir: Path
    output_dir: Path
    stdout_formatters: Path
    config: Path
    required_dirs: Tuple[Path, ...]

    testcase_types_dir: Path
    default_stdout_formatters: Path
    default_config: Path

    def __init__(self, current_dir: Union[Path, str]):
        current_dir = Path(current_dir)
        self.current_dir = current_dir
        self.results_dir = current_dir / "results"
        self.output_summary = current_dir / "grader_output.txt"
        self.tests_dir = current_dir / "tests"

        self.testcases_dir = self.tests_dir / "testcases"
        self.extra_dir = self.tests_dir / "extra"
        self.input_dir = self.tests_dir / "input"
        self.output_dir = self.tests_dir / "output"

        self.stdout_formatters = self.tests_dir / "stdout_formatters.py"
        self.config = self.tests_dir / "config.toml"

        self.required_dirs = ()

        autograder_dir = Path(__file__).parent
        self.testcase_types_dir = autograder_dir / "testcase_types"
        self.default_stdout_formatters = autograder_dir / "default_stdout_formatters.py"
        self.default_config = autograder_dir / "default_config.toml"

    def generate_config(self):
        if not self.config.exists():
            if self.default_config.exists():
                shutil.copy(str(self.default_config), str(self.config))
            else:
                raise AutograderError(f"Failed to generate config:'{self.default_config}' not found.")


class Runner:
    """Grades single submissions"""

    grader: Grader
    lock: asyncio.Lock

    def __init__(self, grader: Grader, lock: asyncio.Lock):
        self.grader = grader
        self.lock = lock

    async def __call__(self, submission: Submission) -> Submission:
        await self.run_on_single_submission(submission, self.lock)
        return submission

    async def run_on_single_submission(self, submission: Submission, lock: asyncio.Lock) -> None:
        self._copy_extra_files(submission.temp_dir)
        await self._get_testcase_output(submission)
        async with lock:
            self.grader.logger.print_single_student_grading_results(submission)
        # Windows sucks at cleaning up processes early
        if not sys.platform.startswith("win32"):
            # Cleanup after running tests on student submission
            shutil.rmtree(submission.temp_dir)

    def _copy_extra_files(self, to_dir: Path) -> None:
        if self.grader.paths.extra_dir.exists():
            for path in self.grader.paths.extra_dir.iterdir():
                new_path = to_dir / path.name
                shutil.copy(str(path), str(new_path))

    # TODO: rename to "_run_testcases_on_submission" or something
    async def _get_testcase_output(self, submission: Submission):
        """Grades single submission and returns its normalized score

        Note: Has side effects in submission instance
        """
        try:
            precompiled_submission = await submission.type.precompile_submission(
                submission.old_path,
                submission.temp_dir,
                self.grader.config.possible_source_file_stems,
                self.grader.config.submission_precompilation_args[submission.old_path.name],
                self.grader.config,
            )
        except ShellError as e:
            error = hide_path_to_directory(e.format("Failed to precompile:"), submission.temp_dir)
            submission.register_precompilation_error(error)
            return 0
        allowed_tests = self.grader.tests.get(submission.type, [])
        if not allowed_tests:
            submission.register_precompilation_error("No suitable testcases found.")
            return 0
        submission.type.run_additional_testcase_operations_in_student_dir(submission.temp_dir)
        for test in allowed_tests:
            testcase_score, message = await test.run(
                precompiled_submission,
                self.grader.config.testcase_compilation_args[test.name],
                self.grader.config.testcase_runtime_args[test.name],
            )
            message = hide_path_to_directory(message, submission.temp_dir)
            submission.add_grade(test.name, testcase_score, test.weight, message)
        submission.register_final_grade(self.grader.config.total_score_to_100_ratio)
