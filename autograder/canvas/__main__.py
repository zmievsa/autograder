"""
>>> autograder canvas send -h
usage: autograder canvas send [-h] [-k [api_key]] [-a [assignment_id]] [-g] [-s] [testing_dir_path]

positional arguments:
  testing_dir_path       Path to directory that contains student submissions

optional arguments:
  -h, --help                            show this help message and exit
  -k, --api_key [api_key]               key associated with the canvas user running autograder (will be asked during run if not provided or already saved)
  -a, --assignment_id [assignment_id]   id associated with the canvas assignment being graded  (will be asked during run if not provided)
  -g, --grade_assignments               will put assignment grades for all submissions associated with their test results 
  -s, --save_api_key_globally           will make autograder remember the canvas api key for future grading
"""

import sys
from pathlib import Path
import argparse


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    return _evaluate_args(_create_parser().parse_args(argv))


def _create_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="Commands", dest="api_key_command")
    _create_upload_parser(subparsers)
    _create_api_key_parser(subparsers)
    return parser


def _create_upload_parser(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("upload", help="Upload assignment grades to canvas")
    parser.add_argument(
        "submission_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to directory that contains student submissions",
    )


def _create_api_key_parser(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("api_key", help="Create/Save/Get/Delete api_key")
    parser.add_argument("url", help="Canvas url")  # TODO: Change its help
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-c", "--create", action="store_true", help="Create a new canvas api key and save it.")
    group.add_argument("-g", "--get", action="store_true", help="Print the api key saved for the specified url.")
    group.add_argument("-d", "--delete", action="store_true", help="Delete the api key saved for the specified url.")
    group.add_argument("-s", "--save", action="store", metavar="<key>", help="Save the specified api-key globally.")


def _evaluate_args(args):
    pass


if __name__ == "__main__":
    main()
