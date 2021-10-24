import sys


def main():
    # Students are also allowed to read from sys.argv
    result = student_submission.add(int(sys.argv[1]), int(sys.argv[2]))
    if result == 14:
        PASS()
    else:
        FAIL()


main()
