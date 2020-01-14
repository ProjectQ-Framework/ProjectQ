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

"""Tests for projectq.backends._aqt._aqt.py."""

import pytest
import json
import math

from projectq import MainEngine
from projectq.backends._aqt import _aqt
from projectq.cengines import (TagRemover,
                               LocalOptimizer,
                               DummyEngine)
from projectq.ops import (All, Allocate, Barrier, Command, Deallocate,
                          Entangle, Measure, NOT, Rx, Ry, Rz, Rxx, S, Sdag, T, Tdag,
                          X, Y, Z)

from projectq.setups import restrictedgateset


# Insure that no HTTP request can be made in all tests in this module
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")

@pytest.mark.parametrize("single_qubit_gate, is_available", [
    (X, False), (Y, False), (Z, False), (T, False), (Tdag, False), (S, False),
    (Sdag, False), (Allocate, True), (Deallocate, True), (Measure, True),
    (NOT, False), (Rx(0.5), True), (Ry(0.5), True), (Rz(0.5), True),
    (Rxx(0.5), True),(Barrier, True), (Entangle, False)])


@pytest.mark.parametrize("num_ctrl_qubits, is_available", [
    (0, True), (1, False), (2, False), (3, False)])
def test_ibm_backend_is_available_control_not(num_ctrl_qubits, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)
    aqt_backend = _aqt.IBMBackend()
    cmd = Command(eng, Rx(0.5), (qubit1,), controls=qureg)
    assert aqt_backend.is_available(cmd) == is_available

def test_aqt_backend_init():
    backend = _aqt.IBMBackend(verbose=True, use_hardware=True)
    assert len(backend.circuit) == 0


def test_aqt_empty_circuit():
    backend = _ibm.IBMBackend(verbose=True)
    eng = MainEngine(backend=backend)
    eng.flush()


def test_aqt_sent_error(monkeypatch):
    # patch send
    def mock_send(*args, **kwargs):
        raise TypeError
    monkeypatch.setattr(_aqt, "send", mock_send)

    backend = _aqt.AQTBackend(verbose=True)
    eng = MainEngine(backend=backend)
    qubit = eng.allocate_qubit()
    Rx(0.5) | qubit
    with pytest.raises(Exception):
        qubit[0].__del__()
        eng.flush()
    # atexit sends another FlushGate, therefore we remove the backend:
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


def test_aqt_retrieve(monkeypatch):
    # patch send
    def mock_retrieve(*args, **kwargs):
        return {'id': 'a3877d18-314f-46c9-86e7-316bc4dbe968',
                'no_qubits': 2,
                'received': [['Y', 0.5, [0]], ['X', 0.5, [0]], ['X', 0.5, [0]],
                            ['Y', 0.5, [0]], ['MS', 0.5, [0, 1]], ['X', -0.5, [0]],
                            ['Y', -0.5, [0]], ['X', -0.5, [1]]],
                'repetitions': 10,
                'samples': [0, 3, 0, 3, 0, 0, 0, 3, 0, 3],
                'status': 'finished'}
    monkeypatch.setattr(_aqt, "retrieve", mock_retrieve)
    backend = _aqt.AQTBackend(retrieve_execution="a3877d18-314f-46c9-86e7-316bc4dbe968")
    engine_list = [TagRemover(),
                   LocalOptimizer(10)]
    eng = MainEngine(backend=backend, engine_list=engine_list)
    unused_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(2)
    # entangle the qureg
    Ry(math.pi/2) | qureg[0]
    Rx(math.pi/2) | qureg[0]
    Rx(math.pi/2) | qureg[0]
    Ry(math.pi/2) | qureg[0]
    Rxx(math.pi/2) | (qureg[0],qureg[1])
    Rx(7*math.pi/2) | qureg[0]
    Ry(7*math.pi/2) | qureg[0]
    Rx(7*math.pi/2) | qureg[1]
    del unused_qubit
    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    eng.flush()
    prob_dict = eng.backend.get_probabilities([qureg[0],qureg[1]])
    assert prob_dict['11'] == pytest.approx(0.4)
    assert prob_dict['00'] == pytest.approx(0.6)


def test_aqt_backend_functional_test(monkeypatch):
    correct_info = """{'data': '[["Y", 0.5, [0]], ["X", 0.5, [0]], ["X", 0.5, [0]],
                            '["Y", 0.5, [0]], ["MS", 0.5, [0, 1]], ["X", -0.5, [0]],'
                            '["Y", -0.5, [0]], ["X", -0.5, [1]]]',
                    'access_token': 'TOKEN',
                    'repetitions': 100,
                    'no_qubits': 2}"""

    def mock_send(*args, **kwargs):
        assert json.loads(args[0]) == json.loads(correct_info)
        return {'id': 'a3877d18-314f-46c9-86e7-316bc4dbe968', 'status': 'queued'}

    monkeypatch.setattr(_aqt, "send", mock_send)

    backend = _aqt.AQTBackend(verbose=True)
    # no circuit has been executed -> raises exception
    with pytest.raises(RuntimeError):
        backend.get_probabilities([])

    engine_list = [TagRemover(),
                   LocalOptimizer(10)]
    eng = MainEngine(backend=backend, engine_list=engine_list)
    unused_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(2)
    # entangle the qureg
    Ry(math.pi/2) | qureg[0]
    Rx(math.pi/2) | qureg[0]
    Rx(math.pi/2) | qureg[0]
    Ry(math.pi/2) | qureg[0]
    Rxx(math.pi/2) | (qureg[0],qureg[1])
    Rx(7*math.pi/2) | qureg[0]
    Ry(7*math.pi/2) | qureg[0]
    Rx(7*math.pi/2) | qureg[1]
    del unused_qubit
    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    eng.flush()
    prob_dict = eng.backend.get_probabilities([qureg[0], qureg[1]])
    assert prob_dict['11'] == pytest.approx(0.4)
    assert prob_dict['00'] == pytest.approx(0.6)

    with pytest.raises(RuntimeError):
        eng.backend.get_probabilities(eng.allocate_qubit())
