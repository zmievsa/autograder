def digits_only(c: str):
    return c.isdigit()

def no_whitespace(c: str):
    return not c.isspace()

ALLOWED_FILTERS = {
    "DIGITS_ONLY": digits_only,
    "NO_WHITESPACE": no_whitespace
}