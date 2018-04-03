from projectq import MainEngine
from projectq.ops import Measure, X, UniformlyControlledGate
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute

import numpy as np
import math
import cmath
import copy
import random
import pytest

from . import _isometry as iso

def normalize(v):
    return v/np.linalg.norm(v,2)

def test_ab():
    k = 0xdeadbeef
    assert iso.a(k, 16) == 0xdead
    assert iso.b(k, 16) == 0xbeef
    assert iso.a(k, 0) == k
    assert iso.b(k, 0) == 0

def test_to_zero_gate():
    U = iso.ToZeroGate()
    U.c0 = 2+1j
    U.c1 = 1-2j
    matrix = U.matrix
    vec = normalize(np.matrix([[U.c0],[U.c1]]))
    assert np.allclose(matrix.H * matrix, np.eye(2))
    assert np.allclose(matrix * vec, [[1], [0]])

def test_state_prep():
    target_state = np.array([1.j,2.,3.j,4.,-5.j,6.,1+7.j,8.])
    target_state = target_state/np.linalg.norm(target_state, 2)
    V = [target_state]

    eng = MainEngine(verbose = True)
    qureg = eng.allocate_qureg(3)
    eng.flush() # order

    iso.apply_isometry(V,qureg)
    eng.flush()

    order, result = eng.backend.cheat()
    print(order)

    print(target_state)
    print(result)
    assert np.allclose(result, target_state)

    Measure | qureg
    eng.flush()

@pytest.mark.parametrize("k,n", [(k,n) for n in range(1,5) for k in range(2**n)])
def test_disentangle(k, n):
    eng = MainEngine()
    qureg = eng.allocate_qureg(n)
    wf = np.array([0.]*k + [1.]*(2**n-k)) / math.sqrt(2**n-k)
    eng.flush()
    eng.backend.set_wavefunction(wf,qureg)
    for s in range(n):
        iso.disentangle(qureg, k, s)
    assert abs(iso.c(qureg, k)) == pytest.approx(1., 1e-10)
    Measure | qureg
    eng.flush()

def test_2_columns():
    col_0 = normalize(np.array([1.j,2.,3.j,4.,-5.j,6.,1+7.j,8.]))
    col_1 = normalize(np.array([8.j,7.,6.j,5.,-4.j,3.,1+2.j,1.]))
    # must be orthogonal
    col_1 = normalize(col_1 - col_0*(np.vdot(col_0,col_1)))
    assert abs(np.vdot(col_0,col_1)) < 1e-10
    V = [col_0, col_1]

    eng = MainEngine(verbose = True)
    qureg = eng.allocate_qureg(3)
    eng.flush() # order
    iso.apply_isometry(V,qureg)
    eng.flush()
    order, result = eng.backend.cheat()
    print(order)
    assert np.allclose(result, col_0)
    Measure | qureg
    eng.flush()

    eng = MainEngine(verbose = True)
    qureg = eng.allocate_qureg(3)
    eng.flush() # order
    X | qureg[0]
    iso.apply_isometry(V,qureg)
    eng.flush()
    order, result = eng.backend.cheat()
    print(order)
    assert np.allclose(result, col_1)
    Measure | qureg
    eng.flush()
