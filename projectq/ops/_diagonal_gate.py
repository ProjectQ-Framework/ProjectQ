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
        D = DiagonalGate(complex_phases)
        D | qureg

    The order of the basis is given by the order of qureg....
    """
    def __init__(self, angles=[], phases=[]):
        # only ever need one of the two in any instance
        assert len(angles) == 0 or len(phases) == 0
        if len(angles) > 0:
            print("Dont construct from angles")
            self._angles = copy.copy(angles)
            self._phases = []
        elif len(phases) > 0:
            self._phases = copy.copy(phases)
            self._angles = []
        else:
            assert False
        self.interchangeable_qubit_indices = []
        self._decomposed = False

    @property
    def angles(self):
        if len(self._angles) > 0:
            return self._angles
        else:
            print("not good 1")
            return [cmath.phase(phase) for phase in self._phases]

    @property
    def phases(self):
        if len(self._phases) > 0:
            return self._phases
        else:
            print("not good 2")
            return [cmath.exp(1j*angle) for angle in self._angles]

    def get_inverse(self):
        inv_phases = [p.conjugate() for p in self.phases]
        return DiagonalGate(phases = inv_phases)

    def decompose(self):
        assert self._decomposed == False
        # don't use classes
        from projectq.isometries import _DecomposeDiagonal
        self._decomposition = _DecomposeDiagonal(self.phases).get_decomposition()
        self._decomposed = True

    @property
    def decomposed(self):
        return self._decomposed

    @property
    def decomposition(self):
        return self._decomposition

    def __str__(self):
        return "D"
