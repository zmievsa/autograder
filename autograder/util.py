import importlib.util
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path


class AutograderError(Exception):
    """The base class for all exceptions that are raised from the incorrect use of Autograder"""


RESULT_REGEX = re.compile(r"Result: (\d+)/\d+")


def print_results(paths, min_score: int, *args, **kwargs):
    with open(paths.output_summary) as f:
        contents = f.read()
    student_outputs = contents.split("\n\n")
    for output in student_outputs:
        match = RESULT_REGEX.search(output)
        if match is not None:
            score = int(match.group(1))
            if score >= min_score:
                print(output + "\n", *args, **kwargs)


def import_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise TypeError(f"File loader for {path} was not found. Please, refer to importlib docs.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    # TODO: Loader has no attribute exec_module. What's up with that?
    spec.loader.exec_module(module)  # type: ignore
    return module


def get_file_stems(dir_: Path):
    return (p.stem for p in dir_.iterdir()) if dir_.exists() else []


def hide_path_to_directory(string_to_hide_path_from: str, path_to_hide: Path, replacement_str: str = "...") -> str:
    return string_to_hide_path_from.replace(str(path_to_hide), replacement_str)


@contextmanager
def temporarily_change_dir(new_dir):
    old_dir = Path.cwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(str(old_dir))
