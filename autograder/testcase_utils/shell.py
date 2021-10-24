import os
from pathlib import Path
import shutil
import sys
from typing import Any, Union
from dataclasses import dataclass
import subprocess


@dataclass(frozen=True)
class ShellCommand:
    """We use this to imitate sh.Command by duck-typing it"""

    command_name: Union[str, Path]

    def __call__(self, *args, allowed_exit_codes=(0,), **kwargs: Any) -> subprocess.CompletedProcess:
        if "env" in kwargs and sys.platform.startswith("win32"):
            kwargs["env"].update({"SYSTEMROOT": os.environ["SYSTEMROOT"]})

        result = subprocess.run(
            # Linux handles non-string args well yet Windows doesn't
            [str(self.command_name)] + [str(a) for a in args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs,
        )
        if result.returncode not in allowed_exit_codes:
            raise ShellError(result.returncode, result.stderr)
        return result


EMPTY_COMMAND = ShellCommand("false")


class ShellError(Exception):
    def __init__(self, returncode: int, stderr: str):
        super().__init__(stderr)
        self.returncode = returncode
        self.stderr = stderr.strip()

    def format(self, title: str) -> str:
        return f"{title}\n{self.stderr}"


def get_shell_command(command: str) -> ShellCommand:
    """An API for commands that postpone throwing non-existence errors from creation to runtime"""
    return EMPTY_COMMAND if shutil.which(command) is None else ShellCommand(command)
