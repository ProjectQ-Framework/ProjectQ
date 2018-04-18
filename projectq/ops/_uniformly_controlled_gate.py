from projectq.ops import get_inverse, BasicGate, CNOT, H, Rz

import numpy as np
import copy
import math
import cmath

class UniformlyControlledGate(BasicGate):
    """
    A set of 2^k single qubit gates controlled on k qubits.
    For each state of the choice qubits the corresponding
    gate is applied to the target qubit.

    .. code-block:: python

        UniforlmyControlledGate(gates) | (choice, qubit)
    """
    def __init__(self, gates):
        self._gates = copy.deepcopy(gates)
        self.interchangeable_qubit_indices = []
        self._diagonal, self._decomposed_gates = \
            _decompose_uniformly_controlled_gate(self._gates)

    # makes problems when using decomposition up to diagonals
    # def get_inverse(self):
    #     inverted_gates = [get_inverse(gate) for gate in self._gates]
    #     return UniformlyControlledGate(inverted_gates)

    def __str__(self):
        return "UCG"

    # makes projectq very unhappy (why?)
    # def __eq__(self, other):
    #     return False

    @property
    def decomposed_gates(self):
        return self._decomposed_gates

    @property
    def gates(self):
        return self._gates

    @property
    def diagonal(self):
        return self._diagonal

def _is_unitary(m):
    return np.allclose(m*m.H, np.eye(2))

# Helper class
class _SingleQubitGate(BasicGate):
    def __init__(self, m):
        assert _is_unitary(m)
        self._matrix = m
        self.interchangeable_qubit_indices = []

    @property
    def matrix(self):
        return self._matrix

    def get_inverse(self):
        return _SingleQubitGate(self._matrix.getH())

    def __str__(self):
        return "U[{:.2f} {:.2f}; {:.2f} {:.2f}]".format(
            abs(self.matrix.item((0,0))), abs(self.matrix.item((0,1))),
            abs(self.matrix.item((1,0))), abs(self.matrix.item((1,1))))

    # make sure optimizer behaves well
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return np.allclose(self.matrix, other.matrix)
        else:
            return False

# Decomposition taken from
# http://lib.tkk.fi/Diss/2007/isbn9789512290918/article3.pdf

# a == r.getH()*u*d*v
# b == r*u*d.getH()*v
def _basic_decomposition(a,b):
    x = a * b.getH()
    det = np.linalg.det(x)
    x11 = x.item((0,0))/cmath.sqrt(det)
    delta = np.pi / 2
    phi = cmath.phase(det)
    psi = cmath.phase(x11)
    r1 = cmath.exp(1j/2 * (delta - phi/2 - psi))
    r2 = cmath.exp(1j/2 * (delta - phi/2 + psi + np.pi))
    r = np.matrix([[r1,0],[0,r2]], dtype=complex)
    d,u = np.linalg.eig(r * x * r)
    # d must be diag(i,-i), otherwise reverse
    if(abs(d[0] + 1j) < 1e-10):
        d = np.flip(d,0)
        u = np.flip(u,1)
    d = np.diag(np.sqrt(d))
    v = d*u.getH()*r.getH()*b
    return v,u,r

# U = D*U'
def _decompose_uniformly_controlled_gate(uniform_gates):
    gates = copy.deepcopy(uniform_gates)

    assert len(gates) > 0
    k = int(round(np.log2(len(gates))))
    n = k+1
    diagonal = np.ones(1<<n, dtype=complex)

    if k == 0:
        return diagonal, gates

    # O(k*2^k)
    for level in range(k):
        intervals = 1<<level
        interval_length = 1<<(k-level)
        for interval in range(intervals):
            for i in range(interval_length//2):
                offset = interval*interval_length
                a = gates[offset + i].matrix
                b = gates[offset + interval_length//2 + i].matrix
                v,u,r = _basic_decomposition(a,b)

                if interval < intervals-1:
                    # merge with following UCG (not yet decomposed)
                    index = offset + interval_length + i
                    gates[index] = _SingleQubitGate(gates[index].matrix*r.getH())
                    index = offset + 3*interval_length//2 + i
                    gates[index] = _SingleQubitGate(gates[index].matrix*r)
                else:
                    # store trailing rotations in diagonal gate
                    for m in range(intervals):
                        off = m*interval_length
                        index =  2*i + 2*off
                        diagonal[index] *= r.getH().item((0,0))
                        diagonal[index+1] *= r.getH().item((1,1))
                        index = interval_length + 2*i + 2*off
                        diagonal[index] *= r.item((0,0))
                        diagonal[index+1] *= r.item((1,1))

                # store in place
                gates[offset + i] = _SingleQubitGate(v)
                gates[offset + interval_length//2 + i] = _SingleQubitGate(u)

    # decompose diagonal gates to CNOTs and merge single qubit gates
    h = H.matrix
    rz = Rz(-np.pi/2).matrix
    gates[0] = _SingleQubitGate(h*gates[0].matrix)
    for i in range(1,(1<<k) - 1):
        gates[i] = _SingleQubitGate(h*gates[i].matrix*rz*h)
    gates[-1] = _SingleQubitGate(gates[-1].matrix*rz*h)

    phase = cmath.exp(-1j*((1<<k)-1)*np.pi/4)
    return phase*diagonal, gates
