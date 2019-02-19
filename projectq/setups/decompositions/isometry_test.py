from projectq import MainEngine
from projectq.ops import Measure, C, X, UniformlyControlledGate, Isometry
from projectq.backends import (CommandPrinter, ResourceCounter,
                               Simulator, IBMBackend)
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute, get_control_count
import projectq.setups.decompositions
from projectq.cengines import (InstructionFilter, AutoReplacer,
                               DecompositionRuleSet, DummyEngine)
from projectq.ops import (All, Command, X, Y, Z, T, H, Tdag, S, Sdag, Measure,
                          Allocate, Deallocate, NOT, Rx, Ry, Rz, Barrier,
                          Entangle)
from projectq.setups.decompositions import all_defined_decomposition_rules

import numpy as np
import math
import cmath
import copy
import random
import pytest

from . import isometry as iso


def normalize(v):
    return v/np.linalg.norm(v)


def test_state_prep():
    n = 5
    target_state = np.array([i for i in range(1 << n)])
    target_state = normalize(target_state)
    V = target_state
    V.shape = (1 << n, 1)

    eng = MainEngine()
    qureg = eng.allocate_qureg(n)
    eng.flush()

    cmd = Isometry(V).generate_command(qureg)
    iso._decompose_isometry(cmd)

    eng.flush()
    order, result = eng.backend.cheat()

    assert np.allclose(result, V[:, 0])
    All(Measure) | qureg


def test_2_columns():
    col_0 = normalize(np.array([1.j, 2., 3.j, 4., -5.j, 6., 1+7.j, 8.]))
    col_1 = normalize(np.array([8.j, 7., 6.j, 5., -4.j, 3., 1+2.j, 1.]))
    # must be orthogonal
    col_1 = normalize(col_1 - col_0*(np.vdot(col_0, col_1)))
    assert abs(np.vdot(col_0, col_1)) < 1e-10
    V = np.array([col_0, col_1]).transpose()

    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    eng.flush()
    cmd = Isometry(V).generate_command(qureg)
    iso._decompose_isometry(cmd)
    eng.flush()
    order, result = eng.backend.cheat()
    assert np.allclose(result, col_0)
    eng.flush()
    All(Measure) | qureg

    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    eng.flush()
    X | qureg[0]
    cmd = Isometry(V).generate_command(qureg)
    iso._decompose_isometry(cmd)
    eng.flush()
    order, result = eng.backend.cheat()
    assert np.allclose(result, col_1)
    eng.flush()
    All(Measure) | qureg


def create_initial_state(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 1:
            X | qureg[pos]


@pytest.mark.parametrize("index", range(8))
def test_full_unitary_3_qubits(index):
    n = 3
    N = 1 << n
    np.random.seed(7)
    re = np.random.rand(N, N)
    im = np.random.rand(N, N)
    M = re + 1j*im
    V, R = np.linalg.qr(M, mode='reduced')

    # must be orthogonal
    for i in range(N):
        for j in range(N):
            if i != j:
                assert abs(np.vdot(V[:, i], V[:, j])) < 1e-14

    eng = MainEngine()
    qureg = eng.allocate_qureg(n)
    eng.flush()
    create_initial_state(index, qureg)
    cmd = Isometry(V).generate_command(qureg)
    iso._decompose_isometry(cmd)
    eng.flush()
    order, result = eng.backend.cheat()
    assert np.allclose(result, V[:, index])
    All(Measure) | qureg
    eng.flush()


@pytest.mark.parametrize("index", range(8))
def test_full_permutation_matrix_3_qubits(index):
    n = 3
    N = 1 << n
    np.random.seed(7)
    V = np.zeros((N, N), dtype=complex)
    perm = np.random.permutation(N)
    for i in range(N):
        V[i, perm[i]] = 1.0

    eng = MainEngine()
    qureg = eng.allocate_qureg(n)
    eng.flush()
    create_initial_state(index, qureg)
    cmd = Isometry(V).generate_command(qureg)
    iso._decompose_isometry(cmd)
    eng.flush()
    order, result = eng.backend.cheat()
    print(order)
    _print_vec(V[:, index])
    _print_qureg(qureg)
    assert np.allclose(result, V[:, index])
    All(Measure) | qureg
    eng.flush()


# useful for debugging
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
