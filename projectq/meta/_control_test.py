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
from projectq.ops import Command, H, Rx, CtrlAll, Measure, All, X
from projectq.meta import DirtyQubitTag, ComputeTag, UncomputeTag, Compute, Uncompute

from projectq.meta import _control
from projectq.backends import Simulator

def test_control_engine_has_compute_tag():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    test_cmd0 = Command(eng, H, (qubit,))
    test_cmd1 = Command(eng, H, (qubit,))
    test_cmd2 = Command(eng, H, (qubit,))
    test_cmd0.tags = [DirtyQubitTag(), ComputeTag(), DirtyQubitTag()]
    test_cmd1.tags = [DirtyQubitTag(), UncomputeTag(), DirtyQubitTag()]
    test_cmd2.tags = [DirtyQubitTag()]
    control_eng = _control.ControlEngine("MockEng", ctrl_state=CtrlAll.One)
    assert control_eng._has_compute_uncompute_tag(test_cmd0)
    assert control_eng._has_compute_uncompute_tag(test_cmd1)
    assert not control_eng._has_compute_uncompute_tag(test_cmd2)


def test_control():
    backend =DummyEngine(save_commands=True)
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


def test_control_state():
    backend = Simulator()
    eng = MainEngine(backend=backend)

    qureg = eng.allocate_qureg(3)
    xreg = eng.allocate_qureg(3)
    X | qureg[1]
    with _control.Control(eng, qureg[0],'0'):
        with Compute(eng):
            X | xreg[0]

        X | xreg[1]
        Uncompute(eng)

    with _control.Control(eng, qureg[1:],'10'):
        X | xreg[2]
    All(Measure) | qureg
    All(Measure) | xreg
    eng.flush()

    assert int(xreg[0]) == 0
    assert int(xreg[1]) == 1
    assert int(xreg[2]) == 1
    assert int(qureg[0]) == 0
    assert int(qureg[1]) == 1
    assert int(qureg[2]) == 0

def test_control_state_contradiction():
    backend =DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qureg = eng.allocate_qureg(1)
    with pytest.raises(AssertionError):
        with _control.Control(eng, qureg[0],'0'):
            qubit = eng.allocate_qubit()
            with _control.Control(eng, qureg[0],'1'):
                H | qubit
    eng.flush()

