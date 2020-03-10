from pathlib import Path
import logging
import sys
import sh


CURRENT_DIR = Path(__file__).parent.resolve()
SUBMISSIONS_DIR: Path = CURRENT_DIR / "submissions"
RESULTS_DIR: Path = CURRENT_DIR / "results"
TESTS_DIR: Path = CURRENT_DIR / "tests"


logger = logging.getLogger("Grader")
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler("grader_output.txt", mode="w"))
logger.addHandler(logging.StreamHandler(sys.stdout))


def get_stderr(error: sh.ErrorReturnCode, string):
    error = str(error)
    return string + error[error.find("STDERR:") + len("STDERR"):].strip()
