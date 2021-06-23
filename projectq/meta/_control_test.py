# -*- coding: utf-8 -*-
#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
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
"""Tests for projectq.meta._control.py"""
import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import Command, H, Rx, CtrlAll, X, IncompatibleControlState
from projectq.meta import DirtyQubitTag, ComputeTag, UncomputeTag, Compute, Uncompute

from projectq.meta import _control
from projectq.types import WeakQubitRef


def test_canonical_representation():
    assert _control.canonical_ctrl_state(0, 0) == ''
    for num_qubits in range(4):
        assert _control.canonical_ctrl_state(0, num_qubits) == '0' * num_qubits

    num_qubits = 4
    for i in range(2 ** num_qubits):
        state = '{0:0b}'.format(i).zfill(num_qubits)
        assert _control.canonical_ctrl_state(i, num_qubits) == state[::-1]
        assert _control.canonical_ctrl_state(state, num_qubits) == state

    for num_qubits in range(10):
        assert _control.canonical_ctrl_state(CtrlAll.Zero, num_qubits) == '0' * num_qubits
        assert _control.canonical_ctrl_state(CtrlAll.One, num_qubits) == '1' * num_qubits

    with pytest.raises(TypeError):
        _control.canonical_ctrl_state(1.1, 2)

    with pytest.raises(ValueError):
        _control.canonical_ctrl_state('1', 2)

    with pytest.raises(ValueError):
        _control.canonical_ctrl_state('11111', 2)

    with pytest.raises(ValueError):
        _control.canonical_ctrl_state('1a', 2)

    with pytest.raises(ValueError):
        _control.canonical_ctrl_state(4, 2)


def test_has_negative_control():
    qubit0 = WeakQubitRef(None, 0)
    qubit1 = WeakQubitRef(None, 0)
    qubit2 = WeakQubitRef(None, 0)
    qubit3 = WeakQubitRef(None, 0)
    assert not _control.has_negative_control(Command(None, H, ([qubit0],)))
    assert not _control.has_negative_control(Command(None, H, ([qubit0],), [qubit1]))
    assert not _control.has_negative_control(Command(None, H, ([qubit0],), [qubit1], control_state=CtrlAll.One))
    assert _control.has_negative_control(Command(None, H, ([qubit0],), [qubit1], control_state=CtrlAll.Zero))
    assert _control.has_negative_control(
        Command(None, H, ([qubit0],), [qubit1, qubit2, qubit3], control_state=CtrlAll.Zero)
    )
    assert not _control.has_negative_control(
        Command(None, H, ([qubit0],), [qubit1, qubit2, qubit3], control_state='111')
    )
    assert _control.has_negative_control(Command(None, H, ([qubit0],), [qubit1, qubit2, qubit3], control_state='101'))


def test_control_engine_has_compute_tag():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    test_cmd0 = Command(eng, H, (qubit,))
    test_cmd1 = Command(eng, H, (qubit,))
    test_cmd2 = Command(eng, H, (qubit,))
    test_cmd0.tags = [DirtyQubitTag(), ComputeTag(), DirtyQubitTag()]
    test_cmd1.tags = [DirtyQubitTag(), UncomputeTag(), DirtyQubitTag()]
    test_cmd2.tags = [DirtyQubitTag()]
    assert _control._has_compute_uncompute_tag(test_cmd0)
    assert _control._has_compute_uncompute_tag(test_cmd1)
    assert not _control._has_compute_uncompute_tag(test_cmd2)


def test_control():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qureg = eng.allocate_qureg(2)
    with _control.Control(eng, qureg):
        qubit = eng.allocate_qubit()
        with Compute(eng):
            Rx(0.5) | qubit
        H | qubit
        Uncompute(eng)
    with _control.Control(eng, qureg[0]):
        H | qubit
    eng.flush()
    assert len(backend.received_commands) == 8
    assert len(backend.received_commands[0].control_qubits) == 0
    assert len(backend.received_commands[1].control_qubits) == 0
    assert len(backend.received_commands[2].control_qubits) == 0
    assert len(backend.received_commands[3].control_qubits) == 0
    assert len(backend.received_commands[4].control_qubits) == 2
    assert len(backend.received_commands[5].control_qubits) == 0
    assert len(backend.received_commands[6].control_qubits) == 1
    assert len(backend.received_commands[7].control_qubits) == 0
    assert backend.received_commands[4].control_qubits[0].id == qureg[0].id
    assert backend.received_commands[4].control_qubits[1].id == qureg[1].id
    assert backend.received_commands[6].control_qubits[0].id == qureg[0].id

    with pytest.raises(TypeError):
        _control.Control(eng, (qureg[0], qureg[1]))


def test_control_state():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])

    qureg = eng.allocate_qureg(3)
    xreg = eng.allocate_qureg(3)
    X | qureg[1]
    with _control.Control(eng, qureg[0], '0'):
        with Compute(eng):
            X | xreg[0]

        X | xreg[1]
        Uncompute(eng)

    with _control.Control(eng, qureg[1:], 2):
        X | xreg[2]
    eng.flush()

    assert len(backend.received_commands) == 6 + 5 + 1
    assert len(backend.received_commands[0].control_qubits) == 0
    assert len(backend.received_commands[1].control_qubits) == 0
    assert len(backend.received_commands[2].control_qubits) == 0
    assert len(backend.received_commands[3].control_qubits) == 0
    assert len(backend.received_commands[4].control_qubits) == 0
    assert len(backend.received_commands[5].control_qubits) == 0

    assert len(backend.received_commands[6].control_qubits) == 0
    assert len(backend.received_commands[7].control_qubits) == 0
    assert len(backend.received_commands[8].control_qubits) == 1
    assert len(backend.received_commands[9].control_qubits) == 0
    assert len(backend.received_commands[10].control_qubits) == 2

    assert len(backend.received_commands[11].control_qubits) == 0

    assert backend.received_commands[8].control_qubits[0].id == qureg[0].id
    assert backend.received_commands[8].control_state == '0'
    assert backend.received_commands[10].control_qubits[0].id == qureg[1].id
    assert backend.received_commands[10].control_qubits[1].id == qureg[2].id
    assert backend.received_commands[10].control_state == '01'

    assert _control.has_negative_control(backend.received_commands[8])
    assert _control.has_negative_control(backend.received_commands[10])


def test_control_state_contradiction():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qureg = eng.allocate_qureg(1)
    with pytest.raises(IncompatibleControlState):
        with _control.Control(eng, qureg[0], '0'):
            qubit = eng.allocate_qubit()
            with _control.Control(eng, qureg[0], '1'):
                H | qubit
    eng.flush()
