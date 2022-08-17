class Memento:
    def __init__(self, value: object) -> None:
        self.state = value

    def get_state(self) -> object:
        return self.state


class Originator:
    def __init__(self) -> None:
        self._state = None

    def set_state(self, value: object) -> None:
        self._state = value.copy()

    def get_state(self) -> object:
        return self._state

    def create_memento(self) -> Memento:
        return Memento(self._state)


class CareTaker:
    def __init__(self, obj_originator: object) -> None:
        self.mementos = []
        self.origin = obj_originator

    def do(self) -> None:
        memento = self.origin.create_memento()
        self.mementos.append(memento)

    def undo(self):
        if len(self.mementos) > 1:
            self.mementos.pop()
            self.origin.set_state(self.mementos[len(self.mementos) - 1].get_state())
            return True
        return False