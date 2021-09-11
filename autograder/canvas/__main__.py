import sys
from pathlib import Path
import argparse

from autograder.canvas.auth import Token, FILE_WITH_TOKEN_INFO
from autograder.canvas.submissions import upload_results


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
    parser = subparsers.add_parser("upload", help="Upload assignments back to canvas")
    parser.add_argument(
        "submission_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to directory that contains student submissions",
    )
    parser.add_argument("course_id", type=int)
    parser.add_argument("assignment_id", type=int)
    parser.add_argument(
        "-g",
        "--grade",
        action="store_true",
        help="Also upload grades for each student submission.",
    )


def _create_api_key_parser(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("token", help="Create/Save/Get/Delete api_key")
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-c",
        "--create",
        action="store",
        metavar="<base_url>",
        help="Create a new canvas api key and save it.",
    )
    group.add_argument("-g", "--get", action="store_true", help="Print the api key saved for the specified url.")
    group.add_argument("-d", "--delete", action="store_true", help="Delete the api key saved for the specified url.")
    group.add_argument(
        "-s",
        "--save",
        action="store",
        nargs=2,
        metavar=("<base_url>", "<token>"),
        help="Save the specified api-token globally.",
    )


def _evaluate_args(args):
    if args.api_key_command == "token":
        if args.create:
            return Token.create(args.create, FILE_WITH_TOKEN_INFO)
        elif args.save:
            Token(args.save[0], args.save[1], FILE_WITH_TOKEN_INFO).save()
        elif args.get:
            token = Token.from_file(FILE_WITH_TOKEN_INFO)
            print(f"Base url: {token.base_url}, Token: {token.token}")
            return token
        elif args.delete:
            Token.from_file(FILE_WITH_TOKEN_INFO).delete()
    elif args.api_key_command == "upload":
        upload_results(args.submission_path, args.course_id, args.assignment_id, args.grade)


if __name__ == "__main__":
    main()
