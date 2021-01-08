import importlib.util
import re
import sys
from pathlib import Path

import sh  # type: ignore


class AutograderError(Exception):
    pass


RESULT_REGEX = re.compile(r"Result: (\d+)\/\d+")


def get_stderr(error: sh.ErrorReturnCode, string):
    error_str = str(error)
    # Remove all unrelated output
    formatted_error = string + error_str[error_str.find("STDERR:") + len("STDERR") :]
    return formatted_error


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
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    # TODO: Loader has no attribute exec_module. What's up with that?
    spec.loader.exec_module(module)  # type: ignore
    return module
