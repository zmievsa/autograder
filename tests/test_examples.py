import json
import sys
from pathlib import Path
from typing import Union

from autograder.__main__ import main as autograder

from . import tools


def run_test(test_dir: Union[str, Path], expected_result: int):
    with tools.silence_output() as buf:
        autograder(["run", f"examples/{test_dir}", "-j"])
        real_result = int(json.loads(buf.getvalue())["average_score"])
    assert real_result == expected_result


def test_simplest_c():
    run_test("simplest_c", 100)


def test_c():
    run_test("c", 100)


def test_cpp():
    run_test("c++", 100)


def test_java():
    run_test("java", 100)


def test_python():
    run_test("python", 50)


def test_multiple_languages():
    run_test("multiple_languages", 100)


def test_stdout_only():
    run_test("stdout_only", 100)


def test_extra_files():
    run_test("extra_files", 100)


def test_extra_cli_args():
    run_test("extra_cli_args", 100)


def test_fibonacci_c():
    run_test("fibonacci_c", 58)


def test_cheating_attempts():
    run_test("cheating_attempts", 0)
