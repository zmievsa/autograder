import random
from enum import Enum
from typing import Dict


SYSTEM_RESERVED_EXIT_CODES = [
    1, 2, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141,
    142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158,
    159, 160, 161, 162, 163, 164, 165, 255
]
# If you want to extend the grader, you change the upper bound of the range
# of ALL_USED_EXIT_CODES
ALL_USED_EXIT_CODES = [0] + list(range(3, 126)) + list(range(166, 255))

EXIT_CODE_COUNT_FOR_RESULTS = 101
ALLOWED_EXIT_CODE_COUNT = EXIT_CODE_COUNT_FOR_RESULTS + 1  # 1 for CHECK_OUTPUT


class ExitCodeEventType(Enum):
    SYSTEM_ERROR = 0
    RESULT = 1
    CHECK_OUTPUT = 2
    CHEAT_ATTEMPT = 3


class ExitCodeEvent:
    type: ExitCodeEventType
    
    value: int = -float("inf")  # type: ignore

    def __init__(self, type, value=-float("inf")):
        """ We set it to -infinity to prevent dumb mistakes.
            If a developer misuses the value, the obvious error
            will most likely occur.
        """
        self.type = type
        self.value = value


class ExitCodeHandler:
    """ Randomizes exit codes allowed in the program to prevent
        cheating by using built-in exit(). If we use all available
        exit codes, we are going to get a ~5% chance of getting 90%
        or above if a student tries to cheat.

        Indexes of allowed_exit_codes are the actual results (scores
        or a value that means 'CHECK_OUTPUT') that correspond to
        randomized exit codes.
    """
    def __init__(self):
        self.allowed_exit_codes = self._generate_allowed_exit_codes()
        self.result_exit_codes = self.allowed_exit_codes[:-1]
        self.check_output_exit_code = self.allowed_exit_codes[-1]

    def scan(self, exit_code: int) -> ExitCodeEvent:
        if exit_code in self.allowed_exit_codes:
            if exit_code == self.check_output_exit_code:
                return ExitCodeEvent(ExitCodeEventType.CHECK_OUTPUT)
            else:
                associated_value = self.allowed_exit_codes.index(exit_code)
                return ExitCodeEvent(ExitCodeEventType.RESULT, associated_value)
        elif exit_code in SYSTEM_RESERVED_EXIT_CODES:
            return ExitCodeEvent(ExitCodeEventType.SYSTEM_ERROR)
        # It means that it IS used by grader but not chosen as a value
        elif exit_code in ALL_USED_EXIT_CODES:
            return ExitCodeEvent(ExitCodeEventType.CHEAT_ATTEMPT)
        else:
            raise ValueError(f"Exit code '{exit_code}' is not possible.")

    def get_formatted_exit_codes(self) -> Dict[str, str]:
        # Last exit code is for check_output
        formatted_result_exit_codes = ', '.join(str(r) for r in self.result_exit_codes)
        return {
            "RESULT_EXIT_CODES": formatted_result_exit_codes,
            "CHECK_OUTPUT_EXIT_CODE": str(self.check_output_exit_code)
        }

    @staticmethod
    def _generate_allowed_exit_codes():
        used_exit_codes = ALL_USED_EXIT_CODES.copy()
        random.shuffle(used_exit_codes)
        return used_exit_codes[:ALLOWED_EXIT_CODE_COUNT]
