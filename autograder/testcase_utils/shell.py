import shutil
from typing import Protocol, Any, Optional

import sh

EMPTY_COMMAND = sh.Command("false")

class ShCommand(Protocol):
    """We use this to imitate sh.Command by duck-typing it"""

    def __call__(self, *args: str, **kwargs: Any) -> Optional[sh.RunningCommand]:
        raise NotImplementedError()


def get_stderr(error: sh.ErrorReturnCode, string):
    error_str = str(error)
    # Remove all unrelated output
    formatted_error = string + error_str[error_str.find("STDERR:") + len("STDERR") :]
    return formatted_error


def Command(command: str, *args: Any, **kwargs: Any) -> sh.Command:
    """An API for commands that postpone throwing non-existence errors from creation to runtime"""
    return EMPTY_COMMAND if shutil.which(command) is None else sh.Command(command, *args, **kwargs)
