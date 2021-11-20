#!/usr/bin/env python

# TODO: Refactor this mess
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import multiprocessing
from typing import Callable
from io import StringIO
import sys

from autograder.__main__ import main as autograder


TEST_DIRS = {
    "simplest_c": 100,
    "c": 100,
    "c++": 100,
    "java": 100,
    "python": 100,
    "multiple_languages": 100,
    "stdout_only": 100 if sys.platform != "win32" else 33,
    "extra_files": 100,
    "extra_cli_args": 100,
    "fibonacci_c": 58,
    "cheating_attempts": 0,  # All cheaters shall fail
}


@contextmanager
def silence_output():
    with StringIO() as buf, redirect_stdout(buf), redirect_stderr(buf):
        yield buf


class Bcolor:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


@contextmanager
def ErrorHandler(dir_name, cleanup_handler: Callable = lambda *a, **kw: None):
    try:
        yield
    except Exception as e:
        print(error(f"TEST {dir_name} raised '{e}')"))
    finally:
        cleanup_handler(dir_name)


def error(s: str) -> str:
    return Bcolor.FAIL + s + Bcolor.ENDC


def test_example(args):
    test_dir, expected_result = args
    with ErrorHandler(test_dir):
        with silence_output():
            real_result = int(autograder(["run", f"examples/{test_dir}"])[1])
        msg = f"CHECKING TEST {test_dir} to equal {expected_result}. Real result: {real_result}"
        if int(expected_result) == real_result:
            print(msg)
        else:
            print(error(msg))


def main():
    multiprocessing.Pool().map(test_example, [(d, r) for d, r in TEST_DIRS.items()])


if __name__ == "__main__":
    main()
