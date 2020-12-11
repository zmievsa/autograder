# You can include source files in extra too! Both student and testcase will be able to use it.


def read_numbers(path):
    with open(path) as f:
        return [int(n) for n in f.read().split() if n]
