from ._basics import BasicGate

import copy

class Isometry(BasicGate):
    """
    A gate that represents arbitrary Isometries.

    Example:
        .. code-block:: python
            col_0 = [1j, -1j]
            col_1 = ...
            V = Isometry([col_0 col_1])
            V | qureg

    """
    def __init__(self, cols):
        self.cols = copy.deepcopy(cols)
        self.interchangeable_qubit_indices = []
        self._decomposition = None

    @property
    def decomposition(self):
        if self._decomposition == None:
            from projectq.isometries import _decompose_isometry
            self._decomposition = _decompose_isometry(self.cols)
        return self._decomposition

    def __str__(self):
        return "V"
