import sys
import argparse
from pathlib import Path

from autograder.grader import Grader  # That's some awful naming
from autograder.util import print_results


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('submission_path',
        type=Path, nargs="?", default=Path.cwd(),
        help='Path to directory that contains student submissions'
    )
    parser.add_argument('-g', '--generate_results',
        action="store_true",
        help='Generate results directory with a result file per student'
    )
    parser.add_argument('-p', '--print',
        type=float, nargs="?", default=None, const=100, metavar="min_score",
        help='Use after already graded to print assignments with score >= min_score'
    )
    args = parser.parse_args(argv)
    current_dir = Path.cwd() / args.submission_path
    if args.print is None:
        Grader(current_dir, args.generate_results).run()
    else:
        print_results(current_dir, args.print)
    


if __name__ == "__main__":
    main()