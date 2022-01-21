import os


def test_env():
    print(os.getenv("VALIDATING_STRING"))
    exit(103)


def test_exit():
    exit(103)


def test_import():
    """We test for unsuccessful imports because python is one of the only languages
    that don't have an easy way of restricting variables/functions from being imported.
    """
    from test_import import VALIDATING_STRING

    print(VALIDATING_STRING)
    exit(103)
