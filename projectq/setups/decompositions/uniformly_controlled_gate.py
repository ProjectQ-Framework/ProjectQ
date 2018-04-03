import math
import cmath
import numpy as np

from projectq.cengines import DecompositionRule
from projectq.ops import UniformlyControlledGate, BasicGate, H, CNOT, Rz

class _SingleQubitGate(BasicGate):
    def __init__(self, m):
        self._matrix = m
        self.interchangeable_qubit_indices = []

    @property
    def matrix(self):
        return self._matrix

    @matrix.setter
    def matrix(self, m):
        self._matrix = m

    def get_inverse(self):
        return _SingleQubitGate(self._matrix.getH())


# has amortized constant time
def _count_trailing_zero_bits(v):
    assert(v > 0)
    v = (v ^ (v - 1)) >> 1;
    c = 0
    while(v):
        v >>= 1;
        c += 1
    return c

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


def _decompose_uniformly_controlled_gate(cmd):
    gates = cmd.gate.gates

    # eliminate first choice qubit
    # for each value of the remaining k-1 choice qubits
    # we have a uniformly controlled gate with one choice qubit
    k = len(cmd.gate.choice_qubits)

    if k == 0:
        target = cmd.qubits[0]
        gates[0] | target
        return

    for level in range(k):
        intervals = 1<<level
        interval_length = 1<<(k-level)
        for interval in range(intervals):
            for i in range(interval_length//2):
                offset = interval*interval_length
                a = gates[offset + i].matrix
                b = gates[offset + interval_length//2 + i].matrix
                v,u,r = _basic_decomposition(a,b)

                # discard last diagonal gate
                if interval < intervals-1:
                    # merge with following UCG (not yet decomposed)
                    index = offset + interval_length + i
                    gates[index] = _SingleQubitGate(gates[index].matrix*r.getH())
                    index = offset + 3*interval_length//2 + i
                    gates[index] = _SingleQubitGate(gates[index].matrix*r)

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

    # apply circuit
    target = cmd.qubits[0]
    for i in range((1<<k) - 1):
        gates[i] | target
        control_index = _count_trailing_zero_bits(i+1)
        choice = cmd.gate.choice_qubits[control_index]
        CNOT | (choice, target)
        Rz(-np.pi/2) | choice
    gates[-1] | target

#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(UniformlyControlledGate, _decompose_uniformly_controlled_gate)
]
