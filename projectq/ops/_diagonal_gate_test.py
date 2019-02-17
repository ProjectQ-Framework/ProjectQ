import numpy as np
import cmath

from projectq import MainEngine
from projectq.ops import BasicGate, Ph, X, Y, Z, H, Measure, Rx, Ry, Rz, All
from projectq.meta import Dagger

from . import _diagonal_gate as diag


def test_merge():
    angles1 = list(range(8))
    angles2 = list(range(8))
    D1 = diag.DiagonalGate(angles=angles1)
    D2 = diag.DiagonalGate(angles=angles2)
    D3 = D1.get_merged(D2)
    for i in range(8):
        assert np.isclose(D3.phases[i], cmath.exp(1j*2*i))


def test_inverse():
    angles = list(range(8))
    D = diag.DiagonalGate(angles=angles)
    D_inv = D.get_inverse()
    for i in range(8):
        assert np.isclose(D_inv.phases[i], cmath.exp(-1j*i))


def test_dagger():
    eng = MainEngine()
    qureg = eng.allocate_qureg(3)

    angles = list(range(8))
    D = diag.DiagonalGate(angles=angles)
    All(H) | qureg
    D | qureg
    with Dagger(eng):
        D | qureg
    All(H) | qureg

    eng.flush()
    qbit_to_bit_map, vec = eng.backend.cheat()
    assert np.isclose(vec[0], 1)

    Measure | qureg
