from projectq import MainEngine
from projectq.ops import Measure, X, Rz, UniformlyControlledGate, DiagonalGate
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute, Dagger

import numpy as np
import math
import cmath
import copy
import random


class _DecomposeIsometry(object):
    def __init__(self, cols, threshold):
        self._cols = cols
        self._threshold = threshold

    def get_decomposition(self):
        n = int(round(np.log2(len(self._cols[0]))))

        # store colums in quregs for easy manipulation
        local_engines = []
        local_quregs = []
        for col in self._cols:
            eng = MainEngine()
            qureg = eng.allocate_qureg(n)
            eng.flush()
            local_engines.append(eng)
            local_quregs.append(qureg)
            eng.backend.set_wavefunction(col, qureg)

        reductions = []
        for k in range(len(self._cols)):
            reductions.append(_reduce_column(k, local_quregs, self._threshold))

        phases = [1./c(local_quregs[k], k) for k in range(len(self._cols))]
        phases = phases + [1.0]*((1 << n) - len(phases))
        diagonal = DiagonalGate(phases=phases)

        return reductions, diagonal.decomposition


def _print_qureg(qureg):
    eng = qureg.engine
    eng.flush()
    bla, vec = eng.backend.cheat()
    for i in range(len(vec)):
        print("{}: {:.3f}, {}".format(i, abs(vec[i]), cmath.phase(vec[i])))
    print("-")


def _print_vec(vec):
    for i in range(len(vec)):
        print("{}: {:.3f}, {}".format(i, abs(vec[i]), cmath.phase(vec[i])))
    print("-")


def _pretty(num):
    if abs(num) < 1e-10:
        return "0"
    return "*"


def _debug(local_quregs):
    matrix = []
    for i in range(len(local_quregs)):
        eng = local_quregs[i].engine
        eng.flush()
        bla, vec = eng.backend.cheat()
        matrix.append(vec)

    N = len(matrix)
    for i in range(len(matrix[0])):
        for j in range(N):
            print(_pretty(matrix[j][i]), end=' ', flush=True)
        print('')
    print('-')


def a(k, s):
    return k >> s


def b(k, s):
    return k - (a(k, s) << s)


def c(qureg, t, k=0, s=0):
    eng = qureg.engine
    n = len(qureg)
    t = b(k, s) + t * 2**s
    assert 0 <= t and t <= 2**n - 1
    bit_string = ("{0:0"+str(n)+"b}").format(t)[::-1]
    eng.flush()
    return eng.backend.get_amplitude(bit_string, qureg)


# maps [c0,c1] to [1,0]
class ToZeroGate(BasicGate):
    @property
    def matrix(self):
        r = math.sqrt(abs(self.c0)**2 + abs(self.c1)**2)
        if r < 1e-15:
            return np.matrix([[1, 0], [0, 1]])
        m = np.matrix([[np.conj(self.c0), np.conj(self.c1)],
                      [-self.c1, self.c0]]) / r
        assert np.allclose(m.getH()*m, np.eye(2))
        return m

    def __str__(self):
        return "TZG"


class ToOneGate(BasicGate):
    @property
    def matrix(self):
        r = math.sqrt(abs(self.c0)**2 + abs(self.c1)**2)
        if r < 1e-15:
            return np.matrix([[1, 0], [0, 1]])
        m = np.matrix([[-self.c1, self.c0],
                       [np.conj(self.c0), np.conj(self.c1)]]) / r
        assert np.allclose(m.getH()*m, np.eye(2))
        return m

    def __str__(self):
        return "TOG"


# compute G_k which reduces column k to |k>
# and apply it to following columns and the user_qureg
def _reduce_column(k, local_quregs, threshold):
    n = len(local_quregs[0])
    reduction = []
    for s in range(n):
        reduction.append(_disentangle(k, s, local_quregs, threshold))
    return reduction


tol = 1e-12


def _disentangle(k, s, local_quregs, threshold):
    qureg = local_quregs[k]
    n = len(qureg)

    assert n >= 1
    assert 0 <= k and k < 2**n
    assert 0 <= s and s < n

    mcg_decomposition = _prepare_disentangle(k, s, local_quregs, threshold)

    for l in range(a(k, s)):
        assert abs(c(qureg, l, k, s)) < tol

    if b(k, s+1) == 0:
        range_l = list(range(a(k, s+1), 2**(n-1-s)))
    else:
        range_l = list(range(a(k, s+1)+1, 2**(n-1-s)))

    if ((k >> s) & 1) == 0:
        gate = ToZeroGate
    else:
        gate = ToOneGate

    gates = []
    if len(range_l) == 0:
        return [mcg_decomposition, gates]
    for l in range(range_l[0]):
        gates.append(Rz(0))
    for l in range_l:
        U = gate()
        U.c0 = c(qureg, 2*l, k, s)
        U.c1 = c(qureg, 2*l + 1, k, s)
        gates.append(U)
    UCG = UniformlyControlledGate(gates, up_to_diagonal=True)
    for q in local_quregs:
        UCG | (q[s+1:], q[s])

    return mcg_decomposition, UCG.decomposition


def _apply_mask(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 0:
            X | qureg[pos]


def _get_one_bits(qureg, mask):
    res = []
    for i in range(len(qureg)):
        if mask & (1 << i):
            res.append(qureg[i])
    return res


def _count_one_bits(mask):
    cnt = 0
    while mask:
        if mask & 1:
            cnt += 1
        mask >>= 1
    return cnt


def _prepare_disentangle(k, s, local_quregs, threshold):
    qureg = local_quregs[k]
    n = len(qureg)

    if b(k, s+1) == 0 or ((k >> s) & 1) != 0:
        return [Rz(0)], None
    if abs(c(qureg, 2*a(k, s+1)+1, k, s)) <= tol:
        return [Rz(0)], None

    assert 1 <= k and k <= 2**n-1
    assert 0 <= s and s <= n-1
    assert (k >> s) & 1 == 0
    assert b(k, s+1) != 0

    for l in range(a(k, s)):
        assert abs(c(qureg, l, k, s)) < tol

    U = ToZeroGate()
    U.c0 = c(qureg, 2*a(k, s+1), k, s)
    U.c1 = c(qureg, 2*a(k, s+1)+1, k, s)

    mask = k

    ctrl = _count_one_bits(mask)
    if ctrl > 0 and ctrl < threshold:
        gates = [Rz(0)] * ((1 << ctrl)-1) + [U]
        UCG = UniformlyControlledGate(gates, up_to_diagonal=True)
        for q in local_quregs:
            controls = _get_one_bits(q, mask)
            UCG | (controls, q[s])
        return UCG.decomposition

    for q in local_quregs:
        qubits = _get_one_bits(q, mask)
        e = q.engine
        if len(qubits) == 0:
            U | q[s]
        else:
            with Control(e, qubits):
                U | q[s]

    return [U], None
