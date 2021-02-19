import os
import shutil
from pathlib import Path

from autograder.config_manager import ALLOWED_LANGUAGES

from .autograder import AutograderPaths
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
    stdout_formatters_path = paths.stdout_formatters
    if not stdout_formatters_path.exists():
        print(f"{stdout_formatters_path.name} not found. Creating a default file...")
        shutil.copy(paths.default_stdout_formatters, str(paths.stdout_formatters))
    else:
        print("Found stdout_formatters.py")

    ans = input(
        "You are now ready to start working with autograder.\n"
        "Would you like me to generate the testcase templates? (Yes/No) "
    )
    if ans.lower().startswith("y"):
        allowed_languages = ", ".join(ALLOWED_LANGUAGES.keys())
        while True:
            choice = input(
                f"Choose a programming language you'd like to generate testcase templates for ({allowed_languages}): "
            )
            lang = ALLOWED_LANGUAGES.get(choice, None)
            if lang is None:
                print(f"Couldn't find the language with name '{choice}'. Please, try again.")
            else:
                break
        safe_copytree(Path(__file__).parent / "templates" / choice, paths.testcases_dir, dirs_exist_ok=True)
    print(
        "\n\nNow if you want to grade your submissions, you can use 'autograder path/to/submissions/dir' "
        "for this directory."
    )
    print(f"You can write your testcases in {paths.testcases_dir}")
    print("If you want to see command line options, use 'autograder -h'")
    print(f"You can put the stdin inputs to your testcases into {paths.input_dir}")
    print(f"You can put the expected outputs to your testcases into {paths.output_dir}")
    print(f"You can put the extra files to be available for each testcase into {paths.extra_dir}")
    print(f"You can configure grading by editing {paths.config}")
    print("You can find readme at https://github.com/Ovsyanka83/autograder")


def safe_copytree(
    src,
    dst,
    symlinks=False,
    ignore=None,
    copy_function=shutil.copy2,
    ignore_dangling_symlinks=False,
    dirs_exist_ok=False,
):
    """This is a newer version of copytree only available for python3.8
    We need it because it has a dirs_exist_ok keyword arg
    """
    with os.scandir(src) as itr:
        entries = list(itr)
    if ignore is not None:
        ignored_names = ignore(os.fspath(src), [x.name for x in entries])
    else:
        ignored_names = set()

    os.makedirs(dst, exist_ok=dirs_exist_ok)
    errors = []
    use_srcentry = copy_function is shutil.copy2 or copy_function is shutil.copy

    for srcentry in entries:
        if srcentry.name in ignored_names:
            continue
        srcname = os.path.join(src, srcentry.name)
        dstname = os.path.join(dst, srcentry.name)
        srcobj = srcentry if use_srcentry else srcname
        try:
            is_symlink = srcentry.is_symlink()
            if is_symlink and os.name == "nt":
                # Special check for directory junctions, which appear as
                # symlinks but we want to recurse.
                lstat = srcentry.stat(follow_symlinks=False)
                if lstat.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT:
                    is_symlink = False
            if is_symlink:
                linkto = os.readlink(srcname)
                if symlinks:
                    # We can't just leave it to `copy_function` because legacy
                    # code with a custom `copy_function` may rely on copytree
                    # doing the right thing.
                    os.symlink(linkto, dstname)
                    shutil.copystat(srcobj, dstname, follow_symlinks=not symlinks)
                else:
                    # ignore dangling symlink if the flag is on
                    if not os.path.exists(linkto) and ignore_dangling_symlinks:
                        continue
                    # otherwise let the copy occur. copy2 will raise an error
                    if srcentry.is_dir():
                        shutil.copytree(srcobj, dstname, symlinks, ignore, copy_function, dirs_exist_ok=dirs_exist_ok)
                    else:
                        copy_function(srcobj, dstname)
            elif srcentry.is_dir():
                shutil.copytree(srcobj, dstname, symlinks, ignore, copy_function, dirs_exist_ok=dirs_exist_ok)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy_function(srcobj, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
        except OSError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        # Copying file access times may fail on Windows
        if getattr(why, "winerror", None) is None:
            errors.append((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)
    return dst
