# Allows us to use student's module from our testcase
import importlib
import sys
import os


def CHECK_OUTPUT():
    print("\n{}".format(VALIDATING_STRING), end="")
    exit({ % CHECK_OUTPUT_EXIT_CODE % })

def RESULT(r):
    print("\n{}".format(VALIDATING_STRING), end="")
    exit(r + { % RESULT_EXIT_CODE_OFFSET % })

def PASS():
    RESULT(100)

def FAIL():
    RESULT(0)


VALIDATING_STRING = os.environ.pop("VALIDATING_STRING", None)
if __name__ != "__main__" or VALIDATING_STRING is None:
    # If a student tries to import a testcase, the test will instantly fail.
    # It would also technically be a recursive import which would most likely
    # raise an exception but I put this here as a safeguard.
    print("CHEATING ATTEMPT")
    FAIL()

student_submission = importlib.import_module(sys.argv[1])