from projectq.ops import BasicGate

import numpy as np

def _is_unitary(m):
    return np.allclose(m*m.H, np.eye(2))

# Helper class
class _SingleQubitGate(BasicGate):
    def __init__(self, m):
        self._matrix = m
        self.interchangeable_qubit_indices = []
        self._error = np.linalg.norm(m*m.H - np.eye(2))

    @property
    def matrix(self):
        return self._matrix

    def get_inverse(self):
        return _SingleQubitGate(self._matrix.getH())

    def __str__(self):
        return "U[{:.2f} {:.2f}; {:.2f} {:.2f}]".format(
            abs(self.matrix.item((0,0))), abs(self.matrix.item((0,1))),
            abs(self.matrix.item((1,0))), abs(self.matrix.item((1,1))))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return np.allclose(self.matrix, other.matrix)
        else:
            return False
