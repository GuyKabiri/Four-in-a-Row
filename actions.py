import enum
from typing import Any


class Actions(enum.Enum):
    EXIT = -3
    RESET = -2
    PRE_GAME = -1

    READY = 1
    WIN = 2
    TIE = 3
    CONTINUE = 4
    ADD_PIECE = 5
    UNDO = 6
    ILLEGAL_LOCATION = 7
    ILLEGAL_DATA = 8

    UNKNOWN = 100

    def is_equals(self, val: Any) -> bool:
        """
        Check whether a value equals to the enum actions value

            Parameters:
                val (int): Value to compare with.

            Returns:
                equals (bool): True if the integer value equals to the enum value.
        """
        return self.value == int(val)
