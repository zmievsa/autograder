# Seems like too much work for only 2 simple functions, no?


import random
import string
from typing import Tuple

VALIDATING_STRING_LENGTH = 30
# DO NOT ATTEMPT TO ADD string.punctuation: it might break strings in some languages because it contains "" and ''
POSSIBLE_CHARS_IN_VALIDATING_STRING = string.ascii_letters + string.digits
LAST_LINE_SPLITTING_CHARACTER = "$"


def generate_validating_string() -> str:
    """ Generates a string of pseudo-random ascii characters """
    # As far as I understand, we do not need this string to be cryptographically strong
    return "".join(random.choice(POSSIBLE_CHARS_IN_VALIDATING_STRING) for _ in range(VALIDATING_STRING_LENGTH))


# Beware: Horrible space and time complexity. Maybe we should optimize that?
def validate_output(output: str, required_validating_string: str) -> Tuple[str, float, bool]:
    """Checks if the output contains the correct validating string on the last line

    Returns the output without the last line (or empty string if it was empty),
    the score that was printed with the validation string and boolean that is true if output is valid.
    """
    if not output:
        return output, 0, False
    split_output = output.splitlines()
    last_line = split_output.pop(-1)
    try:
        result, actual_validating_string = last_line.split(LAST_LINE_SPLITTING_CHARACTER, 1)
        result = float(result)
    except ValueError:  # Means that the last line is not formatted correctly
        return output, 0, False
    output = "\n".join(split_output)
    return output, result, actual_validating_string == required_validating_string
