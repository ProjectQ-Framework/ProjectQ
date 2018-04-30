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

from projectq.isometries import (_SingleQubitGate,
                                 _decompose_uniformly_controlled_gate,
                                 _apply_uniformly_controlled_gate)

################################################################################

# #@pytest.mark.parametrize("n", range(1,15))
# #def test_numerical_error(n):
# for n in range(1,15):
#     random.seed(7)
#     gates = []
#     for i in range(1<<(n-1)):
#         a = Rx(random.uniform(0,2*np.pi)).matrix
#         b = Ry(random.uniform(0,2*np.pi)).matrix
#         c = Rx(random.uniform(0,2*np.pi)).matrix
#         gates.append(_SingleQubitGate(a*b*c))
#
#     decomposed_gates = _decompose_uniformly_controlled_gate(gates)[0]
#     errors = [g._error for g in decomposed_gates]
#     #print("Qubits: {} -----------".format(n))
#     print("Uni: {}".format(np.linalg.norm(errors, np.inf)))
#     #print("Dev: {}".format(np.sqrt(np.var(errors))))
#     #print("Max Error: {}".format(np.linalg.norm(errors, np.inf)))
#     #assert False
#     eng = MainEngine()
#     qureg = eng.allocate_qureg(n)
#     eng.flush() # makes sure the qubits are allocated in order
#     target = qureg[0]
#     choice_reg = qureg[1:]
#     UCG = UniformlyControlledGate(gates)
#     decomposition = UCG.decomposition
#     _apply_uniformly_controlled_gate(decomposition, target, choice_reg, False)
#     with Dagger(eng):
#         UCG | (choice_reg, target)
#     eng.flush()
#     qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
#     vec = np.array([final_wavefunction])
#     init = np.zeros_like(vec, dtype="complex")
#     init[0,0] = 1
#     #print(vec-init)
#     print(np.linalg.norm(vec-init, np.inf))

################################################################################


def test_full_decomposition_1_choice():
    eng = MainEngine()
    qureg = eng.allocate_qureg(2)
    eng.flush() # makes sure the qubits are allocated in order
    A = Rx(np.pi/5)
    B = Ry(np.pi/3)
    UCG = UniformlyControlledGate([A,B])
    cmd = UCG.generate_command(([qureg[1]], qureg[0]))
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
    UCG = UniformlyControlledGate([A,B,C,D])
    cmd = UCG.generate_command((qureg[1:], qureg[0]))
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
    UCG = UniformlyControlledGate([A,B,C,D])
    cmd = UCG.generate_command(([qureg[0],qureg[2]], qureg[1]))
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
        gates.append(_SingleQubitGate(a*b*c))

    choice = qureg[0:2]+qureg[3:4]
    target = qureg[2]
    ignore = qureg[4]
    print(len(choice))
    print(len(gates))
    UCG = UniformlyControlledGate(gates)
    cmd = UCG.generate_command((choice, target))
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


@pytest.mark.parametrize("init", range(16))
def test_diagonal_gate(init):
    eng = MainEngine()
    qureg = eng.allocate_qureg(4)
    eng.flush() # makes sure the qubits are allocated in order
    create_initial_state(init,qureg)

    random.seed(42)
    gates = []
    for i in range(8):
        a = Rx(random.uniform(0,2*np.pi)).matrix
        b = Ry(random.uniform(0,2*np.pi)).matrix
        c = Rx(random.uniform(0,2*np.pi)).matrix
        gates.append(_SingleQubitGate(a*b*c))

    choice = qureg[1:]
    target = qureg[0]

    UCG = UniformlyControlledGate(gates)
    cmd = UCG.generate_command((choice, target))
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    for k in range(8):
        with Compute(eng):
            apply_mask(k, choice)
        with Control(eng, choice):
            gates[k] | target
        Uncompute(eng)

    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction])
    k = 1 << len(choice)
    print(cmath.phase(vec.item(init)))
    assert np.isclose(vec.item(init), 1)
