def add_numbers():
    numbers = input("Please, input numbers to add: ")
    numbers = (int(n) for n in numbers.split())
    return sum(numbers)
