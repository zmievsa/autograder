import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

L = logging.getLogger("AUTOGRADER")
logging.basicConfig(level=logging.CRITICAL, handlers=[logging.StreamHandler()])


def main(argv: Optional[List[str]] = None):
    if argv is None:
        argv = sys.argv[1:]

    parser = _create_parser()

    args = parser.parse_args(argv)
    if args.version:
        from autograder.__version__ import __version__

        print(__version__)
    # the interface architecture needs to be refactored a bit. For now, this hack with hasattr
    # will prevent errors if autograder has been called on its own.
    elif not hasattr(args, "submission_path"):
        parser.print_help()
    else:
        current_dir = (Path.cwd() / args.submission_path).resolve()
        return _evaluate_args(args, current_dir)


def _create_parser():
    parser = argparse.ArgumentParser(prog="autograder")
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="print the autograder version number and exit",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command")
    _create_run_parser(subparsers)
    _create_stats_parser(subparsers)
    _create_guide_parser(subparsers)
    _create_plagiarism_parser(subparsers)
    return parser


def _create_run_parser(subparsers):
    parser = subparsers.add_parser("run", help="Grade submissions in submission path or in current directory")
    parser.add_argument("-j", "--json", action="store_true", help="Output grades in json format")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all debugging output")
    _add_submission_path_argument(parser)
    _add_submission_list_argument(parser)


def _create_stats_parser(subparsers):
    # TODO: Rewrite stats parser to handle json output
    # parser = subparsers.add_parser("stats", help="Display statistics on student grades")
    # parser.add_argument(
    #     "-p",
    #     "--print",
    #     type=float,
    #     nargs="?",
    #     default=None,
    #     const=100,
    #     metavar="min_score",
    #     help="Use after already graded to print assignments with score >= min_score",
    # )
    # _add_submission_path_argument(parser)
    pass


def _create_guide_parser(subparsers):
    parser = subparsers.add_parser("guide", help="Guide you through setting up a grading environment")
    _add_submission_path_argument(parser)


def _create_plagiarism_parser(subparsers):
    parser = subparsers.add_parser("plagiarism", help="Checks how similar the submissions are to each other")
    _add_submission_path_argument(parser)
    _add_submission_list_argument(parser)


def _add_submission_path_argument(parser: argparse.ArgumentParser):
    parser.add_argument(
        "submission_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to directory that contains student submissions",
    )


def _add_submission_list_argument(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-s",
        "--submissions",
        action="store",
        nargs="*",
        metavar="<name>",
        type=Path,
        default=None,
        help="Only consider submissions with specified file names (without full path)",
    )


def _evaluate_args(args: argparse.Namespace, current_dir: Path):
    from autograder.autograder import AutograderPaths, Grader

    if args.command == "guide":
        from autograder import guide

        guide.main(AutograderPaths(current_dir))
    elif args.command == "run":
        if args.verbose:
            L.setLevel(logging.DEBUG)
        submissions = [s.name for s in args.submissions] if args.submissions else args.submissions
        return Grader(current_dir, args.json, submissions).run()
    elif args.command == "plagiarism":
        import json

        from . import plagiarism_detection

        files = [f for f in current_dir.iterdir() if f.is_file() and not f.suffix.endswith(".txt")]
        if args.submissions is not None:
            submissions = [submission.name for submission in args.submissions]
            files = [f for f in files if f.name in submissions]
        result = plagiarism_detection.compare(files)
        result = {tuple(k): v for k, v in result[list(result.keys())[0]].items()}
        output = [{"student1": k[0].name, "student2": k[1].name, "similarity_score": v} for k, v in result.items()]
        output.sort(key=lambda v: v["similarity_score"], reverse=True)
        print(json.dumps({"results": output}, indent=4))
    else:
        raise NotImplementedError(
            f"Unknown command '{args.command}' supplied.\nTry 'autograder --help for more information'"
        )
    return -1


if __name__ == "__main__":
    main()
    exit(0)
