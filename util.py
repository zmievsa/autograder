from pathlib import Path
import logging
import sys
import re
import sh


CURRENT_DIR = Path(__file__).parent.resolve()
SUBMISSIONS_DIR: Path = CURRENT_DIR / "submissions"
RESULTS_DIR: Path = CURRENT_DIR / "results"
TESTS_DIR: Path = CURRENT_DIR / "tests"


logger = logging.getLogger("Grader")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))
if not "print" in [s.lower() for s in sys.argv]:
    logger.addHandler(logging.FileHandler(CURRENT_DIR / "grader_output.txt", mode="w"))


RESULT_REGEX = re.compile(r"Result: (\d+)\/\d+")


def get_stderr(error: sh.ErrorReturnCode, string):
    error = str(error)
    return string + error[error.find("STDERR:") + len("STDERR"):].strip().replace(str(CURRENT_DIR), "...")


def print_results(min_score: int, *args, **kwargs):
    with open(CURRENT_DIR / "grader_output.txt") as f:
        contents = f.read()
    student_outputs = contents.split("\n\n")
    for output in student_outputs:
        match = RESULT_REGEX.search(output)
        if match is not None:
            score = int(match.group(1))
            if score >= min_score:
                print(output + "\n", *args, **kwargs)
