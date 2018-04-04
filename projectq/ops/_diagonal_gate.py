from ._basics import BasicGate

import numpy as np
import copy

class DiagonalGate(BasicGate):
    """
    A diagonal gate is a unitary operation whose matrix representation
    in the computational basis is diagonal.

    TODO:
        D = DiagonalGate(angles)
        D | qureg

    The order of the basis is given by the order of qureg....
    """

    def __init__(self, angles):
        self._angles = copy.copy(angles)
        self.interchangeable_qubit_indices = []

    def get_inverse(self):
        inv_angles = [-angle for angle in self._angles]
        return DiagonalGate(inv_angles)

    @property
    def angles(self):
        return self._angles
