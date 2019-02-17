import numpy as np
import cmath
import math
import pytest
from scipy.linalg import block_diag

from projectq import MainEngine
from projectq.ops import BasicGate, Ph, X, Y, Z, H, Measure, Rx, Ry, Rz, All
from projectq.meta import Dagger, Control

from . import _isometry as iso
from . import _uniformly_controlled_gate as ucg
from . import _diagonal_gate as diag


def create_initial_state(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 1:
            X | qureg[pos]


@pytest.mark.parametrize("index", range(8))
def test_matrix(index):
    A = np.asarray(H.matrix)
    B = np.asarray(Ry(7).matrix)
    A_B = np.array(block_diag(A, B))
    d = [cmath.exp(1j*i) for i in [1, 2, 3, 4]]
    D = np.diag(d)

    eng = MainEngine()
    qureg = eng.allocate_qureg(4)
    eng.flush()
    target = qureg[1]
    control = qureg[0]
    choice = qureg[2]

    create_initial_state(index, qureg)

    print(np.dot(A_B, D))
    V = iso.Isometry(np.dot(A_B, D))

    with Control(eng, control):
        V | (target, choice)

        with Dagger(eng):
            U = ucg.UniformlyControlledGate([H, Ry(7)])
            W = diag.DiagonalGate(phases=d)
            W | (target, choice)
            U | (choice, target)

    eng.flush()
    _, vec = eng.backend.cheat()
    print(vec)
    assert np.isclose(vec[index], 1)
