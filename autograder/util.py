import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable


class AutograderError(Exception):
    """The base class for all exceptions that are raised from the incorrect use of Autograder"""


def import_from_path(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not (spec and spec.loader):
        raise TypeError(f"File loader for {path} was not found. Please, refer to importlib docs.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    # exec_module is not always available which is why a linter won't be able to find it.
    # Docs do not state specific conditions for when it is available so if it's not, we
    # are okay with raising an ImportError.
    spec.loader.exec_module(module)
    return module


def get_file_names(dir_: Path) -> Iterable[str]:
    return (p.name for p in dir_.iterdir()) if dir_.exists() else ()


def hide_path_to_directory(string_to_hide_path_from: str, path_to_hide: Path, replacement: str = "...") -> str:
    """To prevent students from knowing the structure of instructor's directories, we remove the middle
    part of the path to student's file from output.

    Sometimes compilers output a longer/shorter path. For example, gcc through wsl will not start paths
    with "mnt/" while python will so we cut out the beginning and end of the path to hide the more important
    middle part of it.

    The length check is done to prevent indexing exceptions or corruption of output
    in case the path to remove is too short. For example,
    >>> "Hello. World.".replace(str(Path(".")), "...") == "Hello... World..."
    >>> "abc".replace("", "...") == ...a...b...c...
    """
    formatted_string = string_to_hide_path_from.replace(str(path_to_hide), replacement)
    if len(path_to_hide.parts) > 2:
        shorter_path_to_hide = Path("/".join(path_to_hide.parts[2:]))
        formatted_string = formatted_string.replace(str(shorter_path_to_hide), replacement)
    return formatted_string
