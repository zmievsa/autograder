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


def _is_installed(language_name: str, testcase: Type[TestCase]) -> bool:
    """ Useful for logging """
    if testcase.is_installed():
        return True
    else:
        print(f"Utilities for running {language_name} are not installed. Disabling it.")
        return False


class Submission:
    __slots__ = "path", "type", "dir"

    def __init__(self, file: Path, testcase_type: Type[TestCase], temp_dir: Path):
        self.path = file
        self.type = testcase_type
        self.dir = temp_dir / file.name
        self.dir.mkdir()


def get_allowed_languages() -> Dict[str, Type[TestCase]]:
    allowed_languages = {
        "c": CTestCase,
        "java": JavaTestCase,
        "python": PythonTestCase,
        "c++": CPPTestCase,
    }
    return {k: v for k, v in allowed_languages.items() if _is_installed(k, v)}


def get_testcase_type(
    file: Path, allowed_types: Iterable[Type[TestCase]] = ALLOWED_LANGUAGES.values()
) -> Optional[Type[TestCase]]:
    for testcase_type in allowed_types:
        if testcase_type.is_a_type_of(file):
            return testcase_type


class TestCasePicker:
    def __init__(self, allowed_languages=None):
        if allowed_languages is None:
            allowed_languages = get_allowed_languages()
        self.allowed_languages = allowed_languages

    def we():
        pass