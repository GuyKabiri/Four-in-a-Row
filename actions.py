import enum

class Actions(enum.Enum):
    EXIT =              -1
    READY =             1
    WIN =               2
    TIE =               3
    CONTINUE =          4
    ADD_PIECE =         5
    ILLEGAL_LOCATION =  6


    ILLEGAL_DATA =      8

    UNKNOWN = 100

    def is_equals(self, val):
        return self.value == int(val)