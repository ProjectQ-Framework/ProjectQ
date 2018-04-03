from projectq import MainEngine
from projectq.ops import Measure, X, Rz, UniformlyControlledGate
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute, Dagger

import numpy as np
import math
import cmath
import copy
import random

def print_qureg(qureg):
    eng = qureg.engine
    eng.flush()
    n = len(qureg)
    print("----")
    for i in range(2**n):
        bit_string = ("{0:0"+str(n)+"b}").format(i)
        print("{}: {}".format(bit_string,
            eng.backend.get_probability(bit_string[::-1],qureg)))

def a(k,s):
    return k >> s

def b(k,s):
    return k - (a(k,s) << s)

def c(qureg, l, k=0, s=0):
    eng = qureg.engine
    n = len(qureg)
    l = b(k,s) + l * 2**s #check
    assert 0 <= l and l <= 2**n - 1
    bit_string = ("{0:0"+str(n)+"b}").format(l)[::-1]
    eng.flush()
    return eng.backend.get_amplitude(bit_string,qureg)

# maps [c0,c1] to [1,0]
# use inverse matrix for state preparation
class ToZeroGate(BasicGate):
    @property
    def matrix(self):
        r = math.sqrt(abs(self.c0)**2 + abs(self.c1)**2)
        if r < 1e-15:
            return np.matrix([[1,0], [0,1]])
        m = np.matrix([[np.conj(self.c0), np.conj(self.c1)],
                       [       -self.c1,          self.c0 ]]) / r
        assert np.allclose(m.getH()*m, np.eye(2))
        return m

class ToOneGate(BasicGate):
    @property
    def matrix(self):
        r = math.sqrt(abs(self.c0)**2 + abs(self.c1)**2)
        if r < 1e-15:
            return np.matrix([[1,0], [0,1]])
        m = np.matrix([[       -self.c1,          self.c0 ],
                       [np.conj(self.c0), np.conj(self.c1)]]) / r
        assert np.allclose(m.getH()*m, np.eye(2))
        return m

def apply_isometry(V, user_qureg):
    """
    V is a list of column vectors
    """

    n = len(user_qureg)

    #assert...

    user_eng = user_qureg.engine

    # store colums in quregs for easy manipulation
    local_engines = []
    local_quregs = []
    for col in V:
        eng = MainEngine(verbose = True)
        qureg = eng.allocate_qureg(n)
        eng.flush()
        local_engines.append(eng)
        local_quregs.append(qureg)
        eng.backend.set_wavefunction(col, qureg)

    with Dagger(user_eng):
        for k in range(len(V)):
            _reduce_column(local_quregs[k], k, local_quregs[k+1:]+[user_qureg])


# compute G_k which reduces column k to |k>
# and apply it to following columns and the user_qureg
def _reduce_column(qureg, k, others):
    n = len(qureg)
    for s in range(n):
        disentangle(qureg, k, s, others)


tol = 1e-12
def disentangle(qureg, k, s, others=[]):
    n = len(qureg)
    assert n >= 1
    assert 0 <= k and k < 2**n
    assert 0 <= s and s < n

    eng = qureg.engine

    if b(k,s+1) != 0 and ((k >> s) & 1) == 0:
        if c(qureg, 2*a(k,s+1)+1, k, s) != 0:
            prepare_disentangle(qureg, k, s, others)
    print("aks: {}".format(a(k,s)))
    for l in range(a(k,s)):
        assert abs(c(qureg, l, k, s)) < tol

    if b(k,s+1) == 0:
        range_l = list(range(a(k,s+1), 2**(n-1-s)))
    else:
        range_l = list(range(a(k,s+1)+1, 2**(n-1-s)))

    if ((k >> s) & 1) == 0:
        gate = ToZeroGate
    else:
        gate = ToOneGate

    gates = []
    # fill with identities, might be improved upon
    if len(range_l) == 0:
        return

    for l in range(range_l[0]):
        gates.append(Rz(0))
    for l in range_l:
        U = gate()
        U.c0 = c(qureg, 2*l, k, s)
        U.c1 = c(qureg, 2*l + 1, k, s)
        gates.append(U)
    for q in [qureg]+others:
        UCG = UniformlyControlledGate(q[s+1:], gates)
        # maybe flush to avoid cluttering memory
        UCG | q[s]

def apply_mask(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 0:
            X | qureg[pos]

# Lemma 16
def prepare_disentangle(qureg, k, s, others):
    n = len(qureg)
    assert 1 <= k and k <= 2**n-1
    assert 0 <= s and s <= n-1
    assert (k >> s) & 1 == 0
    assert b(k,s+1) != 0

    eng = qureg.engine

    for l in range(a(k,s)):
        assert abs(c(qureg, l, k, s)) < tol

    U = ToZeroGate()
    U.c0 = c(qureg,2*a(k,s+1), k, s)
    U.c1 = c(qureg,2*a(k,s+1)+1, k, s)

    other_qubits = qureg[:s]+qureg[s+1:]
    # cut out s-th bit
    mask = b(k,s) + (a(k,s) << (s-1))

    for q in [qureg]+others:
        qubits = q[:s]+q[s+1:]
        e = q.engine
        with Compute(e):
            apply_mask(mask,qubits)
        with Control(e, qubits):
            U | q[s]
        Uncompute(e)

def state_preparation(user_eng, user_qureg, target_state):
    assert(is_power2(len(target_state)))
    n = int(round(np.log2(len(target_state))))
    assert(n == len(user_qureg))
    #leverage the simulator to compute the decomposition
    local_eng = MainEngine(verbose = True)
    local_qureg = local_eng.allocate_qureg(n)
    local_eng.flush()
    local_eng.backend.set_wavefunction(target_state, local_qureg)
    print("Want:")
    print_qureg(local_eng, local_qureg)

    #TODO measure known local qubits
    with Dagger(user_eng):
        for s in range(n):
            gates = []
            for l in range(2**(n-1-s)):
                U = ToZeroGate()
                U.c0 = c(local_qureg, 2*l, 0, s)
                U.c1 = c(local_qureg, 2*l+1, 0, s)
                gates.append(U)
            for qureg in [user_qureg,local_qureg]:
                UCG = UniformlyControlledGate(qureg[s+1::], gates)
                UCG | qureg[s]

    Measure | local_qureg
    local_eng.flush()
