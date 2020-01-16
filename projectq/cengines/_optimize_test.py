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

"""Tests for projectq.cengines._optimize.py."""

import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import (CNOT, H, Rx, Ry, AllocateQubitGate, X,
                          FastForwardingGate, ClassicalInstructionGate)

from projectq.cengines import _optimize


def test_local_optimizer_caching():
    local_optimizer = _optimize.LocalOptimizer(m=4)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    # Test that it caches for each qubit 3 gates
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    assert len(backend.received_commands) == 0
    H | qb0
    H | qb1
    CNOT | (qb0, qb1)
    assert len(backend.received_commands) == 0
    Rx(0.5) | qb0
    assert len(backend.received_commands) == 1
    assert backend.received_commands[0].gate == AllocateQubitGate()
    H | qb0
    assert len(backend.received_commands) == 2
    assert backend.received_commands[1].gate == H
    # Another gate on qb0 means it needs to send CNOT but clear pipeline of qb1
    Rx(0.6) | qb0
    for cmd in backend.received_commands:
        print(cmd)
    assert len(backend.received_commands) == 5
    assert backend.received_commands[2].gate == AllocateQubitGate()
    assert backend.received_commands[3].gate == H
    assert backend.received_commands[3].qubits[0][0].id == qb1[0].id
    assert backend.received_commands[4].gate == X
    assert backend.received_commands[4].control_qubits[0].id == qb0[0].id
    assert backend.received_commands[4].qubits[0][0].id == qb1[0].id


def test_local_optimizer_flush_gate():
    local_optimizer = _optimize.LocalOptimizer(m=4)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    # Test that it caches for each qubit 3 gates
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    H | qb0
    H | qb1
    assert len(backend.received_commands) == 0
    eng.flush()
    # Two allocate gates, two H gates and one flush gate
    assert len(backend.received_commands) == 5


def test_local_optimizer_fast_forwarding_gate():
    local_optimizer = _optimize.LocalOptimizer(m=4)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    # Test that FastForwardingGate (e.g. Deallocate) flushes that qb0 pipeline
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    H | qb0
    H | qb1
    assert len(backend.received_commands) == 0
    qb0[0].__del__()
    # As Deallocate gate is a FastForwardingGate, we should get gates of qb0
    assert len(backend.received_commands) == 3


def test_local_optimizer_cancel_inverse():
    local_optimizer = _optimize.LocalOptimizer(m=4)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    # Test that it cancels inverses (H, CNOT are self-inverse)
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    assert len(backend.received_commands) == 0
    for _ in range(11):
        H | qb0
    assert len(backend.received_commands) == 0
    for _ in range(11):
        CNOT | (qb0, qb1)
    assert len(backend.received_commands) == 0
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 2
    assert received_commands[0].gate == H
    assert received_commands[0].qubits[0][0].id == qb0[0].id
    assert received_commands[1].gate == X
    assert received_commands[1].qubits[0][0].id == qb1[0].id
    assert received_commands[1].control_qubits[0].id == qb0[0].id


def test_local_optimizer_mergeable_gates():
    local_optimizer = _optimize.LocalOptimizer(m=4)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    # Test that it merges mergeable gates such as Rx
    qb0 = eng.allocate_qubit()
    for _ in range(10):
        Rx(0.5) | qb0
    assert len(backend.received_commands) == 0
    eng.flush()
    # Expect allocate, one Rx gate, and flush gate
    assert len(backend.received_commands) == 3
    assert backend.received_commands[1].gate == Rx(10 * 0.5)
