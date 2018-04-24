from ._basics import BasicGate

import copy

class Isometry(BasicGate):
    """
    Isometries ...
    """
    def __init__(self, cols):
        self._cols = copy.deepcopy(cols)
        self.interchangeable_qubit_indices = []
        self._decomposed = False

    @property
    def cols(self):
        return self._cols

    def decompose(self):
        assert self._decomposed == False
        # don't use classes
        from projectq.isometries import _DecomposeIsometry
        self._decomposition = _DecomposeIsometry(self._cols).get_decomposition()
        self._decomposed = True

    @property
    def decomposed(self):
        return self._decomposed

    @property
    def decomposition(self):
        return self._decomposition

    def __str__(self):
        return "V"
