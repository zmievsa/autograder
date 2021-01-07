def TestOutput(s: str):
    """This function will format each character both in expected and student's outputs,
    removing all characters that are not digits.

    Its name has to be the same as the name of the testcase you're formatting.
    Alternatively, you could specify no stdout formatters or make a default formatter
    named ALL which will be the default formatter for any testcase for which no specific
    formatter has been written.
    """
    return "".join(filter(lambda c: c.isdigit(), s))
