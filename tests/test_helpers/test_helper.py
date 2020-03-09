# Allows us to use student's module from our testcase
import sys
import importlib
student_submission = importlib.import_module(sys.argv[1])


def NO_RESULT():
    exit({% RESULTLESS_EXIT_CODE %})

def RESULT(r):
    exit(r + ({% RESULT_EXIT_CODE_SHIFT %}))

def PASS():
    exit({% MAX_RESULT %})

def FAIL():
    exit({% MIN_RESULT %})
