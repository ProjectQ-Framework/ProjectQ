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

"""Tests for projectq.meta._dagger.py"""

import pytest
import types

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import CNOT, X, Rx, H, Allocate, Deallocate
from projectq.meta import DirtyQubitTag

from projectq.meta import _dagger


def test_dagger_with_dirty_qubits():
    backend = DummyEngine(save_commands=True)

    def allow_dirty_qubits(self, meta_tag):
        return meta_tag == DirtyQubitTag

    backend.is_meta_tag_handler = types.MethodType(allow_dirty_qubits, backend)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    with _dagger.Dagger(eng):
        ancilla = eng.allocate_qubit(dirty=True)
        Rx(0.6) | ancilla
        CNOT | (ancilla, qubit)
        H | qubit
        Rx(-0.6) | ancilla
        del ancilla[0]
    eng.flush(deallocate_qubits=True)
    assert len(backend.received_commands) == 9
    assert backend.received_commands[0].gate == Allocate
    assert backend.received_commands[1].gate == Allocate
    assert backend.received_commands[2].gate == Rx(0.6)
    assert backend.received_commands[3].gate == H
    assert backend.received_commands[4].gate == X
    assert backend.received_commands[5].gate == Rx(-0.6)
    assert backend.received_commands[6].gate == Deallocate
    assert backend.received_commands[7].gate == Deallocate
    assert backend.received_commands[1].tags == [DirtyQubitTag()]
    assert backend.received_commands[6].tags == [DirtyQubitTag()]


def test_dagger_qubit_management_error():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    with pytest.raises(_dagger.QubitManagementError):
        with _dagger.Dagger(eng):
            ancilla = eng.allocate_qubit()
