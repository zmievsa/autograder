from enum import IntEnum

SYSTEM_RESERVED_EXIT_CODES = [
    1,
    2,
    126,
    127,
    128,
    129,
    130,
    131,
    132,
    133,
    134,
    135,
    136,
    137,
    138,
    139,
    140,
    141,
    142,
    143,
    144,
    145,
    146,
    147,
    148,
    149,
    150,
    151,
    152,
    153,
    154,
    155,
    156,
    157,
    158,
    159,
    160,
    161,
    162,
    163,
    164,
    165,
    255,
]

USED_EXIT_CODES = (3, 4, 5)


class ExitCodeEventType(IntEnum):
    RESULT = 3
    CHECK_STDOUT = 4
    CHEAT_ATTEMPT = 5
