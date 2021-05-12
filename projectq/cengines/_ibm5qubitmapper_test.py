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
"""Tests for projectq.cengines._ibm5qubitmapper.py."""

import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import H, CNOT, All

from projectq.cengines import _ibm5qubitmapper, SwapAndCNOTFlipper
from projectq.backends import IBMBackend


def test_ibm5qubitmapper_is_available(monkeypatch):
    # Test that IBM5QubitMapper calls IBMBackend if gate is available.
    def mock_send(*args, **kwargs):
        return "Yes"

    monkeypatch.setattr(_ibm5qubitmapper.IBMBackend, "is_available", mock_send)
    mapper = _ibm5qubitmapper.IBM5QubitMapper()
    assert mapper.is_available("TestCommand") == "Yes"


def test_ibm5qubitmapper_invalid_circuit():
    connectivity = set([(2, 1), (4, 2), (2, 0), (3, 2), (3, 4), (1, 0)])
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(
        backend=backend,
        engine_list=[_ibm5qubitmapper.IBM5QubitMapper(connections=connectivity)],
    )
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


def test_ibm5qubitmapper_valid_circuit1():
    connectivity = set([(2, 1), (4, 2), (2, 0), (3, 2), (3, 4), (1, 0)])
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(
        backend=backend,
        engine_list=[_ibm5qubitmapper.IBM5QubitMapper(connections=connectivity)],
    )
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


def test_ibm5qubitmapper_valid_circuit2():
    connectivity = set([(2, 1), (4, 2), (2, 0), (3, 2), (3, 4), (1, 0)])
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(
        backend=backend,
        engine_list=[_ibm5qubitmapper.IBM5QubitMapper(connections=connectivity)],
    )
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


def test_ibm5qubitmapper_valid_circuit2_ibmqx4():
    connectivity = set([(2, 1), (4, 2), (2, 0), (3, 2), (3, 4), (1, 0)])
    backend = DummyEngine(save_commands=True)

    class FakeIBMBackend(IBMBackend):
        pass

    fake = FakeIBMBackend(device='ibmqx4', use_hardware=True)
    fake.receive = backend.receive
    fake.is_available = backend.is_available
    backend.is_last_engine = True

    eng = MainEngine(
        backend=fake,
        engine_list=[_ibm5qubitmapper.IBM5QubitMapper(connections=connectivity)],
    )
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


def test_ibm5qubitmapper_optimizeifpossible():
    backend = DummyEngine(save_commands=True)
    connectivity = set([(2, 1), (4, 2), (2, 0), (3, 2), (3, 4), (1, 0)])
    eng = MainEngine(
        backend=backend,
        engine_list=[
            _ibm5qubitmapper.IBM5QubitMapper(connections=connectivity),
            SwapAndCNOTFlipper(connectivity),
        ],
    )
    qb0 = eng.allocate_qubit()  # noqa: F841
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    qb3 = eng.allocate_qubit()  # noqa: F841
    CNOT | (qb1, qb2)
    CNOT | (qb2, qb1)
    CNOT | (qb1, qb2)

    eng.flush()

    hadamard_count = 0
    for cmd in backend.received_commands:
        if cmd.gate == H:
            hadamard_count += 1

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

    assert hadamard_count == 4


def test_ibm5qubitmapper_toomanyqubits():
    backend = DummyEngine(save_commands=True)
    connectivity = set([(2, 1), (4, 2), (2, 0), (3, 2), (3, 4), (1, 0)])
    eng = MainEngine(
        backend=backend,
        engine_list=[
            _ibm5qubitmapper.IBM5QubitMapper(),
            SwapAndCNOTFlipper(connectivity),
        ],
    )
    qubits = eng.allocate_qureg(6)
    All(H) | qubits
    CNOT | (qubits[0], qubits[1])
    with pytest.raises(RuntimeError):
        eng.flush()
