from . import decompose_isometry as iso
from . import decompose_ucg as ucg
from . import _SingleQubitGate

from projectq import MainEngine
from projectq.meta import Dagger
from projectq.ops import All, Rx, Ry, Rz, H, CNOT, Measure
from scipy.linalg import block_diag

import numpy as np


def test_is_available_cpp_isometry_decomposition():
    import projectq.libs.isometries.cppdec
    assert projectq.libs.isometries.cppdec


def test_ab():
    k = 0xdeadbeef
    assert iso.a(k, 16) == 0xdead
    assert iso.b(k, 16) == 0xbeef
    assert iso.a(k, 0) == k
    assert iso.b(k, 0) == 0


def normalize(v):
    return v/np.linalg.norm(v)


def test_to_zero_gate():
    U = iso.ToZeroGate()
    U.c0 = 2+1j
    U.c1 = 1-2j
    matrix = U.matrix
    vec = normalize(np.matrix([[U.c0], [U.c1]]))
    assert np.allclose(matrix.H * matrix, np.eye(2))
    assert np.allclose(matrix * vec, [[1], [0]])


def test_basic_decomposition_1_choice():
    a = Rx(np.pi/5).matrix
    b = Ry(np.pi/3).matrix
    v, u, r = ucg._basic_decomposition(a, b)
    d = np.matrix([[np.exp(1j*np.pi/4), 0],
                   [0, np.exp(-1j*np.pi/4)]])
    assert np.allclose(a, r.getH()*u*d*v)
    assert np.allclose(b, r*u*d.getH()*v)

    block = np.matrix(block_diag(a, b))
    inverse = np.matrix(block_diag(a, b)).getH()
    print(inverse*block)
    print(block*inverse)

    eng = MainEngine()
    qureg = eng.allocate_qureg(2)
    eng.flush()

    U = ucg._SingleQubitGate(u)
    V = ucg._SingleQubitGate(v)

    target = qureg[0]
    choice = qureg[1]

    with Dagger(eng):
        V | target

        H | target
        CNOT | (choice, target)
        H | target

        Rz(-np.pi/2) | target
        Rz(-np.pi/2) | choice

        U | target

    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T

    reference = np.matrix(block_diag(a, b))
    print(reference*vec)
    assert np.isclose(abs((reference*vec).item(0)), 1)

    All(Measure) | qureg
    eng.flush()
