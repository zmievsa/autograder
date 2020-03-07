# IMPORTANT: CHECKING OUTPUT AND RESULT NEED TO BE DONE SEPARATELY
# IF THE TEST CASE CHECKS OUTPUT, IT NEEDS TO RETURN THE RESULTLESS_EXIT_CODE

import sh
from pathlib import Path
import shutil
from timer import Timer
from typing import List
from multiprocessing import Pool
from io import StringIO
import os

# CONFIG
TIMEOUT = 1                             # If student's program takes more than this time in seconds -- it is terminated
ERASE_PRINTF = False                    # Gets rid of all student printf statements
ERASE_SCANF  = False                    # can't do this yet
RENAME_STUDENT_MAIN = True              # It is useful when our test case has its own main
COMPILATION_ARGUMENTS: List[str] = []   # Extra args you'd like to use during compilation
SOURCE_FILE_NAME = ".c"                 # A string that has to be in each source file name
ASSIGNMENT_NAME = "Extra credit 1"      # For display in the output
TOTAL_POINTS_POSSIBLE = 100
output_formatter = lambda s: s.isdigit()  # Filters each char in output

# Constants
TOTAL_SCORE_TO_100_RATIO = TOTAL_POINTS_POSSIBLE / 100
KEY = """
\nKey:
\tPASS: Your Submission is awesome
\tFailed to Compile: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings: Your submission uses unchecked or unsafe operations
\tCrashed: Your submission threw an uncaught exception
\tExceeded Time Limit: Your submission took longer than 60 seconds to run (probably an infinite loop)
"""
TEMP_FILE_SUFFIXES = (".c", ".o", ".exe", ".txt")
# These two cuties make it possible to give partial credit.
# Exit codes  1 - 2, 126 - 165, and 255 have special meaning and should NOT be used
# for anything besides their assigned meaning (1 is usually any exception).
# This is the reason we use exit codes [3, ..., 103] so to calculate student
# score (0 - 100), just add 3 to your calculated score.
RESULTLESS_EXIT_CODE = 0
RESULT_EXIT_CODE_SHIFT = 3  # All exit codes that convey student score are shifted by this
ALLOWED_EXIT_CODES = (RESULTLESS_EXIT_CODE, *range(0 + RESULT_EXIT_CODE_SHIFT, 101 + RESULT_EXIT_CODE_SHIFT))
MAX_RESULT = ALLOWED_EXIT_CODES[-1]
MIN_RESULT = ALLOWED_EXIT_CODES[1]
TESTCASE_COMPILATION_ARGS = (
    f"-DNO_RESULT={RESULTLESS_EXIT_CODE}",
    f"-DRESULT(x)=x+({RESULT_EXIT_CODE_SHIFT})",
    f"-DPASS={MAX_RESULT}",
    f"-DFAIL={MIN_RESULT}")


CURRENT_DIR = Path(__file__).parent.resolve()
submissions_dir: Path = CURRENT_DIR / "submissions"
results_dir: Path = CURRENT_DIR / "results"
tests_dir: Path = CURRENT_DIR / "tests"


class Test:
    def __init__(self, path: Path):
        self.path = path
        with open(tests_dir / f"output/{path.stem}.txt") as f:
            self.expected_output = format_output(f.read())
        with open(tests_dir / f"input/{path.stem}.txt") as f:
            self.input = StringIO(f.read().strip())
        
        # Only really works if test name is in snake_case
        self.name = path.stem.replace("_", " ").capitalize()
    
    def run(self, submission):
        """ Returns student score and message to be displayed """
        self.input.seek(0)
        executable_path = self.make_executable_path(submission)
        try:
            sh.gcc("-o", executable_path, self.path, submission.stem + ".o", *TESTCASE_COMPILATION_ARGS)
        except sh.ErrorReturnCode as e:
            return 0, "Failed to Compile"
        with StringIO() as runtime_output:
            test_executable = sh.Command(executable_path)
            try:
                result = test_executable(_in=self.input, _out=runtime_output, _timeout=TIMEOUT, _ok_code=ALLOWED_EXIT_CODES)
            except sh.TimeoutException:
                return 0, "Exceeded Time Limit"
            except sh.ErrorReturnCode as e:
                print(e.exit_code)
                return 0, "Crashed"
            if result.exit_code != RESULTLESS_EXIT_CODE:
                score = result.exit_code - 3   # Shift the range from 3..103 to 0..100
                return score, f"{score}/100"
            elif format_output(runtime_output.getvalue()) == self.expected_output:
                return 100, "100/100"
            else:
                return 0, "Wrong answer"
    
    def make_executable_path(self, submission: Path):
        return self.path.with_name(self.path.stem + submission.stem + ".exe")


def main():
    with Timer(lambda t: print(f"It took us {t} seconds")):
        make_compilation_arguments()
        sh.cd(CURRENT_DIR)
        results_dir.mkdir(exist_ok=True)
        tests_dir = CURRENT_DIR / "tests/testcases"
        clean_directory(CURRENT_DIR)
        
        tests = gather_tests(tests_dir)
        submissions = [(s, results_dir, tests) for s in submissions_dir.iterdir() if SOURCE_FILE_NAME in str(s)]
        os.makedirs("results", exist_ok=True)
        with Pool() as p:
            total_class_points = sum(p.map(run_tests_on_submission, submissions))
        class_average = total_class_points / (len(submissions) or 1)
        print(f"\nAverage score: {round(class_average)}/{TOTAL_POINTS_POSSIBLE}")
        clean_directory(CURRENT_DIR)
        for test in tests:
            test.input.close()


def clean_directory(directory: Path):
    for path in directory.iterdir():
        ext = path.suffix
        if any(ext == s for s in TEMP_FILE_SUFFIXES):
            path.unlink()


def gather_tests(tests_dir: Path) -> List[Test]:
    tests = []
    for test in tests_dir.iterdir():
        if not test.is_file():
            continue
        shutil.copy(test, CURRENT_DIR)
        tests.append(Test(CURRENT_DIR / test.name))
    return tests


def run_tests_on_submission(args):
    submission, results_dir, tests = args
    testcase_count = len(tests)
    student_name = submission.name[:submission.name.find("_")]
    shutil.copy(submission, CURRENT_DIR)
    with open(results_dir / submission.name, "w") as f:
        f.write(f"{ASSIGNMENT_NAME} Test Results\n\n")
        f.write("%-40s%s" % ("TestCase", "Result"))
        f.write("\n================================================================")
        try:
            sh.gcc("-c", f"{submission.name}", *COMPILATION_ARGUMENTS)
        except sh.ErrorReturnCode_1 as e:
            f.write("\nYour file failed to compile")
            return 0
        test: Path
        total_testcase_score = 0
        for test in tests:
            testcase_score, message = test.run(submission)
            f.write("\n%-40s%s" % (test.name, message))
            total_testcase_score += testcase_score
        student_score = total_testcase_score / testcase_count * TOTAL_SCORE_TO_100_RATIO
        student_final_result = f"{round(student_score)}/{TOTAL_POINTS_POSSIBLE}"
        print(f"{student_name}.", student_final_result)
        f.write("\n================================================================\n")
        f.write("Result: " + student_final_result)
        f.write(KEY)
        return student_score


def format_output(output: str):
    """ Removes whitespace and normalizes the arg """
    return "".join(filter(output_formatter, "".join(output.lower().split())))


def make_compilation_arguments():
    COMPILATION_ARGUMENTS.append("-Dscanf_s=scanf")
    if ERASE_PRINTF:
        COMPILATION_ARGUMENTS.append("-Dprintf(...);=")
    if ERASE_SCANF:
        COMPILATION_ARGUMENTS.append("-Dscanf(...);=")  # Causes an error
    if RENAME_STUDENT_MAIN:
        COMPILATION_ARGUMENTS.append("-Dmain=__student_main__")


if __name__ == "__main__":
    main()