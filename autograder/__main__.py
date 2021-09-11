import argparse
import sys
from pathlib import Path


def main(argv=None):
    """Returns the average score of the students"""
    if argv is None:
        argv = sys.argv[1:]

    parser = _create_parser()

    args = parser.parse_args(argv)
    if args.version:
        from autograder.__version__ import __version__

        print(__version__)
        exit(0)
    current_dir = (Path.cwd() / args.submission_path).resolve()
    return _evaluate_args(args, current_dir)


def _create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="store_true", help="print the autograder version number and exit")
    subparsers = parser.add_subparsers(title="Commands", dest="command")
    _create_run_parser(subparsers)
    _create_stats_parser(subparsers)
    _create_guide_parser(subparsers)
    return parser


def _create_run_parser(subparsers):
    parser = subparsers.add_parser("run", help="Grade submissions in submission path or in current directory")
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
    _add_submission_path_argument(parser)


def _create_stats_parser(subparsers):
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
    _add_submission_path_argument(parser)


def _create_guide_parser(subparsers):
    parser = subparsers.add_parser("guide", help="Guide you through setting up a grading environment")
    _add_submission_path_argument(parser)


def _add_submission_path_argument(parser: argparse.ArgumentParser):
    parser.add_argument(
        "submission_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to directory that contains student submissions",
    )


def _evaluate_args(args, current_dir):
    if sys.platform.startswith("win32"):
        print(
            "Windows is not supported by autograder. If you do not have Linux,"
            "try using it through utilities like Windows Subsystem For Linux."
        )
        exit(1)
    elif sys.platform.startswith("darwin"):
        print("OSX is not officially supported. Proceed with caution.")
    from autograder.autograder import Grader, AutograderPaths  # That's some awful naming
    from autograder.util import AutograderError, print_results

    try:
        if args.command == "stats":
            if args.print:
                print_results(AutograderPaths(current_dir), args.print)
        elif args.command == "guide":
            from autograder import guide

            guide.main(AutograderPaths(current_dir))
        elif args.command == "run":
            return Grader(current_dir, no_output=args.no_output, submissions=args.submissions).run()
        else:
            raise NotImplementedError(f"Unknown command '{args.command}' supplied.")
    except AutograderError as e:
        print(e)
    return -1


if __name__ == "__main__":
    main()
