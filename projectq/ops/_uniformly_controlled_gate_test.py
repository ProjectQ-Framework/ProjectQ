import cmath
import copy
import numpy as np

from projectq import MainEngine
from projectq.ops import X, Y, Z, H, All, Measure
from projectq.meta import Dagger

from . import _uniformly_controlled_gate as ucg


def test_merge():
    gates1 = [X, Y, Z, H]
    gates2 = [H, Z, Y, X]
    U1 = ucg.UniformlyControlledGate(gates1)
    U2 = ucg.UniformlyControlledGate(gates2)
    U = U1.get_merged(U2)
    for i in range(len(gates1)):
        assert np.allclose(gates1[i].matrix*gates2[i].matrix,
                           U.gates[i].matrix)


def test_dagger():
    gates = [X, Y, Z, H]
    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    choice = qureg[1:]
    target = qureg[0]

    U = ucg.UniformlyControlledGate(gates)
    All(H) | qureg
    U | (choice, target)
    with Dagger(eng):
        U | (choice, target)
    All(H) | qureg

    eng.flush()
    qbit_to_bit_map, vec = eng.backend.cheat()
    assert np.isclose(vec[0], 1)

    Measure | qureg
