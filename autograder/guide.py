import shutil
from pathlib import Path
from typing import Dict, Optional, Type

from .autograder import AutograderPaths
from .testcase_utils.abstract_testcase import TestCase
from .testcase_utils.testcase_picker import TestCasePicker


def create_dir(path: Path):
    if not path.exists():
        print(f"{path.name} directory does not exist. Creating...")
        path.mkdir()
    else:
        print(f"Found {path.name} directory")


def main(paths: AutograderPaths, language_name: Optional[str] = None, interactive=True):
    if not paths.current_dir.exists() or not paths.current_dir.is_dir():
        print(f"Directory {paths.current_dir} not found. Please, use an existing directory.")
        return
    print("Hello. I will now guide you through the initial setup of autograder.")
    if interactive:
        ans = input(f"Would you like to grade submissions located in '{paths.current_dir}'? (Yes/No) ")
    else:
        ans = "y"
    if not ans.lower().startswith("y"):
        print(
            "You probably haven't specified a directory to the grader. Use 'autograder guide path/to/submissions/dir'"
        )
        return
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
    stdout_formatters_path = paths.stdout_formatters
    if not stdout_formatters_path.exists():
        print(f"{stdout_formatters_path.name} not found. Creating a default file...")
        shutil.copy(str(paths.default_stdout_formatters), str(paths.stdout_formatters))
    else:
        print("Found stdout_formatters.py")

    if interactive:
        ans = input(
            "You are now ready to start working with autograder.\n"
            "Would you like me to generate the testcase templates? (Yes/No) "
        )
    elif language_name:
        ans = "y"
    else:
        ans = "n"
    if ans.lower().startswith("y"):
        supported_languages = _get_supported_languages()
        if not language_name:
            lang = _get_a_valid_language_choice(supported_languages)
        else:
            lang = supported_languages[language_name]
        shutil.copytree(lang.get_template_dir(), paths.current_dir, dirs_exist_ok=True)
        if lang.source_suffix.endswith("java"):
            print("\nJava forces us to have the same name for module and class so")
            print("you must put expected names for java submissions in tests/config.ini. Right now it's 'Homework'")
    print(
        "\n\nNow if you want to grade your submissions, you can use 'autograder run path/to/submissions/dir' "
        "for this directory."
    )
    print(f"You can write your testcases in {paths.testcases_dir}")
    print("If you want to see command line options, use 'autograder -h'")
    print(f"You can put the stdin inputs to your testcases into {paths.input_dir}")
    print(f"You can put the expected outputs to your testcases into {paths.output_dir}")
    print(f"You can put the extra files to be available for each testcase into {paths.extra_dir}")
    print(f"You can configure grading by editing {paths.config}")
    print("You can find docs at https://ovsyanka83.github.io/autograder/")


def _get_supported_languages() -> Dict[str, Type[TestCase]]:
    testcase_types = TestCasePicker.discover_testcase_types(AutograderPaths.testcase_types_dir)
    return {t.type_source_file.stem: t for t in testcase_types if (t.get_template_dir()).exists()}


def _get_a_valid_language_choice(supported_languages: Dict[str, Type[TestCase]]) -> Type[TestCase]:
    allowed_languages = ", ".join(name for name in supported_languages.keys())

    while True:
        choice = input(f"Choose a programming language you'd like to get templates for ({allowed_languages}): ")
        lang = supported_languages.get(choice, None)
        if lang is None:
            print(f"Couldn't find the language with name '{choice}'. Please, try again.")
        else:
            break
    return lang
