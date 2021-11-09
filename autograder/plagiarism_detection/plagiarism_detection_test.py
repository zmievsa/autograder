import time
from pathlib import Path

from plagiarism_detection import compare


def main():
    paths = [f for f in Path("test/demo").iterdir()]

    start = time.time()
    print(compare(paths))
    print(time.time() - start)


if __name__ == "__main__":
    main()
