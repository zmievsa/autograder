# This is a dummy example to show how extra args work


def main():
    result = student_submission.add(1, 2)
    assert result == 3
    if result <= 3:
        PASS()
    else:
        FAIL()


main()
