import sys
import argparse
from pathlib import Path

from autograder.grader import Grader  # That's some awful naming


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('submission_path', type=Path, nargs="?", default=Path.cwd(),
                        help='Path to the directory that contains submissions and testcases')
    # TODO: Add --print and --clean args
    args = parser.parse_args(argv)
    Grader(Path.cwd() / args.submission_path).run()


if __name__ == "__main__":
    main()