# -*- coding: utf-8 -*-
#   Copyright 2017, 2021 ProjectQ-Framework (www.projectq.ch)
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
import sys
import weakref

import pytest

from projectq.cengines import DummyEngine, BasicMapperEngine, LocalOptimizer
from projectq.backends import Simulator
from projectq.ops import AllocateQubitGate, DeallocateQubitGate, FlushGate, H

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
        _main.MainEngine(backend=DummyEngine)
    with pytest.raises(_main.UnsupportedEngineError):
        _main.MainEngine(engine_list=DummyEngine)
    with pytest.raises(_main.UnsupportedEngineError):
        _main.MainEngine(engine_list=[DummyEngine(), DummyEngine])
    with pytest.raises(_main.UnsupportedEngineError):
        engine = DummyEngine()
        _main.MainEngine(backend=engine, engine_list=[engine])


def test_main_engine_init_defaults():
    eng = _main.MainEngine()
    eng_list = []
    current_engine = eng.next_engine
    while not current_engine.is_last_engine:
        eng_list.append(current_engine)
        current_engine = current_engine.next_engine
    assert isinstance(eng_list[-1].next_engine, Simulator)
    import projectq.setups.default

    default_engines = projectq.setups.default.get_engine_list()
    for engine, expected in zip(eng_list, default_engines):
        assert type(engine) == type(expected)


def test_main_engine_init_mapper():
    class LinearMapper(BasicMapperEngine):
        pass

    mapper1 = LinearMapper()
    mapper2 = BasicMapperEngine()
    engine_list1 = [mapper1]
    eng1 = _main.MainEngine(engine_list=engine_list1)
    assert eng1.mapper == mapper1
    engine_list2 = [mapper2]
    eng2 = _main.MainEngine(engine_list=engine_list2)
    assert eng2.mapper == mapper2
    engine_list3 = [mapper1, mapper2]
    with pytest.raises(_main.UnsupportedEngineError):
        _main.MainEngine(engine_list=engine_list3)


def test_main_engine_del():
    # Clear previous exceptions of other tests
    sys.last_type = None
    del sys.last_type
    # need engine which caches commands to test that del calls flush
    caching_engine = LocalOptimizer(cache_size=5)
    backend = DummyEngine(save_commands=True)
    eng = _main.MainEngine(backend=backend, engine_list=[caching_engine])
    qubit = eng.allocate_qubit()
    H | qubit
    assert len(backend.received_commands) == 0
    eng.__del__()
    # Allocate, H, Deallocate, and Flush Gate
    assert len(backend.received_commands) == 4


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


def test_main_engine_atexit_no_error():
    # Clear previous exceptions of other tests
    sys.last_type = None
    del sys.last_type
    backend = DummyEngine(save_commands=True)
    eng = _main.MainEngine(backend=backend, engine_list=[])
    qb = eng.allocate_qubit()  # noqa: F841
    eng._delfun(weakref.ref(eng))
    assert len(backend.received_commands) == 3
    assert backend.received_commands[0].gate == AllocateQubitGate()
    assert backend.received_commands[1].gate == DeallocateQubitGate()
    assert backend.received_commands[2].gate == FlushGate()


def test_main_engine_atexit_with_error():
    sys.last_type = "Something"
    backend = DummyEngine(save_commands=True)
    eng = _main.MainEngine(backend=backend, engine_list=[])
    qb = eng.allocate_qubit()  # noqa: F841
    eng._delfun(weakref.ref(eng))
    assert len(backend.received_commands) == 1
    assert backend.received_commands[0].gate == AllocateQubitGate()


def test_exceptions_are_forwarded():
    class ErrorEngine(DummyEngine):
        def receive(self, command_list):
            raise TypeError

    eng = _main.MainEngine(backend=ErrorEngine(), engine_list=[])
    with pytest.raises(TypeError):
        qb = eng.allocate_qubit()  # noqa: F841
    eng2 = _main.MainEngine(backend=ErrorEngine(), engine_list=[])
    with pytest.raises(TypeError):
        qb = eng2.allocate_qubit()  # noqa: F841

    # NB: avoid throwing exceptions when destroying the MainEngine
    eng.next_engine = DummyEngine()
    eng.next_engine.is_last_engine = True
    eng2.next_engine = DummyEngine()
    eng2.next_engine.is_last_engine = True
