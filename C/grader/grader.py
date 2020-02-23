import sh
from pathlib import Path
import shutil
from timer import Timer
import filecmp
from typing import List
from multiprocessing import Pool
from collections import namedtuple

# CONFIG
TIMEOUT = 1
SOURCE_FILE_NAME = "homework1.c"  # A string that has to be in each source file name
ASSIGNMENT_NAME = "Homework 1"  # For display in the output
total_possible_points = 60

# Constants
KEY = """
\nKey:
\tPASS: Your Submission is awesome
\tFailed to Compile!: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings!: Your submission uses unchecked or unsafe operations
\tCrashed: Your submission threw an uncaught exception
\tExceeded Time Limit: Your submission took longer than 60 seconds to run (probably an infinite loop)
\tWrong Answer!: Your submission produced the wrong result or generated too much output
"""


CURRENT_DIR = Path(__file__).parent.resolve()
REMOVE_MAIN = True
REMOVE_PRINTF = True


class Test:
    def __init__(self, path: Path):
        self.path = path
    
    def expected_output_path(self):
        return 


def main():
    with Timer(lambda t: print(f"It took us {t} seconds")):
        sh.cd(CURRENT_DIR)
        submissions_dir: Path = CURRENT_DIR / "submissions"
        results_dir: Path = CURRENT_DIR / "results"
        results_dir.mkdir(exist_ok=True)
        tests_dir = CURRENT_DIR / "tests/testcases"
        clean_directory(CURRENT_DIR)
        tests = gather_tests(tests_dir)
        submissions = [(s, results_dir, tests) for s in submissions_dir.iterdir() if SOURCE_FILE_NAME in str(s)]
        with Pool() as p:
            total_class_points = sum(p.map(run_tests_on_submission, submissions))
        class_average = total_class_points / (len(submissions) or 1)
        print(f"\nAverage score: {round(class_average)}/{total_possible_points}")
        clean_directory(CURRENT_DIR)


def clean_directory(directory: Path):
    for path in directory.iterdir():
        ext = path.suffix
        if ext == ".c" or ext == ".o" or ext == ".exe" or ext == ".txt":
            path.unlink()


def gather_tests(tests_dir: Path) -> List[Path]:
    tests = []
    for test in tests_dir.iterdir():
        if not test.is_file():
            continue
        shutil.copy(test, CURRENT_DIR)
        tests.append(CURRENT_DIR / test.name)
    return tests


def run_tests_on_submission(args):
    submission, results_dir, tests = args
    testcase_count = len(tests)
    student_name = submission.name[:submission.name.find("_")]
    # print(f"Grading {student_name}")
    shutil.copy(submission, CURRENT_DIR)
    with open(results_dir / submission.name, "w") as f:
        f.write(f"{ASSIGNMENT_NAME} Test Results\n\n")
        f.write("%-40s%s" % ("TestCase", "Result"))
        f.write("\n================================================================")
        try:
            sh.gcc("-c", f"{submission.name}", "-Dmain=__student_main__", "-Dprintf(...);=")
        except sh.ErrorReturnCode_1 as e:
            f.write("\nYour file failed to compile!")
            return 0
        test: Path
        pass_count = 0
        for test in tests:
            test_result = run_test(test, submission)
            test_name = test.stem.replace("_", " ").capitalize()
            f.write("\n%-40s%s" % (test_name, test_result))
            pass_count += int(test_result == "PASS")
        student_score = pass_count * total_possible_points / testcase_count
        student_final_result = f"{round(student_score)}/{total_possible_points}"
        print(f"{student_name}.", student_final_result)
        f.write("\n================================================================\n")
        f.write("Result: " + student_final_result)
        f.write(KEY)
        return student_score


def make_test_executable_path(test: Path, student_submission: Path):
    return test.with_name(test.stem + student_submission.stem + ".exe")


def run_test(test: Path,  submission: Path):
    try:
        sh.gcc("-o", make_test_executable_path(test, submission), test, submission.stem + ".o")  # In case we want to do non-background compilation
    except sh.ErrorReturnCode as e:
        return "Failed to Compile!"
    with open(submission.stem + "_output.txt", "w") as runtime_output:
        test_executable = sh.Command(make_test_executable_path(test, submission))
        try:
            test_executable(_in=test.input,_out=runtime_output, _timeout=TIMEOUT)
        except sh.TimeoutException:
            return "Exceeded Time Limit"
        except sh.ErrorReturnCode:
            return "Crashed"
    if filecmp.cmp(submission.stem + "_output.txt", (CURRENT_DIR / f"tests/output/{test.stem}.txt")):
        return "PASS"
    else:
        return "Wrong Answer!"


def compile_tests(tests: List[Path], submission: Path):
    """ An optimization to compiling that's supposed to make it faster but doesn't benefit us
        if we're already using multiprocessing. Don't forget to call .wait() on compiled tests
    """
    compiled_tests = []
    for test in tests:
        test_executable_path = make_test_executable_path(test, submission)
        compiled_tests.append(sh.gcc("-o", test_executable_path, test, submission.stem + ".o", _bg=True, _bg_exc=False))
    return compiled_tests


main()