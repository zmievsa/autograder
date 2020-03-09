import os
import shutil
from io import StringIO
from multiprocessing import Pool
from pathlib import Path
from typing import List

import sh

from testcases import CTestCase, JavaTestCase, PythonTestCase
from util import CURRENT_DIR, RESULTS_DIR, SUBMISSIONS_DIR, TESTS_DIR


# CONFIG --------------------------------------------------------------
TIMEOUT = 1                     # Student's program is terminated if it takes more than this time in seconds
TOTAL_POINTS_POSSIBLE = 100     # Total points given for automatic tests
TestCaseType = CTestCase        # Specifies which language we're working with
ASSIGNMENT_NAME = "Homework"    # For display in the output
SOURCE_FILE_NAME = "Homework.c" # A string that has to be in each source file name
def FILTER_FUNCTION(s):         # Filters each char in output
    return s.isdigit()
# ---------------------------------------------------------------------

# Constants
TOTAL_SCORE_TO_100_RATIO = TOTAL_POINTS_POSSIBLE / 100
KEY = """
\nKey:
\tFailed to Compile: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings: Your submission uses unchecked or unsafe operations
\tCrashed: Your submission threw an uncaught exception
\tExceeded Time Limit: Your submission took longer than 60 seconds to run (probably an infinite loop)
"""
TEMP_FILE_SUFFIXES = (".class", ".o", ".out")


def main():
    sh.cd(CURRENT_DIR)
    RESULTS_DIR.mkdir(exist_ok=True)
    clean_directory(CURRENT_DIR)
    tests = gather_tests(TESTS_DIR)
    submissions = [(s, RESULTS_DIR, tests) for s in SUBMISSIONS_DIR.iterdir() if SOURCE_FILE_NAME in str(s)]
    os.makedirs("results", exist_ok=True)
    if TestCaseType.multiprocessing_allowed:
        with Pool() as p:
            total_class_points = sum(p.map(run_tests_on_submission, submissions))
    else:
        total_class_points = sum(map(run_tests_on_submission, submissions))
    class_average = total_class_points / (len(submissions) or 1)
    print(f"\nAverage score: {round(class_average)}/{TOTAL_POINTS_POSSIBLE}")
    clean_directory(CURRENT_DIR)
    for test in tests:
        test.cleanup()


def clean_directory(directory: Path):
    for path in directory.iterdir():
        ext = path.suffix
        if any(ext == s for s in TEMP_FILE_SUFFIXES) or SOURCE_FILE_NAME in path.name:
            path.unlink()


def gather_tests(tests_dir: Path) -> List[TestCaseType]:
    tests = []
    for test in (tests_dir / "testcases").iterdir():
        if not (test.is_file() and TestCaseType.source_suffix in test.name):
            continue
        shutil.copy(test, CURRENT_DIR)
        tests.append(TestCaseType(CURRENT_DIR / test.name, tests_dir, TIMEOUT, FILTER_FUNCTION))
    return tests


def run_tests_on_submission(args):
    submission, results_dir, tests = args
    testcase_count = len(tests)
    student_name = submission.name[:submission.name.find("_")]
    with open(results_dir / submission.name, "w") as f:
        f.write(f"{ASSIGNMENT_NAME} Test Results\n\n")
        f.write("%-40s%s" % ("TestCase", "Result"))
        f.write("\n================================================================")
        try:
            precompiled_submission = TestCaseType.precompile_submission(submission, CURRENT_DIR, SOURCE_FILE_NAME)
        except sh.ErrorReturnCode_1 as e:
            f.write("\nYour file failed to compile")
            return 0
        total_testcase_score = 0
        for test in tests:
            testcase_score, message = test.run(precompiled_submission)
            f.write("\n%-40s%s" % (test.name, message))
            total_testcase_score += testcase_score
        student_score = total_testcase_score / testcase_count * TOTAL_SCORE_TO_100_RATIO
        student_final_result = f"{round(student_score)}/{TOTAL_POINTS_POSSIBLE}"
        print(f"{student_name}.", student_final_result)
        f.write("\n================================================================\n")
        f.write("Result: " + student_final_result)
        f.write(KEY)
        return student_score


if __name__ == "__main__":
    main()
