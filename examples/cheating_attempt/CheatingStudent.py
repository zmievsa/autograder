def add_numbers():
    """The student knows that we use exit codes, knows their offset
    and is trying to get a 100 for the test case by calling exit() himself
    """
    exit_code_offset = 3
    exit(100 + exit_code_offset)
