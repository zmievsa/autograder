# This is a dummy example to show how extra args work.
# It will fail if testcase is not precompiled because assert will throw an error
# but it will succeed if testcase is precompiled because config.ini contains a -O argument for this file
# which silences assertions.


def main():
    result = student_submission.add(1, 2)
    assert result == 3
    if result <= 3:
        PASS()
    else:
        FAIL()


main()
