import shutil
from typing import Protocol, Any, Optional

import sh

EMPTY_COMMAND = sh.Command("false")


class ShCommand(Protocol):
    """We use this to imitate sh.Command by duck-typing it"""

    def __call__(self, *args: str, **kwargs: Any) -> Optional[sh.RunningCommand]:
        raise NotImplementedError()


def get_stderr(error: sh.ErrorReturnCode, error_title: str):
    error_str = str(error.stderr.decode("UTF-8"))
    # Remove all unrelated output
    formatted_error = f"{error_title}\n{error_str[error_str.find('STDERR:') + len('STDERR') :]}"
    return formatted_error.strip()


def Command(command: str, *args: Any, **kwargs: Any) -> sh.Command:
    """An API for commands that postpone throwing non-existence errors from creation to runtime"""
    return EMPTY_COMMAND if shutil.which(command) is None else sh.Command(command, *args, **kwargs)
