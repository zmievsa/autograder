import asyncio
import os
import shutil
import subprocess as synchronous_subprocess
import sys
from asyncio import subprocess
from concurrent.futures import TimeoutError
from dataclasses import dataclass
from locale import getpreferredencoding
from pathlib import Path
from typing import Any, Optional, Sequence, Union

# import subprocess


@dataclass
class ShellCommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
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
        if "env" in kwargs and sys.platform.startswith("win32"):
            kwargs["env"].update({"SYSTEMROOT": os.environ["SYSTEMROOT"]})

        process = await subprocess.create_subprocess_exec(
            # Linux handles non-string args well yet Windows doesn't
            str(self.command_name),
            *[str(a) for a in args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            **kwargs,
        )
        # That's the same way subprocess.Popen(text=True) gets the encoding
        encoding = getpreferredencoding(False)
        try:
            result = await asyncio.wait_for(process.communicate(input=stdin.encode(encoding)), timeout=timeout)
        except TimeoutError as e:
            # Windows doesn't know how to clean up its processes
            if sys.platform == "win32" and process.returncode is None:
                synchronous_subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)])
            raise e
        stdout, stderr = (s.decode(encoding) for s in result)
        returncode = process.returncode if process.returncode is not None else -1

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
