import os


def test_env():
    print(os.getenv("VALIDATING_STRING"))
    exit(3)


# The student might hope to get successful on an empty stdout check
def test_exit():
    exit(4)


def test_import():
    """We test for unsuccessful imports because python is one of the only languages
    that don't have an easy way of restricting variables/functions from being imported.
    """
    from test_import import VALIDATING_STRING

    print(VALIDATING_STRING)
    exit(103)
