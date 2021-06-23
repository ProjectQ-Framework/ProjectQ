# -*- coding: utf-8 -*-
#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Tests for projectq.setups.decompositions.stateprep2cnot."""

import cmath
from copy import deepcopy
import math

import numpy as np
import pytest

import projectq
from projectq.ops import All, Command, Measure, Ry, Rz, StatePreparation, Ph
from projectq.setups import restrictedgateset
from projectq.types import WeakQubitRef

import projectq.setups.decompositions.stateprep2cnot as stateprep2cnot


def test_invalid_arguments():
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd = Command(None, StatePreparation([0, 1j]), qubits=([qb0], [qb1]))
    with pytest.raises(ValueError):
        stateprep2cnot._decompose_state_preparation(cmd)


def test_wrong_final_state():
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd = Command(None, StatePreparation([0, 1j]), qubits=([qb0, qb1],))
    with pytest.raises(ValueError):
        stateprep2cnot._decompose_state_preparation(cmd)
    cmd2 = Command(None, StatePreparation([0, 0.999j]), qubits=([qb0],))
    with pytest.raises(ValueError):
        stateprep2cnot._decompose_state_preparation(cmd2)


@pytest.mark.parametrize("zeros", [True, False])
@pytest.mark.parametrize("n_qubits", [1, 2, 3, 4])
def test_state_preparation(n_qubits, zeros):
    engine_list = restrictedgateset.get_engine_list(one_qubit_gates=(Ry, Rz, Ph))
    eng = projectq.MainEngine(engine_list=engine_list)
    qureg = eng.allocate_qureg(n_qubits)
    eng.flush()

    f_state = [0.2 + 0.1 * x * cmath.exp(0.1j + 0.2j * x) for x in range(2 ** n_qubits)]
    if zeros:
        for i in range(2 ** (n_qubits - 1)):
            f_state[i] = 0
    norm = 0
    for amplitude in f_state:
        norm += abs(amplitude) ** 2
    f_state = [x / math.sqrt(norm) for x in f_state]

    StatePreparation(f_state) | qureg
    eng.flush()

    wavefunction = deepcopy(eng.backend.cheat()[1])
    # Test that simulator hasn't reordered wavefunction
    mapping = eng.backend.cheat()[0]
    for key in mapping:
        assert mapping[key] == key
    All(Measure) | qureg
    eng.flush()
    assert np.allclose(wavefunction, f_state, rtol=1e-10, atol=1e-10)
