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
Tests for barrier.py
"""

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import Barrier, R

from . import barrier


def test_recognize_barrier():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    R(0.2) | qubit
    Barrier | qubit
    eng.flush(deallocate_qubits=True)
    # Don't test initial allocate and trailing deallocate and flush gate.
    count = 0
    for cmd in saving_backend.received_commands[1:-2]:
        count += barrier._recognize_barrier(cmd)
    assert count == 2  # recognizes all gates


def test_remove_barrier():
    saving_backend = DummyEngine(save_commands=True)

    def my_is_available(cmd):
        return not cmd.gate == Barrier

    saving_backend.is_available = my_is_available
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    R(0.2) | qubit
    Barrier | qubit
    eng.flush(deallocate_qubits=True)
    # Don't test initial allocate and trailing deallocate and flush gate.
    count = 0
    for cmd in saving_backend.received_commands[1:-2]:
        assert not cmd.gate == Barrier
    assert len(saving_backend.received_commands[1:-2]) == 1
