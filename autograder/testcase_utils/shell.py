import asyncio
import logging
import os
import shutil
import subprocess as synchronous_subprocess
import sys
import textwrap
from asyncio import subprocess
from concurrent.futures import TimeoutError
from dataclasses import dataclass
from locale import getpreferredencoding
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

L = logging.getLogger("AUTOGRADER.testcase_utils.shell")


@dataclass
class ShellCommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass
class ShellCommand:
    """We use this class to abstract away from systemcall libraries"""

    command_name: Union[str, Path]

    async def __call__(
        self,
        *args: object,
        allowed_exit_codes: Sequence[int] = (0,),
        timeout: Optional[float] = None,
        stdin: str = "",
        **kwargs: Any,
    ) -> ShellCommandResult:
        os_specific_kwargs: Dict[str, Any] = {}
        if sys.platform == "win32":
            os_specific_kwargs["startupinfo"] = synchronous_subprocess.STARTUPINFO(
                dwFlags=synchronous_subprocess.STARTF_USESHOWWINDOW,
                wShowWindow=synchronous_subprocess.SW_HIDE,
            )
            if "env" in kwargs:
                kwargs["env"].update({"SYSTEMROOT": os.environ["SYSTEMROOT"]})
        process = await subprocess.create_subprocess_exec(
            # Linux handles non-string args well yet Windows doesn't
            str(self.command_name),
            *[str(a) for a in args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            **kwargs,
            **os_specific_kwargs,
        )
        # That's the same way subprocess.Popen(text=True) gets the encoding
        encoding = getpreferredencoding(False)
        try:
            result = await asyncio.wait_for(process.communicate(input=stdin.encode(encoding)), timeout=timeout)
        except TimeoutError as e:
            # Windows doesn't know how to clean up its processes
            if process.returncode is None and sys.platform == "win32":
                # We could probably do this asynchronously but I am too lazy to test it
                synchronous_subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    **os_specific_kwargs,
                    stdout=synchronous_subprocess.DEVNULL,
                    stderr=synchronous_subprocess.DEVNULL,
                )
            raise e
        stdout, stderr = (s.decode(encoding) for s in result)
        L.debug(
            f"""({process.returncode}) EXECUTED CMD: {self.command_name} {' '.join([str(a) for a in args])}
    STDOUT: {stdout.strip()}
    STDERR: {stderr.strip()}
        """
        )
        returncode = process.returncode if process.returncode is not None else -1
        # Possible fix for OSX sometimes not recognizing correct returncodes
        # Delete after testing if unnecessary
        if process.returncode not in allowed_exit_codes:
            raise ShellError(returncode, stderr)
        return ShellCommandResult(returncode, stdout, stderr)


EMPTY_COMMAND = ShellCommand("false")


class ShellError(Exception):
    def __init__(self, returncode: int, stderr: str):
        super().__init__(stderr)
        self.returncode = returncode
        self.stderr = stderr

    def format(self, title: str) -> str:
        return f"{title}\n{self.stderr}"


def get_shell_command(command: str) -> ShellCommand:
    """An API for commands that postpone throwing non-existence errors from creation to runtime"""
    return EMPTY_COMMAND if shutil.which(command) is None else ShellCommand(command)
