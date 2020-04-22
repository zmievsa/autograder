# Allows us to use student's module from our testcase
import sys
import importlib
student_submission = importlib.import_module(sys.argv[1])


RESULT_EXIT_CODES = [{% RESULT_EXIT_CODES %}]

def CHECK_OUTPUT():
    exit({% CHECK_OUTPUT_EXIT_CODE %})

def RESULT(r):
    exit(RESULT_EXIT_CODES[r])

def PASS():
    RESULT(100)

def FAIL():
    RESULT(0)
