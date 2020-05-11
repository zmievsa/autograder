from file_reader import read_numbers


def main():
    numbers = read_numbers("numbers_to_add.txt")
    sum = 0
    for n in numbers:
        sum = student_submission.add(sum, n)
    if sum == 15:
        PASS()
    else:
        FAIL()


main()