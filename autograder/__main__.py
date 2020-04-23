import sys
import argparse
from pathlib import Path

from autograder.grader import Grader  # That's some awful naming
from autograder.util import print_results


def main(argv=None):
    """ Returns the average score of the students """
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
    parser.add_argument('--precompile_testcases',
        action="store_true",
        help='Precompile testcases to hide their files from student (Java support is minimal)'
    )
    args = parser.parse_args(argv)
    current_dir = (Path.cwd() / args.submission_path).resolve()
    if args.print is None:
        return Grader(
            current_dir,
            args.generate_results,
            precompile_testcases=args.precompile_testcases).run()
    else:
        print_results(current_dir, args.print)
        return -1


if __name__ == "__main__":
    main()
