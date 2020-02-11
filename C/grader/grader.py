# TODO Refactor
# TODO Fix formatting
# TODO Speed up

import sh
from pathlib import Path
import shutil
from timer import Timer
import filecmp
from typing import List


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


def main():
    submissions_dir: Path = CURRENT_DIR / "submissions"
    results_dir: Path = CURRENT_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    tests_dir = CURRENT_DIR / "tests/testcases"
    total_class_points = 0
    student_count = 0
    clean_directory(CURRENT_DIR)
    tests = gather_tests(tests_dir)
    for submission in submissions_dir.iterdir():
        if not SOURCE_FILE_NAME in str(submission):
            continue
        student_count += 1
        total_class_points += run_tests_on_submission(submission, results_dir, tests)
    class_average = total_class_points / student_count
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


def run_tests_on_submission(submission: Path, results_dir: Path, tests: List[Path]):
    testcase_count = len(tests)
    student_name = submission.name[:submission.name.find("_")]
    print(f"Grading {student_name}")
    shutil.copy(submission, CURRENT_DIR)
    with open(results_dir / submission.name, "w") as f:
        f.write(f"{ASSIGNMENT_NAME} Test Results\n\n")
        f.write("%-40s%s" % ("TestCase", "Result"))
        f.write("\n================================================================")
        try:
            sh.gcc("-c", f"{submission.name}", "-Dmain=__student_main__", "-Dprintf(...);=")
        except sh.ErrorReturnCode_1 as e:
            f.write("\nYour file failed to compile!")
            print("Failed to compile")
            return 0
        test: Path
        pass_count = 0
        compiled_tests = compile_tests(tests, submission)
        for test, compiled_test in zip(tests, compiled_tests):
            test_result = run_test(test, compiled_test, submission)
            test_name = test.stem.replace("_", " ").capitalize()
            f.write("\n%-40s%s" % (test_name, test_result))
            pass_count += int(test_result == "PASS")
        student_score = pass_count * total_possible_points / testcase_count
        student_final_result = f"{round(student_score)}/{total_possible_points}"
        print("Done.", student_final_result)
        f.write("\n================================================================\n")
        f.write("Result: " + student_final_result)
        f.write(KEY)
        return student_score

def compile_tests(tests: List[Path], submission: Path):
    compiled_tests = []
    for test in tests:
        test_executable_path = make_test_executable_path(test, submission)
        compiled_tests.append(sh.gcc("-o", test_executable_path, test, submission.stem + ".o", _bg=True, _bg_exc=False))
    return compiled_tests


def make_test_executable_path(test: Path, student_submission: Path):
    return test.with_name(test.stem + student_submission.stem + ".exe")



def run_test(test: Path, compiled_test: sh.RunningCommand, submission: Path):
    try:
        result = compiled_test.wait()
    except sh.ErrorReturnCode as e:
        return "Failed to Compile!"
    with open(submission.stem + "_output.txt", "w") as runtime_output:
        test_executable = sh.Command(make_test_executable_path(test, submission))
        try:
            test_executable(_out=runtime_output, _timeout=TIMEOUT)
        except sh.TimeoutException:
            return "Exceeded Time Limit"
        except sh.ErrorReturnCode:
            return "Crashed"
    if filecmp.cmp(submission.stem + "_output.txt", (CURRENT_DIR / f"tests/output/{test.stem}.txt")):
        return "PASS"
    else:
        return "Wrong Answer!"



main()