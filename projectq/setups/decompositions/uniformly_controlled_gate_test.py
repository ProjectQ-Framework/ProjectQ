# Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"Tests for projectq.setups.decompositions.uniformly_controlled_gate."
import copy

import numpy as np
import pytest
import random
from scipy.linalg import block_diag

from projectq import MainEngine
from projectq.meta import Control, Dagger, Compute, Uncompute
from projectq.ops import H, Rx, Ry, Rz, X, UniformlyControlledGate

from . import uniformly_controlled_gate as ucg

from projectq.libs.isometries import _SingleQubitGate

from ._isometries_fixture import iso_decomp_chooser


def test_full_decomposition_1_choice(iso_decomp_chooser):
    eng = MainEngine()
    qureg = eng.allocate_qureg(2)
    eng.flush()
    A = Rx(np.pi / 5)
    B = Ry(np.pi / 3)
    UCG = UniformlyControlledGate([A, B])
    cmd = UCG.generate_command(([qureg[1]], qureg[0]))
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    vec = np.array([final_wavefunction]).T
    reference = np.matrix(block_diag(A.matrix, B.matrix))
    print(reference * vec)
    assert np.isclose((reference * vec).item(0), 1)


def test_full_decomposition_2_choice(iso_decomp_chooser):
    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    eng.flush()
    A = Rx(np.pi / 5)
    B = H
    C = Rz(np.pi / 5)
    D = Ry(np.pi / 3)
    UCG = UniformlyControlledGate([A, B, C, D])
    cmd = UCG.generate_command((qureg[1:], qureg[0]))
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    vec = np.array([final_wavefunction]).T
    reference = np.matrix(block_diag(A.matrix, B.matrix, C.matrix, D.matrix))
    print(reference * vec)
    assert np.isclose((reference * vec).item(0), 1)


def test_full_decomposition_2_choice_target_in_middle(iso_decomp_chooser):
    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    eng.flush()
    A = Rx(np.pi / 5)
    B = H
    C = Rz(np.pi / 5)
    D = Ry(np.pi / 3)
    UCG = UniformlyControlledGate([A, B, C, D])
    cmd = UCG.generate_command(([qureg[0], qureg[2]], qureg[1]))
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T
    vec[[1, 2]] = vec[[2, 1]]  # reorder basis
    vec[[5, 6]] = vec[[6, 5]]
    reference = np.matrix(block_diag(A.matrix, B.matrix, C.matrix, D.matrix))
    print(reference * vec)
    assert np.isclose((reference * vec).item(0), 1)


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


@pytest.mark.parametrize("init", range(10))
def test_full_decomposition_4_choice_target_in_middle(init, iso_decomp_chooser):
    n = 4
    eng = MainEngine()
    qureg = eng.allocate_qureg(n)
    eng.flush()  # makes sure the qubits are allocated in order
    create_initial_state(init, qureg)

    random.seed(42)
    gates = []
    for i in range(1 << (n - 1)):
        a = Rx(random.uniform(0, 2 * np.pi)).matrix
        b = Ry(random.uniform(0, 2 * np.pi)).matrix
        c = Rx(random.uniform(0, 2 * np.pi)).matrix
        gates.append(_SingleQubitGate(a * b * c))

    choice = qureg[1:]
    target = qureg[0]
    print(len(choice))
    print(len(gates))
    UCG = UniformlyControlledGate(gates)
    dec = UCG.decomposition

    cmd = UCG.generate_command((choice, target))
    with Dagger(eng):
        ucg._decompose_uniformly_controlled_gate(cmd)
    for k in range(1 << (n - 1)):
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
