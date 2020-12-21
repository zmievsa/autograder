import argparse
import sys
from pathlib import Path

from autograder import guide
from autograder.__version__ import __version__
from autograder.grader import Grader  # That's some awful naming
from autograder.util import AutograderError, print_results


def main(argv=None):
    """ Returns the average score of the students """
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="store_true", help="show the version number")
    parser.add_argument(
        "submission_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to directory that contains student submissions",
    )
    parser.add_argument(
        "-p",
        "--print",
        type=float,
        nargs="?",
        default=None,
        const=100,
        metavar="min_score",
        help="Use after already graded to print assignments with score >= min_score",
    )
    parser.add_argument("--no_output", action="store_true", help="Do not output any code to the console")
    parser.add_argument(
        "-s",
        "--submissions",
        action="store",
        nargs="*",
        metavar="<name>",
        default=[],
        help="Only grade submissions with specified file names (without full path)",
    )
    parser.add_argument("-g", "--guide", action="store_true", help="Guide you through setting up a grading environment")
    args = parser.parse_args(argv)
    current_dir = (Path.cwd() / args.submission_path).resolve()
    if args.version:
        print(__version__)
        exit(0)
    try:
        grader = Grader(
            current_dir,
            no_output=args.no_output,
            submissions=args.submissions,
        )
        if args.print:
            print_results(grader.paths, args.print)
        elif args.guide:
            guide.main(grader.paths)
        else:
            return grader.run()
    except AutograderError as e:
        print(e)
    return -1


if __name__ == "__main__":
    main()
