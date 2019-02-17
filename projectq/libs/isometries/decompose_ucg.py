from projectq.ops import H, Rz
from .single_qubit_gate import _SingleQubitGate

import numpy as np
import copy
import math
import cmath
import scipy.linalg


# Decomposition taken from
# http://lib.tkk.fi/Diss/2007/isbn9789512290918/article3.pdf
class _DecomposeUCG(object):
    def __init__(self, gates):
        assert len(gates) > 0

        self.gates = _unwrap(gates)
        self.k = int(round(np.log2(len(gates))))
        self.n = self.k+1
        self.diagonal = np.ones(1 << self.n, dtype=complex)

    # call only once
    def get_decomposition(self):
        if self.k == 0:
            return _wrap(self.gates), self.diagonal

        for level in range(self.k):
            intervals = 1 << level
            interval_length = 1 << (self.k-level)
            for interval in range(intervals):
                for i in range(interval_length//2):
                    r = self._apply_basic_decomposition(level, interval, i)
                    self._merge_controlled_rotations(level, interval, i, r)

        self._decompose_diagonals()
        return _wrap(self.gates), self.diagonal

    def _apply_basic_decomposition(self, level, interval, i):
        intervals = 1 << level
        interval_length = 1 << (self.k-level)
        offset = interval*interval_length

        a = self.gates[offset + i]
        b = self.gates[offset + interval_length//2 + i]
        v, u, r = _basic_decomposition(a, b)

        # store in place
        self.gates[offset + i] = v
        self.gates[offset + interval_length//2 + i] = u
        return r

    def _merge_controlled_rotations(self, level, interval, i, r):
        intervals = 1 << level
        interval_length = 1 << (self.k-level)
        offset = interval*interval_length

        if interval < intervals-1:
            # merge with following UCG (not yet decomposed)
            index = offset + interval_length + i
            self.gates[index] = self.gates[index]*r.getH()
            index = offset + 3*interval_length//2 + i
            self.gates[index] = self.gates[index]*r
        else:
            # store trailing rotations in diagonal gate
            for m in range(intervals):
                off = m*interval_length
                index = 2*i + 2*off
                self.diagonal[index] *= r.getH().item((0, 0))
                self.diagonal[index+1] *= r.getH().item((1, 1))
                index = interval_length + 2*i + 2*off
                self.diagonal[index] *= r.item((0, 0))
                self.diagonal[index+1] *= r.item((1, 1))

    def _decompose_diagonals(self):
        # decompose diagonal gates to CNOTs and merge single qubit gates
        h = H.matrix
        rz = Rz(-np.pi/2).matrix
        self.gates[0] = h*self.gates[0]
        for i in range(1, (1 << self.k) - 1):
            self.gates[i] = h*self.gates[i]*rz*h
        self.gates[-1] = self.gates[-1]*rz*h

        self.gates = [_closest_unitary(G) for G in self.gates]

        # merge Rz gates into final diagonal
        phi = cmath.exp(1j*np.pi/4)
        N = 1 << self.n
        if self.k >= 1:
            self.diagonal[:N//2] *= phi
            self.diagonal[N//2:] *= 1/phi
        if self.k >= 2:
            self.diagonal[:N//4] *= 1j
            self.diagonal[N//4:N//2] *= -1j
            self.diagonal[N//2:3*N//4] *= 1j
            self.diagonal[3*N//4:] *= -1j

        # global phase shift
        phase = cmath.exp(-1j*((1 << self.k)-1)*np.pi/4)
        if self.k >= 3:
            phase *= -1

        self.diagonal *= phase


def _closest_unitary(A):
    V, __, Wh = scipy.linalg.svd(A)
    U = np.matrix(V.dot(Wh))
    return U


def _wrap(gates):
    return [_SingleQubitGate(gate) for gate in gates]


def _unwrap(gates):
    return [gate.matrix for gate in gates]


# a == r.getH()*u*d*v
# b == r*u*d.getH()*v
def _basic_decomposition(a, b):
    x = a * b.getH()
    det = np.linalg.det(x)
    x11 = x.item((0, 0))/cmath.sqrt(det)
    delta = np.pi / 2
    phi = cmath.phase(det)
    psi = cmath.phase(x11)
    r1 = cmath.exp(1j/2 * (delta - phi/2 - psi))
    r2 = cmath.exp(1j/2 * (delta - phi/2 + psi + np.pi))
    r = np.matrix([[r1, 0], [0, r2]], dtype=complex)
    d, u = np.linalg.eig(r * x * r)
    # d must be diag(i,-i), otherwise reverse
    if(abs(d[0] + 1j) < 1e-10):
        d = np.flip(d, 0)
        u = np.flip(u, 1)
    d = np.diag(np.sqrt(d))
    v = d*u.getH()*r.getH()*b
    return v, u, r
