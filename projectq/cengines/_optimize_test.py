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
import math
from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import (CNOT, H, Rx, Ry, Rz, Rxx, Ryy, Rzz, Measure, AllocateQubitGate, X,
                          FastForwardingGate, ClassicalInstructionGate, XGate, Ph, X, SqrtX)
from projectq.setups import restrictedgateset, trapped_ion_decomposer

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

def test_local_optimizer_cancel_separated_inverse():
    """ Tests the situation where the next command on
    this qubit is an inverse command, but another qubit 
    involved is separated from the inverse by only commutable 
    gates. The two commands should cancel. """
    local_optimizer = _optimize.LocalOptimizer(m=5)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    assert len(backend.received_commands) == 0
    Rxx(math.pi) | (qb0, qb1)
    Rx(0.3) | qb1
    Rxx(-math.pi) | (qb0, qb1)
    assert len(backend.received_commands) == 0
    Measure | qb0
    Measure | qb1
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 1
    assert received_commands[0].gate == Rx(0.3)
    assert received_commands[0].qubits[0][0].id == qb1[0].id

def test_local_optimizer_mergeable_gates():
    local_optimizer = _optimize.LocalOptimizer(m=4)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    # Test that it merges mergeable gates such as Rx
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    for _ in range(10):
        Rx(0.5) | qb0
    for _ in range(10):
        Ry(0.5) | qb0
    for _ in range(10):
        Rz(0.5) | qb0
    # Test merge for Rxx, Ryy, Rzz with interchangeable qubits
    Rxx(0.5) | (qb0, qb1)
    Rxx(0.5) | (qb1, qb0)
    Ryy(0.5) | (qb0, qb1)
    Ryy(0.5) | (qb1, qb0)
    Rzz(0.5) | (qb0, qb1)
    Rzz(0.5) | (qb1, qb0)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    # Expect one gate each of Rx, Ry, Rz, Rxx, Ryy, Rzz
    assert len(received_commands) == 6
    assert received_commands[0].gate == Rx(10 * 0.5)
    assert received_commands[1].gate == Ry(10 * 0.5)
    assert received_commands[2].gate == Rz(10 * 0.5)
    assert received_commands[3].gate == Rxx(1.0)
    assert received_commands[4].gate == Ryy(1.0)
    assert received_commands[5].gate == Rzz(1.0)

def test_local_optimizer_separated_mergeable_gates():
    """Tests the situation where the next command on this qubit
    is a mergeable command, but another qubit involved is separated 
    from the mergeable command by only commutable gates. 
    The commands should merge.
    """
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    #assert len(backend.received_commands) == 0
    #Reminder: Rxx and Rx commute
    Rxx(0.3) | (qb0, qb1)
    Rx(math.pi) | qb1
    Rxx(0.8) | (qb0, qb1)
    Rx(0.3) | qb1
    Rxx(1.2) | (qb0, qb1)
    Ry(0.5) | qb1
    H | qb0
    assert len(backend.received_commands) == 0
    Measure | qb0
    Measure | qb1
    assert len(backend.received_commands) == 8
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert received_commands[0].gate == Rxx(2.3)
    assert received_commands[1].gate == H
    assert received_commands[2].gate == Rx(math.pi+0.3)
    assert received_commands[3].gate == Ry(0.5)
    assert received_commands[0].qubits[0][0].id == qb0[0].id
    assert received_commands[0].qubits[1][0].id == qb1[0].id
    assert received_commands[1].qubits[0][0].id == qb0[0].id
    assert received_commands[2].qubits[0][0].id == qb1[0].id
    assert received_commands[3].qubits[0][0].id == qb1[0].id

def test_local_optimizer_identity_gates():
    local_optimizer = _optimize.LocalOptimizer(m=4)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    # Test that it merges mergeable gates such as Rx
    qb0 = eng.allocate_qubit()
    for _ in range(10):
        Rx(0.0) | qb0
        Ry(0.0) | qb0
        Rx(4*math.pi) | qb0
        Ry(4*math.pi) | qb0
    Rx(0.5) | qb0
    assert len(backend.received_commands) == 0
    eng.flush()
    # Expect allocate, one Rx gate, and flush gate
    assert len(backend.received_commands) == 3
    assert backend.received_commands[1].gate == Rx(0.5)

def test_local_optimizer_commutable_gates():
    """ Test that inverse gates separated by two commutable gates 
    cancel successfully and that mergeable gates separated by
    two commutable gates cancel successfully.
    """
    local_optimizer = _optimize.LocalOptimizer(m=5)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    qb3 = eng.allocate_qubit()
    Rx(0.4) | qb0
    Rx(-math.pi) | qb1
    Rxx(0.3) | (qb1, qb0)
    Rxx(0.5) | (qb0, qb1)
    Rx(math.pi) | qb1
    Rx(0.5) | qb0
    Rxx(0.2) | (qb2, qb3)
    Rx(0.3) | qb2
    Rx(0.2) | qb3
    Rxx(0.2) | (qb3, qb2)
    X | qb3 
    Ph(0.2) | qb3
    X | qb3
    Ph(0.1) | qb3
    X | qb3
    Rx(0.2) | qb3
    X | qb3
    X | qb3
    SqrtX | qb3
    X | qb3
    # All the Xs should cancel, because we have 3 pairs of Xs each 
    # separated by a gate which is commutable with X.
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
            print(cmd)
    assert len(received_commands) == 8
    assert received_commands[0].gate == Rxx(0.4)
    # A check that we have the gates we expect.
    assert received_commands[1].gate == Rx(0.2)
    assert received_commands[2].gate == Rx(0.9)
    assert received_commands[3].gate == Rxx(0.8)
    assert received_commands[4].gate == Rx(0.3)
    assert received_commands[5].gate == Ph(0.3)
    assert received_commands[6].gate == Rx(0.2)
    assert received_commands[7].gate == SqrtX
    # A check the qubit ids on the final gates in the circuit
    # are as we expect.
    # If this test doesn't succeed check that the Rxx 
    # interchangeable qubits attribute is working.
    assert received_commands[0].qubits[0][0].id == qb2[0].id
    assert received_commands[0].qubits[1][0].id == qb3[0].id

def test_local_optimizer_commutable_circuit_Rz_example_1():
    """ Example circuit where the Rzs should merge. """
    # Rzs should merge
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Rz(0.1) | qb0
    H | qb0
    CNOT | (qb1, qb0)
    H | qb0
    Rz(0.2) | qb0
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert received_commands[0].gate == Rz(0.3)
    assert len(received_commands) == 4

def test_local_optimizer_commutable_circuit_Rz_example_2():
    """ Rzs shouldn't merge (Although in theory they should, 
    this would require a new update.) """
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Rz(0.1) | qb1
    H | qb0
    CNOT | (qb1, qb0)
    H | qb0
    Rz(0.2) | qb1
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert received_commands[1].gate == Rz(0.1)
    assert len(received_commands) == 5

def test_local_optimizer_commutable_circuit_Rz_example_3():
    """ Rzs should not merge because they are operating on different qubits. """
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Rz(0.1) | qb1
    H | qb0
    CNOT | (qb1, qb0)
    H | qb0
    Rz(0.2) | qb0
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert received_commands[1].gate == Rz(0.1)
    assert len(received_commands) == 5

def test_local_optimizer_commutable_circuit_Rz_example_4():
    """Rzs shouldn't merge because they are operating on different qubits."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Rz(0.1) | qb0
    H | qb0
    CNOT | (qb1, qb0)
    H | qb0
    Rz(0.2) | qb1
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert received_commands[0].gate == Rz(0.1)
    assert len(received_commands) == 5

def test_local_optimizer_commutable_circuit_Rz_example_5():
    """Rzs shouldn't merge because CNOT is the wrong orientation."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Rz(0.1) | qb0
    H | qb0
    CNOT | (qb0, qb1)
    H | qb0
    Rz(0.2) | qb0
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert received_commands[0].gate == Rz(0.1)
    assert len(received_commands) == 5

def test_local_optimizer_commutable_circuit_Rz_example_6():
    """Rzs shouldn't merge (Although in theory they should, 
    this would require a new update.)"""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Rz(0.1) | qb0
    H | qb1
    CNOT | (qb0, qb1)
    H | qb1
    Rz(0.2) | qb0
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert received_commands[0].gate == Rz(0.1)
    assert len(received_commands) == 5

def test_local_optimizer_commutable_circuit_Rz_example_7():
    """Rzs shouldn't merge. Second H on wrong qubit."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Rz(0.1) | qb0
    H | qb0
    CNOT | (qb1, qb0)
    H | qb1
    Rz(0.2) | qb0
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert received_commands[0].gate == Rz(0.1)
    assert len(received_commands) == 5

def test_local_optimizer_commutable_circuit_CNOT_example_1():
    """This example should commute."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb2, qb0)
    H | qb0
    CNOT | (qb0, qb1)
    H | qb0
    CNOT | (qb2, qb0)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 3
    assert received_commands[0].gate == H

def test_local_optimizer_commutable_circuit_CNOT_example_2():
    """This example should commute."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb1, qb0)
    H | qb0
    CNOT | (qb0, qb2)
    H | qb0
    CNOT | (qb1, qb0)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 3
    assert received_commands[0].gate == H

def test_local_optimizer_commutable_circuit_CNOT_example_3():
    """This example should commute."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb0, qb1)
    H | qb1
    CNOT | (qb1, qb2)
    H | qb1
    CNOT | (qb0, qb1)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 3
    assert received_commands[0].gate == H 

def test_local_optimizer_commutable_circuit_CNOT_example_4():
    """This example shouldn't commute because the CNOT is the
    wrong orientation."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb1, qb0)
    H | qb1
    CNOT | (qb1, qb2)
    H | qb1
    CNOT | (qb1, qb0)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 5
    assert received_commands[0].gate.__class__ == XGate

def test_local_optimizer_commutable_circuit_CNOT_example_5():
    """This example shouldn't commute because the CNOT is the
    wrong orientation."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb0, qb1)
    H | qb1
    CNOT | (qb1, qb2)
    H | qb1
    CNOT | (qb1, qb0)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 5
    assert received_commands[0].gate.__class__ == XGate

def test_local_optimizer_commutable_circuit_CNOT_example_6():
    """This example shouldn't commute because the CNOT is the
    wrong orientation. Same as example_3 with middle CNOT reversed."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb0, qb1)
    H | qb1
    CNOT | (qb2, qb1)
    H | qb1
    CNOT | (qb0, qb1)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 5
    assert received_commands[0].gate.__class__ == XGate

def test_local_optimizer_commutable_circuit_CNOT_example_7():
    """This example shouldn't commute because the CNOT is the
    wrong orientation. Same as example_1 with middle CNOT reversed."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb2, qb0)
    H | qb0
    CNOT | (qb1, qb0)
    H | qb0
    CNOT | (qb2, qb0)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 5
    assert received_commands[0].gate.__class__ == XGate
    
def test_local_optimizer_commutable_circuit_CNOT_example_8():
    """This example shouldn't commute because the CNOT is the
    wrong orientation. Same as example_2 with middle CNOT reversed."""
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb1, qb0)
    H | qb0
    CNOT | (qb2, qb0)
    H | qb0
    CNOT | (qb1, qb0)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 5
    assert received_commands[0].gate.__class__ == XGate

def test_local_optimizer_commutable_circuit_CNOT_and_Rz_example_1():
    """This example is to check everything works as expected when
    the commutable circuit is on later commands in the optimizer 
    dictionary. The number of commmands should reduce from 10 to 7. """
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    Rz(0.1) | qb0
    H | qb0
    CNOT | (qb1, qb0)
    H | qb0
    Rz(0.2) | qb0
    CNOT | (qb0, qb1)
    H | qb1
    CNOT | (qb1, qb2)
    H | qb1
    CNOT | (qb0, qb1)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 7
    assert received_commands[6].gate == H

def test_local_optimizer_commutable_circuit_CNOT_and_Rz_example_2():
    """ This example is to check everything works as expected when
    the commutable circuit is on qubits 3, 4, 5. """
    local_optimizer = _optimize.LocalOptimizer(m=10)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    qb3 = eng.allocate_qubit()
    qb4 = eng.allocate_qubit()
    Rz(0.1) | qb0
    H | qb0
    CNOT | (qb1, qb0)
    H | qb0
    Rz(0.2) | qb0
    CNOT | (qb2, qb3)
    H | qb3
    CNOT | (qb3, qb4)
    H | qb3
    CNOT | (qb2, qb3)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 7
    assert received_commands[6].gate == H

def test_local_optimizer_apply_commutation_false():
    """Test that the local_optimizer behaves as if commutation isn't an option
    if you set apply_commutation = False. """
    local_optimizer = _optimize.LocalOptimizer(m=10, apply_commutation=False)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[local_optimizer])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Rz(0.1) | qb0 # Rzs next to eachother should merge
    Rz(0.4) | qb0
    Rzz(0.3) | (qb0, qb1) # Rzs either side of Rzz should not merge
    Rz(0.2) | qb0 
    H | qb0 # Hs next to eachother should cancel
    H | qb0
    Ry(0.1) | qb1 # Ry should not merge with the Rz on the other side of
    H | qb0       # a commutable list
    CNOT | (qb0, qb1)
    H | qb0
    Ry(0.2) | qb1
    Rxx(0.2) | (qb0, qb1) 
    Rx(0.1) | qb1 # Rxxs either side of Rx shouldn't merge
    Rxx(0.1) | (qb0, qb1)
    eng.flush()
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    assert len(received_commands) == 11
    assert received_commands[0].gate == Rz(0.5)
    assert received_commands[2].gate == Rz(0.2)
    assert received_commands[4].gate == Ry(0.1)
    assert received_commands[7].gate == Ry(0.2)
    assert received_commands[10].gate == Rxx(0.1)