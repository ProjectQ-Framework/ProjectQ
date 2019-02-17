from ._basics import BasicGate, NotInvertible, NotMergeable


import numpy as np
import cmath
import copy


def _is_power_of_2(k):
    if(k < 1):
        return False
    else:
        return ((k-1) & k) == 0


class DiagonalGate(BasicGate):
    """
    A diagonal gate is a unitary operation whose matrix representation
    in the computational basis is diagonal.

    Example:
        .. code-block:: python
            phases = [1j, -1j]
            D = DiagonalGate(phases=phases)
            D | qureg

    Attributes:
        phases: list of complex numbers with modulus one
        angles: alternatively the real angles can be provided

    Note:
        The k-th phase will be applied to the k-th basis vector in the
        usual lexicographic order of the basis vectors. The first qubit in
        the qureg is in the least significant position.
    """
    def __init__(self, phases=[], angles=[]):
        if len(angles) > 0 and len(phases) > 0:
            raise ValueError("Provide either a list of angles or of phases")

        if len(angles) > 0:
            if not _is_power_of_2(len(angles)):
                raise ValueError("Number of angles must be 2^k for k=0,1,2...")
            self._angles = copy.copy(angles)
            self._phases = []
        elif len(phases) > 0:
            if not _is_power_of_2(len(phases)):
                raise ValueError("Number of angles must be 2^k for k=0,1,2...")
            self._phases = copy.copy(phases)
            self._angles = []
        else:
            raise ValueError("Provide either a list of angles or of phases")
        self.interchangeable_qubit_indices = []
        self._decomposition = None

    @property
    def angles(self):
        if len(self._angles) == 0:
            self._angles = [cmath.phase(phase) for phase in self.phases]
        return self._angles

    @property
    def phases(self):
        if len(self._phases) == 0:
            self._phases = [cmath.exp(1j*angle) for angle in self.angles]
        return self._phases

    @property
    def decomposition(self):
        if self._decomposition is None:
            from projectq.libs.isometries import _decompose_diagonal_gate
            self._decomposition = _decompose_diagonal_gate(self.phases)
        return self._decomposition

    def get_inverse(self):
        if len(self._angles) > 0:
            return DiagonalGate(angles=[-a for a in self._angles])
        else:
            return DiagonalGate(phases=[p.conjugate() for p in self._phases])

    # TODO: can also be merged with uniformly controlled gates
    def get_merged(self, other):
        if isinstance(other, DiagonalGate):
            other_phases = other.phases
            if len(self.phases) != len(other_phases):
                raise NotMergeable("Cannot merge these two gates.")
            new_phases = [self.phases[i]*other_phases[i] for i
                          in range(len(other_phases))]
            return DiagonalGate(phases=new_phases)
        else:
            raise NotMergeable("Cannot merge these two gates.")

    def __eq__(self, other):
        """ Not implemented as this object is a floating point type."""
        return NotImplemented

    def __ne__(self, other):
        """ Not implemented as this object is a floating point type."""
        return NotImplemented

    def __str__(self):
        return "D"
