#!/usr/bin/env python

# TODO: Refactor this mess

from contextlib import contextmanager
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Callable

import autograder


class NonDaemonPool(Pool):
    def Process(self, *args, **kwds):
        proc = super(NonDaemonPool, self).Process(*args, **kwds)  # type: ignore

        class NonDaemonProcess(proc.__class__):
            """Monkey-patch process to ensure it is never daemonized"""

            @property
            def daemon(self):
                return False

            @daemon.setter
            def daemon(self, val):
                pass

        proc.__class__ = NonDaemonProcess
        return proc


TEST_DIRS = {
    "simplest_c": 100,
    "c": 100,
    "c++": 100,
    "java": 100,
    "python": 100,
    "multiple_languages": 100,
    "extra_files": 100,
    "fibonacci_c": 58,
    "cheating_attempts": 0,  # All cheaters shall fail
}


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
        FAIL(f"TEST {dir_name} raised '{e}')")
    finally:
        cleanup_handler(dir_name)


def PASS(message):
    print(message)


def FAIL(message):
    print(Bcolor.FAIL + message + Bcolor.ENDC)


def run_silenced_grader(*args):
    return autograder.__main__.main(["--no_output"] + list(args))


def test_example(args):
    test_dir, expected_result = args
    if expected_result == "EXTRA_CLI_ARGS":
        return test_extra_cli_args()
    with ErrorHandler(test_dir):
        real_result = int(run_silenced_grader(f"examples/{test_dir}"))
        msg = f"CHECKING TEST {test_dir} to equal {expected_result}. Real result: {real_result}"
        if int(expected_result) == real_result:
            PASS(msg)
        else:
            FAIL(msg)


def main():
    with NonDaemonPool() as pool:
        pool.map(test_example, [(d, r) for d, r in TEST_DIRS.items()] + [tuple(["", "EXTRA_CLI_ARGS"])])


def test_extra_cli_args():
    testing_dir = Path("examples/extra_cli_args/")

    with ErrorHandler(testing_dir.name):
        result = run_silenced_grader(str(testing_dir))
        s = f"CHECKING TEST {testing_dir.name} with args to equal 100. Real result: {int(result)}"
        if result == 100:
            PASS(s)
        else:
            FAIL(s)

    old_config_path = testing_dir / "tests/config.ini"
    with old_config_path.open() as f:
        old_config = f.read()
    with old_config_path.open("w") as f:
        f.write(old_config + "\nANTI_CHEAT = false\n")
    with ErrorHandler(testing_dir.name):
        result = run_silenced_grader(str(testing_dir))
        s = f"CHECKING TEST {testing_dir.name} without args to equal 0. Real result: {int(result)}"
        if result == 0:
            PASS(s)
        else:
            FAIL(s)
    with old_config_path.open("w") as f:
        f.write(old_config)


if __name__ == "__main__":
    main()
