import json

from autograder.__main__ import main as autograder
from tempfile import TemporaryDirectory

from . import tools


def run_test(language: str) -> None:
    with TemporaryDirectory() as tmpdir:
        autograder(["guide", tmpdir, "-y", "-l", language])
        with tools.silence_output() as buf:
            autograder(["run", tmpdir, "-j"])
            real_result = int(json.loads(buf.getvalue())["average_score"])
    assert real_result == 100


def test_c() -> None:
    run_test("c")


def test_cpp() -> None:
    run_test("cpp")


def test_java() -> None:
    run_test("java")


def test_python() -> None:
    run_test("python")
