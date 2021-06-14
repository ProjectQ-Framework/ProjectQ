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
"""Tests for projectq.setups.squaregrid."""

import pytest

import projectq
from projectq.cengines import DummyEngine, GridMapper
from projectq.libs.math import AddConstant
from projectq.ops import BasicGate, CNOT, H, Measure, Rx, Rz, Swap, X

import projectq.setups.grid as grid_setup


def test_mapper_present_and_correct_params():
    found = False
    mapper = None
    for engine in grid_setup.get_engine_list(num_rows=3, num_columns=2):
        if isinstance(engine, GridMapper):
            mapper = engine
            found = True
    assert found
    assert mapper.num_rows == 3
    assert mapper.num_columns == 2


def test_parameter_any():
    engine_list = grid_setup.get_engine_list(num_rows=3, num_columns=2, one_qubit_gates="any", two_qubit_gates="any")
    backend = DummyEngine(save_commands=True)
    eng = projectq.MainEngine(backend, engine_list)
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    gate = BasicGate()
    gate | (qubit1, qubit2)
    gate | qubit1
    eng.flush()
    print(len(backend.received_commands))
    assert backend.received_commands[2].gate == gate
    assert backend.received_commands[3].gate == gate


def test_restriction():
    engine_list = grid_setup.get_engine_list(
        num_rows=3,
        num_columns=2,
        one_qubit_gates=(Rz, H),
        two_qubit_gates=(CNOT, AddConstant),
    )
    backend = DummyEngine(save_commands=True)
    eng = projectq.MainEngine(backend, engine_list)
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()
    eng.flush()
    CNOT | (qubit1, qubit2)
    H | qubit1
    Rz(0.2) | qubit1
    Measure | qubit1
    Swap | (qubit1, qubit2)
    Rx(0.1) | (qubit1)
    AddConstant(1) | qubit1 + qubit2 + qubit3
    eng.flush()
    assert backend.received_commands[4].gate == X
    assert len(backend.received_commands[4].control_qubits) == 1
    assert backend.received_commands[5].gate == H
    assert backend.received_commands[6].gate == Rz(0.2)
    assert backend.received_commands[7].gate == Measure
    for cmd in backend.received_commands[7:]:
        assert cmd.gate != Swap
        assert not isinstance(cmd.gate, Rx)
        assert not isinstance(cmd.gate, AddConstant)


def test_wrong_init():
    with pytest.raises(TypeError):
        grid_setup.get_engine_list(num_rows=3, num_columns=2, one_qubit_gates="any", two_qubit_gates=(CNOT))
    with pytest.raises(TypeError):
        grid_setup.get_engine_list(num_rows=3, num_columns=2, one_qubit_gates="Any", two_qubit_gates=(CNOT,))
