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

"""Tests for projectq.meta._loop.py"""

import pytest
import types

from copy import deepcopy
from projectq import MainEngine
from projectq.meta import ComputeTag, DirtyQubitTag
from projectq.cengines import DummyEngine
from projectq.ops import H, CNOT, X, FlushGate, Allocate, Deallocate

from projectq.meta import _loop


def test_loop_tag():
    tag0 = _loop.LoopTag(10)
    tag1 = _loop.LoopTag(10)
    tag2 = tag0
    tag3 = deepcopy(tag0)
    tag3.num = 9
    other_tag = ComputeTag()
    assert tag0 == tag2
    assert tag0 != tag1
    assert not tag0 == tag3
    assert not tag0 == other_tag


def test_loop_wrong_input_type():
    eng = MainEngine(backend=DummyEngine(), engine_list=[])
    qubit = eng.allocate_qubit()
    with pytest.raises(TypeError):
        _loop.Loop(eng, 1.1)


def test_loop_negative_iteration_number():
    eng = MainEngine(backend=DummyEngine(), engine_list=[])
    qubit = eng.allocate_qubit()
    with pytest.raises(ValueError):
        _loop.Loop(eng, -1)


def test_loop_with_supported_loop_tag_and_local_qubits():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])

    def allow_loop_tags(self, meta_tag):
            return meta_tag == _loop.LoopTag

    backend.is_meta_tag_handler = types.MethodType(allow_loop_tags, backend)
    qubit = eng.allocate_qubit()
    H | qubit
    with _loop.Loop(eng, 6):
        ancilla = eng.allocate_qubit()
        ancilla2 = eng.allocate_qubit()
        H | ancilla2
        H | ancilla
        CNOT | (ancilla, qubit)
        H | ancilla
        H | ancilla2
        del ancilla2
        del ancilla
    H | qubit
    eng.flush(deallocate_qubits=True)
    assert len(backend.received_commands) == 14
    assert backend.received_commands[0].gate == Allocate
    assert backend.received_commands[1].gate == H
    assert backend.received_commands[2].gate == Allocate
    assert backend.received_commands[3].gate == Allocate
    assert backend.received_commands[4].gate == H
    assert backend.received_commands[5].gate == H
    assert backend.received_commands[6].gate == X
    assert backend.received_commands[7].gate == H
    assert backend.received_commands[8].gate == H
    assert backend.received_commands[9].gate == Deallocate
    assert backend.received_commands[10].gate == Deallocate
    assert backend.received_commands[11].gate == H
    assert backend.received_commands[12].gate == Deallocate
    assert backend.received_commands[13].gate == FlushGate()
    # Test qubit ids
    qubit_id = backend.received_commands[0].qubits[0][0].id
    ancilla_id = backend.received_commands[2].qubits[0][0].id
    ancilla2_id = backend.received_commands[3].qubits[0][0].id
    assert qubit_id != ancilla_id
    assert qubit_id != ancilla2_id
    assert ancilla_id != ancilla2_id
    assert backend.received_commands[1].qubits[0][0].id == qubit_id
    assert backend.received_commands[4].qubits[0][0].id == ancilla2_id
    assert backend.received_commands[5].qubits[0][0].id == ancilla_id
    assert backend.received_commands[6].qubits[0][0].id == qubit_id
    assert backend.received_commands[6].control_qubits[0].id == ancilla_id
    assert backend.received_commands[7].qubits[0][0].id == ancilla_id
    assert backend.received_commands[8].qubits[0][0].id == ancilla2_id
    assert backend.received_commands[9].qubits[0][0].id == ancilla2_id
    assert backend.received_commands[10].qubits[0][0].id == ancilla_id
    assert backend.received_commands[11].qubits[0][0].id == qubit_id
    assert backend.received_commands[12].qubits[0][0].id == qubit_id
    # Tags
    assert len(backend.received_commands[3].tags) == 1
    loop_tag = backend.received_commands[3].tags[0]
    assert isinstance(loop_tag, _loop.LoopTag)
    assert loop_tag.num == 6
    for ii in [0, 1, 11, 12, 13]:
        assert backend.received_commands[ii].tags == []
    for ii in range(2, 9):
        assert backend.received_commands[ii].tags == [loop_tag]


def test_empty_loop():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()

    assert len(backend.received_commands) == 1
    with _loop.Loop(eng, 0):
        H | qubit
    assert len(backend.received_commands) == 1


def test_empty_loop_when_loop_tag_supported_by_backend():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])

    def allow_loop_tags(self, meta_tag):
            return meta_tag == _loop.LoopTag

    backend.is_meta_tag_handler = types.MethodType(allow_loop_tags, backend)
    qubit = eng.allocate_qubit()

    assert len(backend.received_commands) == 1
    with _loop.Loop(eng, 0):
        H | qubit
    assert len(backend.received_commands) == 1


def test_loop_with_supported_loop_tag_depending_on_num():
    # Test that if loop has only one iteration, there is no loop tag
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])

    def allow_loop_tags(self, meta_tag):
            return meta_tag == _loop.LoopTag

    backend.is_meta_tag_handler = types.MethodType(allow_loop_tags, backend)
    qubit = eng.allocate_qubit()
    with _loop.Loop(eng, 1):
        H | qubit
    with _loop.Loop(eng, 2):
        H | qubit
    assert len(backend.received_commands[1].tags) == 0
    assert len(backend.received_commands[2].tags) == 1


def test_loop_unrolling():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    with _loop.Loop(eng, 3):
        H | qubit
    eng.flush(deallocate_qubits=True)
    assert len(backend.received_commands) == 6


def test_loop_unrolling_with_ancillas():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    qubit_id = deepcopy(qubit[0].id)
    with _loop.Loop(eng, 3):
        ancilla = eng.allocate_qubit()
        H | ancilla
        CNOT | (ancilla, qubit)
        del ancilla
    eng.flush(deallocate_qubits=True)
    assert len(backend.received_commands) == 15
    assert backend.received_commands[0].gate == Allocate
    for ii in range(3):
        assert backend.received_commands[ii * 4 + 1].gate == Allocate
        assert backend.received_commands[ii * 4 + 2].gate == H
        assert backend.received_commands[ii * 4 + 3].gate == X
        assert backend.received_commands[ii * 4 + 4].gate == Deallocate
        # Check qubit ids
        assert (backend.received_commands[ii * 4 + 1].qubits[0][0].id ==
                backend.received_commands[ii * 4 + 2].qubits[0][0].id)
        assert (backend.received_commands[ii * 4 + 1].qubits[0][0].id ==
                backend.received_commands[ii * 4 + 3].control_qubits[0].id)
        assert (backend.received_commands[ii * 4 + 3].qubits[0][0].id ==
                qubit_id)
        assert (backend.received_commands[ii * 4 + 1].qubits[0][0].id ==
                backend.received_commands[ii * 4 + 4].qubits[0][0].id)
    assert backend.received_commands[13].gate == Deallocate
    assert backend.received_commands[14].gate == FlushGate()
    assert (backend.received_commands[1].qubits[0][0].id !=
            backend.received_commands[5].qubits[0][0].id)
    assert (backend.received_commands[1].qubits[0][0].id !=
            backend.received_commands[9].qubits[0][0].id)
    assert (backend.received_commands[5].qubits[0][0].id !=
            backend.received_commands[9].qubits[0][0].id)


def test_nested_loop():
    backend = DummyEngine(save_commands=True)

    def allow_loop_tags(self, meta_tag):
            return meta_tag == _loop.LoopTag

    backend.is_meta_tag_handler = types.MethodType(allow_loop_tags, backend)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    with _loop.Loop(eng, 3):
        with _loop.Loop(eng, 4):
            H | qubit
    eng.flush(deallocate_qubits=True)
    assert len(backend.received_commands) == 4
    assert backend.received_commands[1].gate == H
    assert len(backend.received_commands[1].tags) == 2
    assert backend.received_commands[1].tags[0].num == 4
    assert backend.received_commands[1].tags[1].num == 3
    assert (backend.received_commands[1].tags[0].id !=
            backend.received_commands[1].tags[1].id)


def test_qubit_management_error():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    with pytest.raises(_loop.QubitManagementError):
        with _loop.Loop(eng, 3):
            qb = eng.allocate_qubit()


def test_qubit_management_error_when_loop_tag_supported():
    backend = DummyEngine(save_commands=True)

    def allow_loop_tags(self, meta_tag):
            return meta_tag == _loop.LoopTag

    backend.is_meta_tag_handler = types.MethodType(allow_loop_tags, backend)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    with pytest.raises(_loop.QubitManagementError):
        with _loop.Loop(eng, 3):
            qb = eng.allocate_qubit()
