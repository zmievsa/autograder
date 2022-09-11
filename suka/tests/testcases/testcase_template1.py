# student_submission is provided by autograder, represents student's module, and can be used freely
# PASS(), RESULT(res), FAIL(), and CHECK_STDOUT() are also provided by autograder and can be used freely


def main():
    # You can call any function from student's file like this.
    # It can have any arguments and return values -- use it like any other function.
    result = student_submission.some_student_function()

    SOME_EXPECTED_RESULT = 83
    if result == SOME_EXPECTED_RESULT:
        PASS()
    else:
        FAIL()


main()
