import sys
import argparse
from pathlib import Path

from autograder.grader import Grader  # That's some awful naming
from autograder.util import print_results, AutograderError
import autograder.guide


def main(argv=None):
    """ Returns the average score of the students """
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('submission_path',
        type=Path, nargs="?", default=Path.cwd(),
        help='Path to directory that contains student submissions'
    )
    parser.add_argument('-p', '--print',
        type=float, nargs="?", default=None, const=100, metavar="min_score",
        help='Use after already graded to print assignments with score >= min_score'
    )
    parser.add_argument('--no_output',
        action="store_true",
        help="Do not output any code to the console"
    )
    parser.add_argument('--generate_config',
        action="store_true",
        help="Generate a default config file in the <submission_path>"
    )
    parser.add_argument('-s', '--submissions',
                        action="store", nargs="*", metavar="<submission_name>", default=[],
                        help="Only grade submissions with specified file names (without full path)"
    )
    parser.add_argument('-g', '--guide',
                        action="store_true",
                        help="Guide you through setting up a grading environment"
    )
    args = parser.parse_args(argv)
    current_dir = (Path.cwd() / args.submission_path).resolve()
    if args.print is None:
        try:
            grader = Grader(
                current_dir,
                no_output=args.no_output,
                submissions=args.submissions,
            )
            if args.generate_config:
                grader.generate_config()
            elif args.guide:
                autograder.guide.main(current_dir, grader)
            else:
                return grader.run()
        except AutograderError as e:
            print(e)
    else:
        print_results(current_dir, args.print)
        return -1


if __name__ == "__main__":
    main()
