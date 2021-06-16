# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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
import pytest

from projectq.backends import Simulator
from projectq.backends._ionq._ionq_mapper import BoundedQubitMapper
from projectq.cengines import MainEngine, DummyEngine
from projectq.meta import LogicalQubitIDTag
from projectq.ops import AllocateQubitGate, Command, DeallocateQubitGate
from projectq.types import WeakQubitRef


def test_cannot_allocate_past_max():
    mapper = BoundedQubitMapper(1)
    engine = MainEngine(
        DummyEngine(),
        engine_list=[mapper],
        verbose=True,
    )
    engine.allocate_qubit()
    with pytest.raises(RuntimeError) as excinfo:
        engine.allocate_qubit()

    assert str(excinfo.value) == "Cannot allocate more than 1 qubits!"

    # Avoid double error reporting
    mapper.current_mapping = {0: 0, 1: 1}


def test_cannot_reallocate_same_qubit():
    engine = MainEngine(
        Simulator(),
        engine_list=[BoundedQubitMapper(1)],
        verbose=True,
    )
    qureg = engine.allocate_qubit()
    qubit = qureg[0]
    qubit_id = qubit.id
    with pytest.raises(RuntimeError) as excinfo:
        allocate_cmd = Command(
            engine=engine,
            gate=AllocateQubitGate(),
            qubits=([WeakQubitRef(engine=engine, idx=qubit_id)],),
            tags=[LogicalQubitIDTag(qubit_id)],
        )
        engine.send([allocate_cmd])

    assert str(excinfo.value) == "Qubit with id 0 has already been allocated!"


def test_cannot_deallocate_unknown_qubit():
    engine = MainEngine(
        Simulator(),
        engine_list=[BoundedQubitMapper(1)],
        verbose=True,
    )
    qureg = engine.allocate_qubit()
    with pytest.raises(RuntimeError) as excinfo:
        deallocate_cmd = Command(
            engine=engine,
            gate=DeallocateQubitGate(),
            qubits=([WeakQubitRef(engine=engine, idx=1)],),
            tags=[LogicalQubitIDTag(1)],
        )
        engine.send([deallocate_cmd])
    assert str(excinfo.value) == "Cannot deallocate a qubit that is not already allocated!"

    # but we can still deallocate an already allocated one
    engine.deallocate_qubit(qureg[0])
    del qureg
    del engine


def test_cannot_deallocate_same_qubit():
    mapper = BoundedQubitMapper(1)
    engine = MainEngine(
        Simulator(),
        engine_list=[mapper],
        verbose=True,
    )
    qureg = engine.allocate_qubit()
    qubit_id = qureg[0].id
    engine.deallocate_qubit(qureg[0])

    with pytest.raises(RuntimeError) as excinfo:
        deallocate_cmd = Command(
            engine=engine,
            gate=DeallocateQubitGate(),
            qubits=([WeakQubitRef(engine=engine, idx=qubit_id)],),
            tags=[LogicalQubitIDTag(qubit_id)],
        )
        engine.send([deallocate_cmd])

    assert str(excinfo.value) == "Cannot deallocate a qubit that is not already allocated!"


def test_flush_deallocates_all_qubits():
    mapper = BoundedQubitMapper(10)
    engine = MainEngine(
        Simulator(),
        engine_list=[mapper],
        verbose=True,
    )
    # needed to prevent GC from removing qubit refs
    qureg = engine.allocate_qureg(10)
    assert len(mapper.current_mapping.keys()) == 10
    assert len(engine.active_qubits) == 10
    engine.flush()
    # Should still be around after flush
    assert len(engine.active_qubits) == 10
    assert len(mapper.current_mapping.keys()) == 10

    # GC will clean things up
    del qureg
    assert len(engine.active_qubits) == 0
    assert len(mapper.current_mapping.keys()) == 0
