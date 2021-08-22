
# Allows us to use student's module from our testcase
import importlib
import os
import sys


def CHECK_STDOUT():
    print(f"\n-1{ % SPLITCHAR % }{VALIDATING_STRING}", end="")
    exit({ % CHECK_STDOUT_EXIT_CODE % })

def RESULT(r: float):
    print(f"\n{r}{ % SPLITCHAR % }{VALIDATING_STRING}", end="")
    exit({ % RESULT_EXIT_CODE % })

def PASS():
    RESULT(100)

def FAIL():
    RESULT(0)

def CHEATING_ATTEMPT():
    exit({ % CHEAT_ATTEMPT_EXIT_CODE % })


VALIDATING_STRING = os.environ.pop("VALIDATING_STRING", None)
if __name__ != "__main__" or VALIDATING_STRING is None:
    # If a student tries to import a testcase, the test will instantly fail.
    # It would also technically be a recursive import which would most likely
    # raise an exception but I put this here as a safeguard.
    print("CHEATING ATTEMPT")
    del VALIDATING_STRING
    CHEATING_ATTEMPT()

student_submission = importlib.import_module(sys.argv[1])