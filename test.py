#!/usr/bin/env python

import autograder


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


def main():
    for test_dir, expected_result in TEST_DIRS.items():
        try:
            real_result = autograder.__main__.main([f"examples/{test_dir}", "--no_output"])
            msg = f"CHECKING TEST {test_dir} to equal {expected_result}. Real result: {real_result}"
            if expected_result == real_result:
                PASS(msg)
            else:
                FAIL(msg)
        except Exception as e:
            FAIL(f"TEST {test_dir} raised '{e}')")


if __name__ == "__main__":
    main()
