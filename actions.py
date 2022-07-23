import enum

class Actions(enum.Enum):
    EXIT =              -1
    WIN =               1
    CONTINUE =          2
    ADD_PIECE =         3
    ILLEGAL_LOCATION =  4


    ILLEGAL_DATA =      8

    UNKNOWN = 100

    def is_equals(self, val):
        return self.value == int(val)