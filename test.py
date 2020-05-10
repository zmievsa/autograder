#!/usr/bin/env python
# I should really use pytest for this...
from pathlib import Path

import autograder
from time import sleep


TEST_DIRS = {
    "simplest_c": 100,
    "c": 100,
    "c++": 100,
    "java": 100,
    "python": 100,
    "multiple_languages": 100,
    "extra_files": 100,
    "fibonacci_c": 58,
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


def run_silenced_grader(*args):
    result = autograder.__main__.main(["--no_output"] + list(args))
    return result


def main():
    for test_dir, expected_result in TEST_DIRS.items():
        try:
            real_result = int(run_silenced_grader(f"examples/{test_dir}"))
            msg = f"CHECKING TEST {test_dir} to equal {expected_result}. Real result: {real_result}"
            if int(expected_result) == real_result:
                PASS(msg)
            else:
                FAIL(msg)
        except Exception as e:
            FAIL(f"TEST {test_dir} raised '{e}')")

    test_extra_cli_args()


def test_extra_cli_args():
    testing_dir = Path("examples/extra_cli_args")
    old_config_path = testing_dir / "config.ini"
    with old_config_path.open() as f:
        old_config = f.read()
    with old_config_path.open("w") as f:
        f.write(old_config + "\nPRECOMPILE_TESTCASES = false\n")
    result = run_silenced_grader(str(testing_dir))
    s = f"CHECKING TEST extra_cli_args without args to equal 0. Real result: {int(result)}"
    if result == 0:
        PASS(s)
    else:
        FAIL(s)
    with old_config_path.open("w") as f:
        f.write(old_config)
    result = run_silenced_grader(str(testing_dir))
    s = f"CHECKING TEST extra_cli_args with args to equal 100. Real result: {int(result)}"
    if result == 100:
        PASS(s)
    else:
        FAIL(s)


if __name__ == "__main__":
    main()
