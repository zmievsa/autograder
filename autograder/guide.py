from .grader import Grader, ALLOWED_LANGUAGES
from pathlib import Path
import shutil


def create_dir(path: Path):
    if not path.exists():
        print(f"{path.name} directory does not exist. Creating...")
        path.mkdir()
    else:
        print(f"Found {path.name} directory")


def main(path: Path, grader: Grader):
    if not path.exists() or not path.is_dir():
        print(f"Directory {path} not found. Please, use an existing directory.")
        exit(0)
    print("Hello. I will now guide you through the initial setup of autograder.")
    ans = input(f"Would you like to grade submissions located in '{path}'? (Yes/No) ")
    if not ans.lower().startswith("y"):
        print("You probably haven't specified a directory to the grader. Use 'autograder path/to/submissions/dir'")
        exit(0)
    create_dir(grader.tests_dir)
    create_dir(grader.testcases_dir)
    create_dir(grader.tests_dir / "input")
    create_dir(grader.tests_dir / "output")
    config_path = grader.tests_dir / "config.ini"
    if not config_path.exists():
        print(f"config.ini not found in {grader.tests_dir}. Creating a default config...")
        grader.generate_config()
    else:
        print("Found config.ini")
    output_formatters_path = grader.tests_dir / "output_formatters.py"
    if not output_formatters_path.exists():
        print(f"{output_formatters_path.name} not found. Creating a default file...")
        shutil.copy(
            str(Path(__file__).parent / "default_formatters.py"),
            str(grader.tests_dir / "output_formatters.py")
        )
    else:
        print("Found output_formatters.py")

    ans = input("You are now ready to start working with autograder.\n"
                "Would you like me to give you the link to the example testcases? (Yes/No) ")
    if ans.lower().startswith("y"):
        while True:
            allowed_languages = ', '.join(ALLOWED_LANGUAGES.keys())
            choice = input(f"Choose a programming language you'd like to generate testcases for ({allowed_languages}): ")
            lang = ALLOWED_LANGUAGES.get(choice, None)
            if lang is None:
                print(f"Couldn't find the language with name '{choice}'. Please, try again.")
            else:
                break
        print("Here is the default testcase directory:\n"
              f"https://github.com/Ovsyanka83/autograder/tree/master/examples/{choice.lower()}/tests/testcases")
    print("Now if you want to grade your submissions, you can use 'autograder path/to/submissions/dir' "
          "for this directory.")
    print(f"You can write your testcases in {path / 'tests/testcases'}")
    print("If you want to see command line options, use 'autograder -h'")
    print(f"You can put the stdin inputs to your testcases into {path / 'tests/input'}")
    print(f"You can put the expected outputs to your testcases into {path / 'tests/output'}")
    print(f"You can configure grading by editing {path / 'tests/config.ini'}")
    print("You can find readme at https://github.com/Ovsyanka83/autograder")

