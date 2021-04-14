import argparse
import sys
from pathlib import Path


def main(argv=None):
    """ Returns the average score of the students """
    if argv is None:
        argv = sys.argv[1:]

    parser = _create_parser()

    args = parser.parse_args(argv)
    current_dir = (Path.cwd() / args.submission_path).resolve()
    if args.version:
        from autograder.__version__ import __version__

        print(__version__)
        exit(0)

    if sys.platform.startswith("win32"):
        print(
            "Windows is not supported by autograder. If you do not have Linux,"
            "try using it through utilities like Windows Subsystem For Linux."
        )
        exit(1)
    elif sys.platform.startswith("darwin"):
        print("OSX is not officially supported. Proceed with caution.")
    from autograder.autograder import Grader  # That's some awful naming
    from autograder.util import AutograderError, print_results

    try:
        grader = Grader(
            current_dir,
            no_output=args.no_output,
            submissions=args.submissions,
        )
        if args.print:
            print_results(grader.paths, args.print)
        elif args.guide:
            from autograder import guide

            guide.main(grader.paths)
        else:
            return grader.run()
    except AutograderError as e:
        print(e)
    return -1


def _create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="store_true", help="print the autograder version number and exit")
    subparsers = parser.add_subparsers(title="Commands")
    _create_run_parser(subparsers)
    _create_stats_parser(subparsers)
    _create_guide_parser(subparsers)
    return parser


def _create_run_parser(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("run", help="Grade submissions in submission path or in current directory")
    parser.add_argument(
        "submission_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to directory that contains student submissions",
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


def _create_stats_parser(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("stats", help="Display statistics on student grades")
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


def _create_guide_parser(subparsers: argparse._SubParsersAction):
    subparsers.add_parser("guide", help="Guide you through setting up a grading environment")


if __name__ == "__main__":
    main()
