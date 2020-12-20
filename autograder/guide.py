import shutil
from pathlib import Path

from autograder.config_manager import ALLOWED_LANGUAGES

from .grader import AutograderPaths
from .testcases import ALLOWED_LANGUAGES


def create_dir(path: Path):
    if not path.exists():
        print(f"{path.name} directory does not exist. Creating...")
        path.mkdir()
    else:
        print(f"Found {path.name} directory")


def main(paths: AutograderPaths):
    if not paths.current_dir.exists() or not paths.current_dir.is_dir():
        print(f"Directory {paths.current_dir} not found. Please, use an existing directory.")
        exit(0)
    print("Hello. I will now guide you through the initial setup of autograder.")
    ans = input(f"Would you like to grade submissions located in '{paths.current_dir}'? (Yes/No) ")
    if not ans.lower().startswith("y"):
        print("You probably haven't specified a directory to the grader. Use 'autograder path/to/submissions/dir'")
        exit(0)
    create_dir(paths.tests_dir)
    create_dir(paths.testcases_dir)
    create_dir(paths.input_dir)
    create_dir(paths.output_dir)
    create_dir(paths.extra_dir)
    config_path = paths.config
    if not config_path.exists():
        print(f"config.ini not found in {paths.tests_dir}. Creating a default config...")
        paths.generate_config()
    else:
        print("Found config.ini")
    output_formatters_path = paths.output_formatters
    if not output_formatters_path.exists():
        print(f"{output_formatters_path.name} not found. Creating a default file...")
        shutil.copy(paths.default_output_formatters, str(paths.output_formatters))
    else:
        print("Found output_formatters.py")

    ans = input(
        "You are now ready to start working with autograder.\n"
        "Would you like me to give you the link to the example testcases? (Yes/No) "
    )
    if ans.lower().startswith("y"):
        allowed_languages = ", ".join(ALLOWED_LANGUAGES.keys())
        while True:
            choice = input(
                f"Choose a programming language you'd like to generate testcases for ({allowed_languages}): "
            )
            lang = ALLOWED_LANGUAGES.get(choice, None)
            if lang is None:
                print(f"Couldn't find the language with name '{choice}'. Please, try again.")
            else:
                break
        print(
            "Here is the default testcase directory:\n"
            f"https://github.com/Ovsyanka83/autograder/tree/master/examples/{choice.lower()}/tests/testcases"
        )
    print(
        "Now if you want to grade your submissions, you can use 'autograder path/to/submissions/dir' "
        "for this directory."
    )
    print(f"You can write your testcases in {paths.testcases_dir}")
    print("If you want to see command line options, use 'autograder -h'")
    print(f"You can put the stdin inputs to your testcases into {paths.input_dir}")
    print(f"You can put the expected outputs to your testcases into {paths.output_dir}")
    print(f"You can put the extra files to be available for each testcase into {paths.extra_dir}")
    print(f"You can configure grading by editing {paths.config}")
    print("You can find readme at https://github.com/Ovsyanka83/autograder")
