import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, List, Mapping, Optional

from autograder.testcase_utils.abstract_testcase import TestCase as AbstractTestCase
from autograder.testcase_utils.abstract_testcase import TestCaseResult
from autograder.testcase_utils.shell import EMPTY_COMMAND, ShellCommand, get_shell_command
from autograder.util import hide_path_to_directory

INCLUDE_MEMLEAK: str = '\n#include "leak_detector_c.h"\n'
MEMLEAK_DIR: Optional[TemporaryDirectory] = None
PRECOMPILED_MEMLEAK_FNAME = "memleak_detector.o"
MEMLEAK_SOURCE = Path(__file__).parent / "memleak" / "memleak_detector.c"
MEMLEAK_HEADER = Path(__file__).parent / "memleak" / "memleak_detector.h"
L = logging.getLogger("AUTOGRADER.ttypes.gcc")


class TestCase(AbstractTestCase):
    source_suffix = ".c"
    executable_suffix = ".out"
    helper_module = "test_helper.c"  # type: ignore
    compiler = get_shell_command("gcc")
    SUBMISSION_COMPILATION_ARGS: List[str] = ["-Dmain=__student_main__"]
    TESTCASE_COMPILATION_ARGS: List[str] = []
    MEMLEAK_TEMP_DIR: Optional[TemporaryDirectory] = None

    if sys.platform == "win32":
        # Windows cannot load its libraries if linking is dynamic
        TESTCASE_COMPILATION_ARGS += ["-static"]
    else:
        # Windows does not support re-declaring scanf_s even if mingw is used
        SUBMISSION_COMPILATION_ARGS += ["-Dscanf_s=scanf"]

    @classmethod
    def is_installed(cls) -> bool:
        return cls.compiler is not EMPTY_COMMAND

    @classmethod
    def get_template_dir(cls) -> Path:
        return cls.type_source_file.parent / "c_templates"

    @classmethod
    async def precompile_submission(
        cls,
        submission: Path,
        student_dir: Path,
        possible_source_file_stems: List[str],
        cli_args: str,
        config: Mapping[str, Any],
        lock: asyncio.Lock,
        *args,
        **kwargs,
    ) -> Path:
        """Compiles student submission without linking it to speed up total compilation time"""

        cli_args_lst = cli_args.split()
        if memleak_is_enabled(config):
            L.debug("Detected memleak to be enabled")
            async with lock:
                if not cls.MEMLEAK_TEMP_DIR:
                    cls.MEMLEAK_TEMP_DIR = await cls.precompile_memleak_detector(cls.TESTCASE_COMPILATION_ARGS)
                shutil.copy(Path(cls.MEMLEAK_TEMP_DIR.name) / PRECOMPILED_MEMLEAK_FNAME, student_dir)
            cli_args_lst.extend(["-include", str(MEMLEAK_HEADER)])

        copied_submission = await super().precompile_submission(
            submission, student_dir, [submission.stem], cli_args, config, lock, *args, **kwargs
        )
        precompiled_submission = copied_submission.with_suffix(".o")
        try:
            await cls.compiler(
                "-c",
                copied_submission,
                "-o",
                precompiled_submission,
                *cli_args_lst,
                *cls.SUBMISSION_COMPILATION_ARGS,
            )
        finally:
            copied_submission.unlink()
        return precompiled_submission

    async def precompile_testcase(self, cli_args: str) -> None:
        await self.compiler("-c", self.path, "-o", self.path.with_suffix(".o"), *cli_args.split())
        self.path.unlink()
        self.path = self.path.with_suffix(".o")

    async def compile_testcase(self, precompiled_submission: Path, cli_args: str) -> ShellCommand:
        executable_path = self.make_executable_path(precompiled_submission)
        path_to_self = precompiled_submission.with_name(self.path.name)
        files_to_compile = [precompiled_submission]

        # This is a hack to allow compilation of stdout-only single-file testcases
        if path_to_self != precompiled_submission:
            files_to_compile.append(path_to_self)
        if memleak_is_enabled(self.config):
            files_to_compile.append(precompiled_submission.with_name(PRECOMPILED_MEMLEAK_FNAME))
        await self.compiler(
            "-o",
            executable_path,
            *files_to_compile,
            *cli_args.split(),
            *self.TESTCASE_COMPILATION_ARGS,
        )

        return ShellCommand(executable_path)

    @classmethod
    async def precompile_memleak_detector(cls, compilation_args: List[Any]) -> TemporaryDirectory:
        memleak_temp_dir = TemporaryDirectory()
        tmp = Path(memleak_temp_dir.name)
        L.debug(f"CREATED TMP DIR FOR MEMLEAK, {memleak_temp_dir.name}")
        await cls.compiler(
            "-c",
            MEMLEAK_SOURCE,
            "-o",
            tmp / PRECOMPILED_MEMLEAK_FNAME,
            *compilation_args,
        )
        return memleak_temp_dir

    async def _weightless_run(
        self,
        precompiled_submission: Path,
        compiled_testcase: ShellCommand,
        testcase_runtime_args: str,
    ) -> TestCaseResult:
        if not memleak_is_enabled(self.config):
            return await super()._weightless_run(precompiled_submission, compiled_testcase, testcase_runtime_args)
        with TemporaryDirectory() as tmp:
            memleak_output = Path(tmp) / "memleak.txt"
            L.debug(f"Created memleak output file {memleak_output}")
            compiled_testcase = add_env_vars(compiled_testcase, MEMLEAK_FILE=str(memleak_output))
            result = await super()._weightless_run(precompiled_submission, compiled_testcase, testcase_runtime_args)
            memleak_output_text = memleak_output.read_text() if memleak_output.is_file() else ""
            memleak_output_text = hide_path_to_directory(memleak_output_text, precompiled_submission.parent)
        if memleak_output_text:
            result.extra_output_fields["Memory Leak Summary"] = memleak_output_text
        return result


def add_env_vars(command: ShellCommand, **env: str) -> ShellCommand:
    async def inner(*args: Any, **kwargs: Any):
        if not "env" in kwargs:
            kwargs["env"] = {}
        kwargs["env"].update(env)
        return await command(*args, **kwargs)

    return inner  # type: ignore


def memleak_is_enabled(config: Mapping) -> bool:
    return config.get("GCC", {}).get("MEMORY_LEAK_DETECTION", False)
