#!/usr/bin/env python3
# This homework checks whether stdout formatters are functioning correctly for stdout-only testcases


def numberSaver():
    arr = [0] * 9
    sum = 0
    while True:
        userInput = int(input("Input num from 1 to 9 (0 to exit):\n"))
        if userInput > 0 and userInput < 10:
            arr[userInput - 1] += 1
        else:
            break

    print("You typedd::")

    for i in range(1, 10):
        print(f"{i}) {arr[i-1]} time(s)")
        sum += arr[i - 1] * i

    return sum


numberSaver()
