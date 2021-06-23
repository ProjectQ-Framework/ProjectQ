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
"""
Tests for projectq.backends._resource.py.
"""

import pytest

from projectq.cengines import DummyEngine, MainEngine, NotYetMeasuredError
from projectq.meta import LogicalQubitIDTag
from projectq.ops import All, Allocate, CNOT, Command, H, Measure, QFT, Rz, Rzz, X
from projectq.types import WeakQubitRef

from projectq.backends import ResourceCounter


class MockEngine(object):
    def is_available(self, cmd):
        return False


def test_resource_counter_isavailable():
    resource_counter = ResourceCounter()
    resource_counter.next_engine = MockEngine()
    assert not resource_counter.is_available("test")
    resource_counter.next_engine = None
    resource_counter.is_last_engine = True

    assert resource_counter.is_available("test")


def test_resource_counter_measurement():
    eng = MainEngine(ResourceCounter(), [])
    qb1 = WeakQubitRef(engine=eng, idx=1)
    qb2 = WeakQubitRef(engine=eng, idx=2)
    cmd0 = Command(engine=eng, gate=Allocate, qubits=([qb1],))
    cmd1 = Command(
        engine=eng,
        gate=Measure,
        qubits=([qb1],),
        controls=[],
        tags=[LogicalQubitIDTag(2)],
    )
    with pytest.raises(NotYetMeasuredError):
        int(qb1)
    with pytest.raises(NotYetMeasuredError):
        int(qb2)
    eng.send([cmd0, cmd1])
    eng.flush()
    with pytest.raises(NotYetMeasuredError):
        int(qb1)
    assert int(qb2) == 0


def test_resource_counter():
    resource_counter = ResourceCounter()
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend, [resource_counter])

    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    H | qubit1
    X | qubit2
    del qubit2

    qubit3 = eng.allocate_qubit()
    CNOT | (qubit1, qubit3)
    Rz(0.1) | qubit1
    Rz(0.3) | qubit1
    Rzz(0.5) | qubit1

    All(Measure) | qubit1 + qubit3

    with pytest.raises(NotYetMeasuredError):
        int(qubit1)

    assert resource_counter.max_width == 2
    assert resource_counter.depth_of_dag == 6

    str_repr = str(resource_counter)
    assert str_repr.count(" HGate : 1") == 1
    assert str_repr.count(" XGate : 1") == 1
    assert str_repr.count(" CXGate : 1") == 1
    assert str_repr.count(" Rz : 2") == 1
    assert str_repr.count(" AllocateQubitGate : 3") == 1
    assert str_repr.count(" DeallocateQubitGate : 1") == 1

    assert str_repr.count(" H : 1") == 1
    assert str_repr.count(" X : 1") == 1
    assert str_repr.count(" CX : 1") == 1
    assert str_repr.count(" Rz(0.1) : 1") == 1
    assert str_repr.count(" Rz(0.3) : 1") == 1
    assert str_repr.count(" Allocate : 3") == 1
    assert str_repr.count(" Deallocate : 1") == 1

    sent_gates = [cmd.gate for cmd in backend.received_commands]
    assert sent_gates.count(H) == 1
    assert sent_gates.count(X) == 2
    assert sent_gates.count(Measure) == 2


def test_resource_counter_str_when_empty():
    assert isinstance(str(ResourceCounter()), str)


def test_resource_counter_depth_of_dag():
    resource_counter = ResourceCounter()
    eng = MainEngine(resource_counter, [])
    assert resource_counter.depth_of_dag == 0
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    QFT | qb0 + qb1 + qb2
    assert resource_counter.depth_of_dag == 1
    H | qb0
    H | qb0
    assert resource_counter.depth_of_dag == 3
    CNOT | (qb0, qb1)
    X | qb1
    assert resource_counter.depth_of_dag == 5
    Measure | qb1
    Measure | qb1
    assert resource_counter.depth_of_dag == 7
    CNOT | (qb1, qb2)
    Measure | qb2
    assert resource_counter.depth_of_dag == 9
    qb1[0].__del__()
    qb2[0].__del__()
    assert resource_counter.depth_of_dag == 9
    qb0[0].__del__()
    assert resource_counter.depth_of_dag == 9
