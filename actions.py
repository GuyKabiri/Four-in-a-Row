import enum
from typing import Any

class Actions(enum.Enum):
    EXIT =              -2
    RESET =             -1
    READY =             1
    WIN =               2
    TIE =               3
    CONTINUE =          4
    ADD_PIECE =         5
    ILLEGAL_LOCATION =  6
    ILLEGAL_DATA =      7

    UNKNOWN =           100

    def is_equals(self, val: Any) -> bool:
        '''
        Check whether a value equals to the enum actions value

            Parameters:
                val (int): Value to compare with.

            Returns:
                equals (bool): True if the integer value equals to the enum value. 
        '''
        return self.value == int(val)