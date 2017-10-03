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

"""Tests for projectq.cengines._ibmcnotmapper.py."""

import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import H, CNOT, X, Measure

from projectq.cengines import _ibmcnotmapper
from projectq.backends import IBMBackend


def test_ibmcnotmapper_is_available(monkeypatch):
    # Test that IBMCNOTMapper calls IBMBackend if gate is available.
    def mock_send(*args, **kwargs):
        return "Yes"
    monkeypatch.setattr(_ibmcnotmapper.IBMBackend, "is_available", mock_send)
    mapper = _ibmcnotmapper.IBMCNOTMapper()
    assert mapper.is_available("TestCommand") == "Yes"


def test_ibmcnotmapper_invalid_circuit():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_ibmcnotmapper.IBMCNOTMapper()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    qb3 = eng.allocate_qubit()
    CNOT | (qb1, qb2)
    CNOT | (qb0, qb1)
    CNOT | (qb0, qb2)
    CNOT | (qb3, qb1)
    with pytest.raises(Exception):
        CNOT | (qb3, qb2)
        eng.flush()


def test_ibmcnotmapper_valid_circuit1():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_ibmcnotmapper.IBMCNOTMapper()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    qb3 = eng.allocate_qubit()
    qb4 = eng.allocate_qubit()
    CNOT | (qb0, qb1)
    CNOT | (qb0, qb2)
    CNOT | (qb0, qb3)
    CNOT | (qb0, qb4)
    CNOT | (qb1, qb2)
    CNOT | (qb3, qb4)
    CNOT | (qb4, qb3)
    eng.flush()


def test_ibmcnotmapper_valid_circuit2():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_ibmcnotmapper.IBMCNOTMapper()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    qb3 = eng.allocate_qubit()
    qb4 = eng.allocate_qubit()
    CNOT | (qb3, qb1)
    CNOT | (qb3, qb2)
    CNOT | (qb3, qb0)
    CNOT | (qb3, qb4)
    CNOT | (qb1, qb2)
    CNOT | (qb0, qb4)
    CNOT | (qb2, qb1)
    eng.flush()


def test_ibmcnotmapper_valid_circuit2_ibmqx4():
    backend = DummyEngine(save_commands=True)

    class FakeIBMBackend(IBMBackend):
        pass

    fake = FakeIBMBackend(device='ibmqx4', use_hardware=True)
    fake.receive = backend.receive
    fake.is_available = backend.is_available
    backend.is_last_engine = True

    eng = MainEngine(backend=fake,
                     engine_list=[_ibmcnotmapper.IBMCNOTMapper()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    qb3 = eng.allocate_qubit()
    qb4 = eng.allocate_qubit()
    CNOT | (qb3, qb1)
    CNOT | (qb3, qb2)
    CNOT | (qb3, qb0)
    CNOT | (qb3, qb4)
    CNOT | (qb1, qb2)
    CNOT | (qb0, qb4)
    CNOT | (qb2, qb1)
    eng.flush()


def test_ibmcnotmapper_deviceexception():
    backend = DummyEngine(save_commands=True)

    class FakeIBMBackend(IBMBackend):
        pass

    fake = FakeIBMBackend(device='ibmqx5', use_hardware=True)
    fake.receive = backend.receive
    fake.is_available = backend.is_available
    backend.is_last_engine = True

    eng = MainEngine(backend=fake,
                     engine_list=[_ibmcnotmapper.IBMCNOTMapper()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    CNOT | (qb0, qb1)
    with pytest.raises(Exception):
        eng.flush()
    fake.device = 'ibmqx4'
    CNOT | (qb0, qb1)
    eng.flush()


def test_ibmcnotmapper_optimizeifpossible():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_ibmcnotmapper.IBMCNOTMapper()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    qb3 = eng.allocate_qubit()
    CNOT | (qb1, qb2)
    CNOT | (qb2, qb1)
    CNOT | (qb1, qb2)

    eng.flush()

    hadamard_count = 0
    for cmd in backend.received_commands:
        if cmd.gate == H:
            hadamard_count += 1
        if cmd.gate == X:
            assert cmd.qubits[0][0].id == qb2[0].id

    assert hadamard_count == 4
    backend.received_commands = []

    CNOT | (qb2, qb1)
    CNOT | (qb1, qb2)
    CNOT | (qb2, qb1)

    eng.flush()

    hadamard_count = 0
    for cmd in backend.received_commands:
        if cmd.gate == H:
            hadamard_count += 1
        if cmd.gate == X:
            assert cmd.qubits[0][0].id == qb1[0].id

    assert hadamard_count == 4
