from ._basics import BasicGate

import numpy as np
import cmath
import copy

# I know this is ugly...
class DiagonalGate(BasicGate):
    """
    A diagonal gate is a unitary operation whose matrix representation
    in the computational basis is diagonal.

    TODO:
        D = DiagonalGate(angles)
        D | qureg

    The order of the basis is given by the order of qureg....
    """
    def __init__(self, angles=[], phases=[]):
        # only ever need one of the two in any instance
        assert not angles or not phases
        if len(angles) > 0:
            self._angles = copy.copy(angles)
            self._phases = []
        elif len(phases) > 0:
            self._phases = copy.copy(phases)
            self._angles = []
        else:
            assert False
        self.interchangeable_qubit_indices = []

    @property
    def angles(self):
        if self._angles:
            return self._angles
        else:
            print("not good 1")
            return [cmath.phase(phase) for phase in self._phases]

    @property
    def phases(self):
        if self._phases:
            return self._phases
        else:
            print("not good 2")
            return [cmath.exp(1j*angle) for angle in self._angles]

    def get_inverse(self):
        inv_angles = [-angle for angle in self.angles]
        return DiagonalGate(angles = inv_angles)

    def __str__(self):
        return "D"
