import sys
from pathlib import Path
from typing import List
from autograder.config_manager import GradingConfig

from autograder.testcase_utils.abstract_testcase import ShellCommand
from autograder.testcase_utils.abstract_testcase import TestCase as AbstractTestCase
from autograder.testcase_utils.shell import EMPTY_COMMAND, get_shell_command

INCLUDE_MEMLEAK: str = '\n#include "leak_detector_c.h"\n'


class TestCase(AbstractTestCase):
    source_suffix = ".c"
    executable_suffix = ".out"
    helper_module = "test_helper.c"  # type: ignore
    compiler = get_shell_command("gcc")
    SUBMISSION_COMPILATION_ARGS: List[str] = ["-Dmain=__student_main__"]
    TESTCASE_COMPILATION_ARGS: List[str] = []
    if sys.platform.startswith("win32"):
        # Windows cannot load its libraries if linking is dynamic
        TESTCASE_COMPILATION_ARGS += ["-static"]
    else:
        # Windows does not support re-declaring scanf_s even if mingw is used
        SUBMISSION_COMPILATION_ARGS += ["-Dscanf_s=scanf"]

    @classmethod
    def is_installed(cls) -> bool:
        return cls.compiler is not EMPTY_COMMAND

    @classmethod
    def get_template_dir(cls):
        return cls.type_source_file.parent / "c_templates"

    @classmethod
    async def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        cli_args: str,
        config: GradingConfig,
    ) -> Path:
        """Compiles student submission without linking it.
        It is done to speed up total compilation time
        """
        copied_submission = await super().precompile_submission(
            submission,
            student_dir,
            [submission.stem],
            cli_args,
            config,
        )
        precompiled_submission = copied_submission.with_suffix(".o")

        # TODO: Append INCLUDE_MEMLEAK to submission here
        # copied_submission.write_text(copied_submission.read_text())
        try:
            await cls.compiler(
                "-c",
                f"{copied_submission}",
                "-o",
                precompiled_submission,
                *cli_args.split(),
                *cls.SUBMISSION_COMPILATION_ARGS,
            )
        finally:
            copied_submission.unlink()
        return precompiled_submission

    async def precompile_testcase(self, cli_args: str):
        await self.compiler(
            "-c",
            self.path,
            "-o",
            self.path.with_suffix(".o"),
            *cli_args.split(),
        )
        self.path.unlink()
        self.path = self.path.with_suffix(".o")

    async def compile_testcase(self, precompiled_submission: Path, cli_args: str) -> ShellCommand:
        executable_path = self.make_executable_path(precompiled_submission)
        files_to_compile = [
            precompiled_submission.with_name(self.path.name),
            precompiled_submission,
        ]
        # if self.config.file["GCC"].getboolean("MEMORY_LEAK_DETECTION"):
        #     files_to_compile.append(precompiled_submission.with_name("memleak_detector.c"))
        await self.compiler(
            "-o",
            executable_path,
            *files_to_compile,
            *cli_args.split(),
            *self.TESTCASE_COMPILATION_ARGS,
        )
        return ShellCommand(executable_path)

    @property
    def memleak_detector_source_file(self) -> Path:
        return self.type_source_file.parent / "memleak_detector" / "memleak_detector.c"

    @property
    def memleak_detector_header_file(self) -> Path:
        return self.type_source_file.parent / "memleak_detector" / "memleak_detector.h"
