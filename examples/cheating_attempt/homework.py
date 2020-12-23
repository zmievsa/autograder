import os


def test_env():
    print(os.getenv("VALIDATING_STRING"))
    exit(103)


def test_exit():
    exit(103)


def test_import():
    from test_import import VALIDATING_STRING

    print(VALIDATING_STRING)
    exit(103)