# You can include source files in extra too! Both student and testcase will be able to use it.

from pathlib import Path


def read_numbers(path):
    return [int(n) for n in Path(path).read_text().split() if n]
