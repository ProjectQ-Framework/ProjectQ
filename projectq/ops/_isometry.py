from ._basics import BasicGate

import copy

class Isometry(BasicGate):
    """
    Isometries ...
    """
    def __init__(self, cols):
        self._cols = copy.deepcopy(cols)
        self.interchangeable_qubit_indices = []
