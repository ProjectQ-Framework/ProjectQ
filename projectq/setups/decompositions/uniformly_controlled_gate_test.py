"Tests for projectq.setups.decompositions.uniformly_controlled_gate."
import copy

import numpy as np
import math
import cmath
from scipy.linalg import block_diag
import pytest
import random

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (DummyEngine, AutoReplacer, InstructionFilter,
                               InstructionFilter, DecompositionRuleSet)
from projectq.meta import Control,Dagger,Compute,Uncompute
from projectq.ops import H,Rx,Ry,Rz,X,UniformlyControlledGate,CNOT

from . import uniformly_controlled_gate as ucg

def test_count_trailing_zero_bits():
    assert ucg._count_trailing_zero_bits(1) == 0
    assert ucg._count_trailing_zero_bits(2) == 1
    assert ucg._count_trailing_zero_bits(3) == 0
    assert ucg._count_trailing_zero_bits(4) == 2
    assert ucg._count_trailing_zero_bits(5) == 0
    assert ucg._count_trailing_zero_bits(6) == 1
    assert ucg._count_trailing_zero_bits(7) == 0

def test_basic_decomposition_1_choice():
    a = Rx(np.pi/5).matrix
    b = Ry(np.pi/3).matrix
    v,u,r = ucg._basic_decomposition(a,b)
    d = np.matrix([[np.exp(1j*np.pi/4),0],
                   [0,np.exp(-1j*np.pi/4)]])
    assert np.allclose(a, r.getH()*u*d*v)
    assert np.allclose(b, r*u*d.getH()*v)

    block = np.matrix(block_diag(a,b))
    inverse = np.matrix(block_diag(a,b)).getH()
    print(inverse*block)
    print(block*inverse)

    eng = MainEngine()
    qureg = eng.allocate_qureg(2)
    eng.flush() # makes sure the qubits are allocated in order

    U = ucg._SingleQubitGate(u)
    V = ucg._SingleQubitGate(v)

    target = qureg[0]
    choice = qureg[1]

    with Dagger(eng):
        V | target

        H | target
        CNOT | (choice, target)
        H | target

        # the minus signs are missing in the paper
        Rz(-np.pi/2) | target
        Rz(-np.pi/2) | choice

        U | target

    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T

    reference = np.matrix(block_diag(a,b))
    print(reference*vec)
    assert np.isclose(abs((reference*vec).item(0)), 1)

def test_full_decomposition_1_choice():
    eng = MainEngine()
    qureg = eng.allocate_qureg(2)
    eng.flush() # makes sure the qubits are allocated in order
    A = Rx(np.pi/5)
    B = Ry(np.pi/3)
    UCG = UniformlyControlledGate([qureg[1]], [A,B])
    cmd = UCG.generate_command(qureg[0])
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    vec = np.array([final_wavefunction]).T
    reference = np.matrix(block_diag(A.matrix,B.matrix))
    print(reference*vec)
    assert np.isclose(abs((reference*vec).item(0)), 1)

def test_full_decomposition_2_choice():
    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    eng.flush() # makes sure the qubits are allocated in order
    A = Rx(np.pi/5)
    B = H
    C = Rz(np.pi/5)
    D = Ry(np.pi/3)
    UCG = UniformlyControlledGate(qureg[1:], [A,B,C,D])
    cmd = UCG.generate_command(qureg[0])
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    vec = np.array([final_wavefunction]).T
    reference = np.matrix(block_diag(A.matrix,B.matrix,C.matrix,D.matrix))
    print(reference*vec)
    assert np.isclose(abs((reference*vec).item(0)), 1)

def test_full_decomposition_2_choice_target_in_middle():
    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    eng.flush() # makes sure the qubits are allocated in order
    A = Rx(np.pi/5)
    B = H
    C = Rz(np.pi/5)
    D = Ry(np.pi/3)
    UCG = UniformlyControlledGate([qureg[0],qureg[2]], [A,B,C,D])
    cmd = UCG.generate_command(qureg[1])
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T
    vec[[1,2]] = vec[[2,1]] #reorder basis
    vec[[5,6]] = vec[[6,5]]
    reference = np.matrix(block_diag(A.matrix,B.matrix,C.matrix,D.matrix))
    print(reference*vec)
    assert np.isclose(abs((reference*vec).item(0)), 1)

def apply_mask(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 0:
            X | qureg[pos]

def create_initial_state(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 1:
            X | qureg[pos]

@pytest.mark.parametrize("init", range(32))
def test_full_decomposition_4_choice_target_in_middle(init):
    eng = MainEngine()
    qureg = eng.allocate_qureg(5)
    eng.flush() # makes sure the qubits are allocated in order
    create_initial_state(init,qureg)

    random.seed(42)
    gates = []
    for i in range(8):
        a = Rx(random.uniform(0,2*np.pi)).matrix
        b = Ry(random.uniform(0,2*np.pi)).matrix
        c = Rx(random.uniform(0,2*np.pi)).matrix
        gates.append(ucg._SingleQubitGate(a*b*c))

    choice = qureg[0:2]+qureg[3:4]
    target = qureg[2]
    ignore = qureg[4]
    print(len(choice))
    print(len(gates))
    UCG = UniformlyControlledGate(choice, gates)
    cmd = UCG.generate_command(target)
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    for k in range(8):
        with Compute(eng):
            apply_mask(k, choice)
        with Control(eng, choice):
            gates[k] | target
        Uncompute(eng)

    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T
    print(vec)
    assert np.isclose(abs((vec).item(init)), 1)
