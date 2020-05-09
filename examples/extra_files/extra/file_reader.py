# You can include source files in extra too!


def read_numbers(path):
    with open(path) as f:
        return [int(n) for n in f.read().split() if n]
