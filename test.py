#!/usr/bin/env python

import autograder
from time import sleep
import sys
import io


TEST_DIRS = {
    "simplest_c": 100,
    "c": 100,
    "java": 100,
    "python": 100
}


class Bcolor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def PASS(message):
    print(message)


def FAIL(message):
    print(Bcolor.FAIL + message + Bcolor.ENDC)


def run_silenced_grader(*args, **kwargs):
    save_stdout = sys.stdout
    sys.stdout = io.StringIO()
    result = autograder.__main__.main(*args, **kwargs)
    sys.stdout = save_stdout
    return result


def main():
    for test_dir, expected_result in TEST_DIRS.items():
        try:
            real_result = run_silenced_grader([f"examples/{test_dir}", "--no_output"])
            msg = f"CHECKING TEST {test_dir} to equal {expected_result}. Real result: {real_result}"
            if expected_result == real_result:
                PASS(msg)
            else:
                FAIL(msg)
        except Exception as e:
            FAIL(f"TEST {test_dir} raised '{e}')")

    test_extra_cli_args()


def test_extra_cli_args():
    result = run_silenced_grader(["examples/extra_cli_args"])
    s = f"Test extra_cli_args without args returned {result} total score"
    if result == 0:
        PASS(s)
    else:
        FAIL(s)
    sleep(1)  # To prevent two calls executing in parallel
    result = run_silenced_grader(["examples/extra_cli_args", "--precompile_testcases"])
    s = f"Test extra_cli_args with args returned {result} total score"
    if result == 100:
        PASS(s)
    else:
        FAIL(s)


if __name__ == "__main__":
    main()
