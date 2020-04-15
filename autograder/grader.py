import os
import sys
import shutil
from io import StringIO
from pathlib import Path
from typing import List
import logging

import sh

from .testcases import CTestCase, JavaTestCase, PythonTestCase
from .util import get_stderr, print_results


# CONFIG --------------------------------------------------------------
TIMEOUT = 1                     # Student's program is terminated if it takes more than this time in seconds
TOTAL_POINTS_POSSIBLE = 100     # Total points given for automatic tests
TestCaseType = CTestCase        # Specifies which language we're working with
ASSIGNMENT_NAME = "Homework"    # For display in the output
SOURCE_FILE_NAME = "Homework.c".lower() # A string that has to be in each source file name
def FILTER_FUNCTION(s):         # Filters each char in output
    return s.isdigit()
# ---------------------------------------------------------------------

# Constants
TOTAL_SCORE_TO_100_RATIO = TOTAL_POINTS_POSSIBLE / 100
KEY = """
\nKey:
\tFailed to Compile: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings: Your submission uses unchecked or unsafe operations
\tCrashed due to signal SIGNAL_CODE: Your submission threw an uncaught exception.
\tAll signal error codes are described here: http://man7.org/linux/man-pages/man7/signal.7.html
\tExceeded Time Limit: Your submission took longer than 60 seconds to run (probably an infinite loop)
"""
TEMP_FILE_SUFFIXES = (".class", ".o", ".out")
logger = logging.getLogger("Grader")


def main(current_dir):
    # TODO: Add config reading from ini
    # TODO: Rewrite logging
    current_dir = current_dir.resolve()
    print(current_dir)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stdout)) # TODO: Rewrite this to use actual args
    if not "print" in [s.lower() for s in sys.argv]:
        logger.addHandler(logging.FileHandler(current_dir / "grader_output.txt", mode="w"))
    results_dir = current_dir / "results"
    results_dir.mkdir(exist_ok=True)
    temp_dir = current_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    os.chdir(temp_dir)
    tests_dir = current_dir / "tests"
    tests = gather_testcases(tests_dir, temp_dir)
    submissions = [
        (s, current_dir, results_dir, tests) for s in current_dir.iterdir() if SOURCE_FILE_NAME in str(s).lower()
    ]
    total_class_points = sum(map(run_tests_on_submission, submissions))
    class_average = total_class_points / (len(submissions) or 1)
    logger.info(f"\nAverage score: {round(class_average)}/{TOTAL_POINTS_POSSIBLE}")
    logger.info(KEY)
    shutil.rmtree(temp_dir)


def clean_directory(directory: Path):
    for path in directory.iterdir():
        ext = path.suffix
        if any(ext == s for s in TEMP_FILE_SUFFIXES) or SOURCE_FILE_NAME in path.name.lower():
            path.unlink()


def gather_testcases(tests_dir: Path, temp_dir: Path) -> List[TestCaseType]:
    tests = []
    for test in (tests_dir / "testcases").iterdir():
        if not (test.is_file() and TestCaseType.source_suffix in test.name):
            continue
        shutil.copy(test, temp_dir)
        tests.append(TestCaseType(temp_dir / test.name, tests_dir, TIMEOUT, FILTER_FUNCTION))
    return tests


def run_tests_on_submission(args):
    submission, current_dir, results_dir, tests = args
    testcase_count = len(tests)
    if "_" in submission.name:
        student_name = submission.name[:submission.name.find("_")]
    else:
        student_name = submission.name
    logger.info(f"Grading {student_name}")
    with open(results_dir / submission.name, "w") as f:
        f.write(f"{ASSIGNMENT_NAME} Test Results\n\n")
        f.write("%-40s%s" % ("TestCase", "Result"))
        f.write("\n================================================================")
        try:
            precompiled_submission = TestCaseType.precompile_submission(submission, current_dir, SOURCE_FILE_NAME)
        except sh.ErrorReturnCode_1 as e:
            stderr = get_stderr(e, "Failed to precompile")
            logger.info(stderr + f"\nResult: 0/{TOTAL_POINTS_POSSIBLE}\n")
            f.write(f"\nYour file failed to compile{stderr.replace('Failed to precompile', '')}")
            return 0
        total_testcase_score = 0
        for test in tests:
            logger.info(f"Running '{test.name}'")
            testcase_score, message = test.run(precompiled_submission)
            logger.info(message)
            f.write("\n%-40s%s" % (test.name, message))
            total_testcase_score += testcase_score
        student_score = total_testcase_score / testcase_count * TOTAL_SCORE_TO_100_RATIO
        student_final_result = f"{round(student_score)}/{TOTAL_POINTS_POSSIBLE}"
        logger.info(f"Result: {student_final_result}\n")
        f.write("\n================================================================\n")
        f.write("Result: " + student_final_result)
        f.write(KEY)
        return student_score


# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         if sys.argv[1].lower() == "clean":
#             clean_directory(CURRENT_DIR)
#         elif sys.argv[1].lower() == "print":
#             with open(CURRENT_DIR / "filtered output.txt", "w") as f:
#                 print_results(int(sys.argv[2]), file=f)
#         else:
#             raise ValueError("Unknown command line argument")
#     else:
#         main()
