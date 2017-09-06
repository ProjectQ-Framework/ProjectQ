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

"""Tests for projectq.cengines._main.py."""

import pytest
from projectq.cengines import DummyEngine, LocalOptimizer
from projectq.backends import Simulator
from projectq.ops import H, AllocateQubitGate, FlushGate, DeallocateQubitGate

from projectq.cengines import _main


def test_main_engine_init():
    ceng1 = DummyEngine()
    ceng2 = DummyEngine()
    test_backend = DummyEngine()
    engine_list = [ceng1, ceng2]
    eng = _main.MainEngine(backend=test_backend, engine_list=engine_list)
    assert id(eng.next_engine) == id(ceng1)
    assert id(eng.main_engine) == id(eng)
    assert not eng.is_last_engine
    assert id(ceng1.next_engine) == id(ceng2)
    assert id(ceng1.main_engine) == id(eng)
    assert not ceng1.is_last_engine
    assert id(ceng2.next_engine) == id(test_backend)
    assert id(ceng2.main_engine) == id(eng)
    assert not ceng2.is_last_engine
    assert test_backend.is_last_engine
    assert id(test_backend.main_engine) == id(eng)
    assert not test_backend.next_engine
    assert len(engine_list) == 2


def test_main_engine_init_failure():
    with pytest.raises(_main.UnsupportedEngineError):
        eng = _main.MainEngine(backend=DummyEngine)
    with pytest.raises(_main.UnsupportedEngineError):
        eng = _main.MainEngine(engine_list=DummyEngine)
    with pytest.raises(_main.UnsupportedEngineError):
        eng = _main.MainEngine(engine_list=[DummyEngine(), DummyEngine])
    with pytest.raises(_main.UnsupportedEngineError):
        engine = DummyEngine()
        eng = _main.MainEngine(backend=engine, engine_list=[engine])


def test_main_engine_init_defaults():
    eng = _main.MainEngine()
    eng_list = []
    current_engine = eng.next_engine
    while not current_engine.is_last_engine:
        eng_list.append(current_engine)
        current_engine = current_engine.next_engine
    assert isinstance(eng_list[-1].next_engine, Simulator)
    from projectq.setups.default import default_engines
    for engine, expected in zip(eng_list, default_engines()):
        assert type(engine) == type(expected)


def test_main_engine_del():
    # need engine which caches commands to test that del calls flush
    caching_engine = LocalOptimizer(m=5)
    backend = DummyEngine(save_commands=True)
    eng = _main.MainEngine(backend=backend, engine_list=[caching_engine])
    qubit = eng.allocate_qubit()
    H | qubit
    assert len(backend.received_commands) == 0
    eng.__del__()
    # Allocate, H, and Flush Gate
    assert len(backend.received_commands) == 3


def test_main_engine_set_and_get_measurement_result():
    eng = _main.MainEngine()
    qubit0 = eng.allocate_qubit()
    qubit1 = eng.allocate_qubit()
    with pytest.raises(_main.NotYetMeasuredError):
        print(int(qubit0))
    eng.set_measurement_result(qubit0[0], True)
    eng.set_measurement_result(qubit1[0], False)
    assert int(qubit0)
    assert not int(qubit1)


def test_main_engine_get_qubit_id():
    # Test that ids are not identical
    eng = _main.MainEngine()
    ids = []
    for _ in range(10):
        ids.append(eng.get_new_qubit_id())
    assert len(set(ids)) == 10


def test_main_engine_flush():
    backend = DummyEngine(save_commands=True)
    eng = _main.MainEngine(backend=backend, engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    H | qubit
    eng.flush()
    assert len(backend.received_commands) == 3
    assert backend.received_commands[0].gate == AllocateQubitGate()
    assert backend.received_commands[1].gate == H
    assert backend.received_commands[2].gate == FlushGate()
    eng.flush(deallocate_qubits=True)
    assert len(backend.received_commands) == 5
    assert backend.received_commands[3].gate == DeallocateQubitGate()
    # keep the qubit alive until at least here
    assert len(str(qubit)) != 0
