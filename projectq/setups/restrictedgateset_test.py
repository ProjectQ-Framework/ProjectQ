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
"""Tests for projectq.setups.restrictedgateset."""

import pytest

import projectq
from projectq.cengines import DummyEngine
from projectq.libs.math import AddConstant, AddConstantModN, MultiplyByConstantModN
from projectq.ops import (
    BasicGate,
    CNOT,
    CRz,
    H,
    Measure,
    QFT,
    QubitOperator,
    Rx,
    Rz,
    Swap,
    TimeEvolution,
    Toffoli,
    X,
)
from projectq.meta import Control

import projectq.setups.restrictedgateset as restrictedgateset


def test_parameter_any():
    engine_list = restrictedgateset.get_engine_list(one_qubit_gates="any", two_qubit_gates="any")
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
    engine_list = restrictedgateset.get_engine_list(
        one_qubit_gates=(Rz, H),
        two_qubit_gates=(CNOT, AddConstant, Swap),
        other_gates=(Toffoli, AddConstantModN, MultiplyByConstantModN(2, 8)),
    )
    backend = DummyEngine(save_commands=True)
    eng = projectq.MainEngine(backend, engine_list, verbose=True)
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()
    eng.flush()
    CNOT | (qubit1, qubit2)
    H | qubit1
    with Control(eng, qubit2):
        Rz(0.2) | qubit1
    Measure | qubit1
    AddConstant(1) | (qubit1 + qubit2)
    AddConstantModN(1, 9) | (qubit1 + qubit2 + qubit3)
    Toffoli | (qubit1 + qubit2, qubit3)
    Swap | (qubit1, qubit2)
    MultiplyByConstantModN(2, 8) | qubit1 + qubit2 + qubit3
    TimeEvolution(0.5, QubitOperator("X0 Y1 Z2")) | qubit1 + qubit2 + qubit3
    QFT | qubit1 + qubit2 + qubit3
    Rx(0.1) | (qubit1)
    MultiplyByConstantModN(2, 9) | qubit1 + qubit2 + qubit3
    eng.flush()
    assert backend.received_commands[4].gate == X
    assert len(backend.received_commands[4].control_qubits) == 1
    assert backend.received_commands[5].gate == H
    assert backend.received_commands[6].gate == Rz(0.1)
    assert backend.received_commands[10].gate == Measure
    assert backend.received_commands[11].gate == AddConstant(1)
    assert backend.received_commands[12].gate == AddConstantModN(1, 9)
    assert backend.received_commands[13].gate == X
    assert len(backend.received_commands[13].control_qubits) == 2
    assert backend.received_commands[14].gate == Swap
    assert backend.received_commands[15].gate == MultiplyByConstantModN(2, 8)
    for cmd in backend.received_commands[16:]:
        assert cmd.gate != QFT
        assert not isinstance(cmd.gate, Rx)
        assert not isinstance(cmd.gate, MultiplyByConstantModN)
        assert not isinstance(cmd.gate, TimeEvolution)


def test_wrong_init():
    with pytest.raises(TypeError):
        restrictedgateset.get_engine_list(two_qubit_gates=(CNOT))
    with pytest.raises(TypeError):
        restrictedgateset.get_engine_list(one_qubit_gates="Any")
    with pytest.raises(TypeError):
        restrictedgateset.get_engine_list(other_gates="any")
    with pytest.raises(TypeError):
        restrictedgateset.get_engine_list(one_qubit_gates=(CRz,))
    with pytest.raises(TypeError):
        restrictedgateset.get_engine_list(two_qubit_gates=(CRz,))
    with pytest.raises(TypeError):
        restrictedgateset.get_engine_list(other_gates=(CRz,))
