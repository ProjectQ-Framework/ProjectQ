from projectq import MainEngine
from projectq.ops import Measure, X, DiagonalGate, Rz, CNOT
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute, Dagger

import numpy as np
import math
import cmath
import copy
import random
import pytest

from . import diagonal_gate as diag

class _SingleDiagonalGate(BasicGate):
    def __init__(self, angles):
        a,b = cmath.exp(1j*angles[0]), cmath.exp(1j*angles[1])
        self._matrix = np.matrix([[a,0],[0,b]])
        self.interchangeable_qubit_indices = []

    @property
    def matrix(self):
        return self._matrix

def test_decompose_rotation_no_control():
    angles = [7.4, -10.3]
    U1 = _SingleDiagonalGate(angles).matrix
    phase, theta = diag._basic_decomposition(angles[0], angles[1])
    U2 = cmath.exp(1j*phase) * Rz(theta).matrix

    assert np.allclose(U1, U2)

def create_initial_state(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 1:
            X | qureg[pos]

@pytest.mark.parametrize("init", range(4))
def test_decompose_single_control(init):
    eng = MainEngine(verbose = True)
    qureg = eng.allocate_qureg(2)
    eng.flush()
    create_initial_state(init, qureg)

    target = qureg[0]
    control = qureg[1]

    angles = [-3.5, 20.3]
    phi1, phi2 = diag._decompose_rotation(angles[0], angles[1])

    with Control(eng, control):
        Rz(angles[1]) | target
    with Compute(eng):
        X | control
    with Control(eng, control):
        Rz(angles[0]) | target
    Uncompute(eng)

    with Dagger(eng):
        Rz(phi1) | target
        CNOT | (control, target)
        Rz(phi2) | target
        CNOT | (control, target)

    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T
    print(vec)

    assert np.isclose(vec.item(init), 1)

@pytest.mark.parametrize("init", range(4))
def test_apply_uniformly_controlled_rotation_1(init):
    eng = MainEngine(verbose = True)
    qureg = eng.allocate_qureg(2)
    eng.flush()
    create_initial_state(init, qureg)

    target = qureg[0]
    control = qureg[1]

    angles = [-3.5, 20.3]

    with Control(eng, control):
        Rz(angles[1]) | target
    with Compute(eng):
        X | control
    with Control(eng, control):
        Rz(angles[0]) | target
    Uncompute(eng)

    with Dagger(eng):
        diag._apply_uniformly_controlled_rotation(angles, [target, control])

    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T
    print(vec)

    assert np.isclose(vec.item(init), 1)

def apply_mask(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 0:
            X | qureg[pos]

@pytest.mark.parametrize("init", range(16))
def test_apply_uniformly_controlled_rotation_3(init):
    eng = MainEngine(verbose = True)
    qureg = eng.allocate_qureg(4)
    eng.flush()
    create_initial_state(init, qureg)

    target = qureg[0]
    control = qureg[1:]

    angles = list(range(1,9))

    with Dagger(eng):
        for i in range(8):
            with Compute(eng):
                apply_mask(i, control)
            with Control(eng, control):
                Rz(angles[i]) | target
            Uncompute(eng)

    diag._apply_uniformly_controlled_rotation(angles, [target]+control)


    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T
    print(vec)

    print(cmath.phase(vec.item(init)))
    assert np.isclose(vec.item(init), 1)

@pytest.mark.parametrize("init", range(16))
def test_decompose_diagonal_gate(init):
    angles = list(range(1,9))
    eng = MainEngine(verbose = True)
    qureg = eng.allocate_qureg(4)
    eng.flush()
    create_initial_state(init, qureg)

    D = DiagonalGate(angles=angles)
    cmd = D.generate_command(qureg[1:])
    diag._decompose_diagonal_gate(cmd)

    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T

    print(vec.item(init) - cmath.exp(1j*(((init>>1)&7)+1)))
    assert np.isclose(vec.item(init), cmath.exp(1j*(((init>>1)&7)+1)))

@pytest.mark.parametrize("init", range(4))
def test_decompose_diagonal_gate_2(init):
    angles = [0, np.pi/2, np.pi/4, -np.pi/4]
    eng = MainEngine(verbose = True)
    qureg = eng.allocate_qureg(2)
    eng.flush()
    create_initial_state(init, qureg)

    D = DiagonalGate(angles=angles)
    cmd = D.generate_command(qureg)
    diag._decompose_diagonal_gate(cmd)

    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T

    print(vec.item(init) - cmath.exp(1j*angles[init]))
    assert False
