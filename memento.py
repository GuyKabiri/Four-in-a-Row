class Memento:
    def __init__(self, value: object) -> None:
        '''
        Create a new memento.

            Parameters:
                value (object): An object to save as a state.
        '''
        self.state = value


    def get_state(self) -> object:
        '''
        Get the state of the memento.

            Returns:
                state (object): The object that was saved in the memnto.
        '''
        return self.state


class Originator:
    def __init__(self) -> None:
        '''
        Create a new originator to handle the memento state.
        '''
        self._state = None


    def set_state(self, value: object) -> None:
        '''
        Save an object copy as the state so it could be saved as a memento object.

            Parameters:
                value (object): The object to save its copy.
        '''
        self._state = value.copy()


    def get_state(self) -> object:
        '''
        Returns the current stated (object) of the originator.

            Returns:
                state (object): The object that was saved in the memnto.
        '''
        return self._state


    def create_memento(self) -> Memento:
        '''
        Create memento object of the current state.
        '''
        return Memento(self._state)


class CareTaker:
    def __init__(self, obj_originator: Originator) -> None:
        '''
        Create a new caretaker to maintain a mechanism of undo.

            Parameters:
                obj_originator (Originator): An originator object to maintain the memnto state.
        '''
        self.mementos = []
        self.origin = obj_originator


    def do(self) -> None:
        '''
        Adds a memento state to the list.
        '''
        memento = self.origin.create_memento()
        self.mementos.append(memento)


    def undo(self):
        '''
        Undo the last action in the list. Returns True if performed undo, otherwise returns False.

            Returns:
                performed (bool): True if performed undo, False if did not.
        '''
        if len(self.mementos) > 1:
            self.mementos.pop()
            self.origin.set_state(self.mementos[len(self.mementos) - 1].get_state())
            return True
        return False