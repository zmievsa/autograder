import sh
from pathlib import Path
import shutil


# CONFIG
TIMEOUT = 10
SOURCE_FILE_NAME = "homework1.c"  # A string that has to be in each source file name
ASSIGNMENT_NAME = "Homework 1"  # For display in the output
total_possible_points = 60

# Constants
KEY = """
\nKey:
\tPASS: Your Submission is awesome
\tFailed to Compile!: Your submission did not compile due to a syntax or naming error
\tCompiled with warnings!: Your submission uses unchecked or unsafe operations
\tCrashed!: Your submission threw an uncaught exception
\tExceeded Time Limit!: Your submission took longer than 60 seconds to run (probably an infinite loop)
\tWrong Answer!: Your submission produced the wrong result or generated too much output
"""


CURRENT_DIR = Path(__file__).parent.resolve()
REMOVE_MAIN = True
REMOVE_PRINTF = True


def main():
    submissions_dir: Path = CURRENT_DIR / "submissions"
    results_dir: Path = CURRENT_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    total_class_points = 0
    student_count = 0
    # CLEANUP
    for path in CURRENT_DIR.iterdir():
        ext = path.suffix
        if ext == ".c" or ext == ".o" or ext == ".exe" or ext == ".txt":
            path.unlink()
    submission: Path #TODELETE
    for submission in submissions_dir.iterdir():
        if not SOURCE_FILE_NAME in str(submission):
            continue
        student_count += 1
        student_name = submission.name[:submission.name.find("_")]
        print(f"Grading {student_name}")
        shutil.copy(submission, CURRENT_DIR)

        with open(results_dir / submission.name, "w") as f:
            f.write(f"{ASSIGNMENT_NAME} Test Results\n\n")
            f.write("%-40s%s" % ("TestCase", "Result"))
            f.write("\n================================================================\n")
            try:
                sh.gcc("-c", f"{submission.name}", "-Dmain=__student_main__", "-Dprintf(...);=")
                test_dir = CURRENT_DIR / "tests/testcases"
            except sh.ErrorReturnCode_1:
                f.write("Your file failed to compile!")
                print("Failed to compile")
                continue
            test: Path
            pass_count = 0
            testcase_count = 0
            for test in test_dir.iterdir():
                if not test.is_file():
                    continue
                testcase_count += 1
                shutil.copy(test, CURRENT_DIR)
                test_executable = (CURRENT_DIR / test.stem).with_suffix(".exe")
                result = sh.gcc("-o", test_executable, test.name, submission.stem + ".o", _ok_code=[0, 1])
                if result.exit_code != 0:
                    f.write("Failed to Compile!")
                    continue
                with open("output.txt", "w") as runtime_output:
                    try:
                        exit_code = sh.timeout("-k", 0, 1, test_executable, _out=runtime_output).exit_code
                    except sh.ErrorReturnCode:
                        exit_code = -1  # Unknown error happened
                if exit_code == 124:
                    f.write("Exceeded Time Limit!")
                    continue
                elif exit_code != 0:
                    f.write("Crashed!")
                    continue
                try:
                    exit_code = sh.diff("output.txt", (CURRENT_DIR / f"tests/output/{test.stem}.txt")).exit_code
                except sh.ErrorReturnCode_1:
                    exit_code = 1
                if exit_code != 0:
                    f.write("Wrong Answer!")
                    continue
                else:
                    test_name = test.stem.replace("_", " ").capitalize()
                    f.write("\n%-40s%s" % (test_name, "PASS"))
                pass_count += 1
            student_score = pass_count * total_possible_points / testcase_count
            total_class_points += student_score
            student_final_result = f"{round(student_score)}/{total_possible_points}"
            print("Done.", student_final_result)
            f.write("\n================================================================\n")
            f.write("Result: " + student_final_result)
            f.write(KEY)
    class_average = total_class_points / student_count
    print(f"\nAverage score: {round(class_average)}/{total_possible_points}")

    # CLEANUP
    for path in CURRENT_DIR.iterdir():
        ext = path.suffix
        if ext == ".c" or ext == ".o" or ext == ".exe" or ext == ".txt":
            path.unlink()

main()