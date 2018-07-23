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

"""Tests for projectq.backends._ibm._ibm.py."""

import pytest
import json

import projectq.setups.decompositions
from projectq import MainEngine
from projectq.backends._ibm import _ibm
from projectq.cengines import (TagRemover,
                               LocalOptimizer,
                               AutoReplacer,
                               IBM5QubitMapper,
                               SwapAndCNOTFlipper,
                               DummyEngine,
                               DecompositionRuleSet)
from projectq.ops import (All, Allocate, Barrier, Command, Deallocate,
                          Entangle, Measure, NOT, Rx, Ry, Rz, S, Sdag, T, Tdag,
                          X, Y, Z)

from projectq.setups.ibm import ibmqx4_connections


# Insure that no HTTP request can be made in all tests in this module
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


_api_url = 'https://quantumexperience.ng.bluemix.net/api/'
_api_url_status = 'https://quantumexperience.ng.bluemix.net/api/'


@pytest.mark.parametrize("single_qubit_gate, is_available", [
    (X, True), (Y, True), (Z, True), (T, True), (Tdag, True), (S, True),
    (Sdag, True), (Allocate, True), (Deallocate, True), (Measure, True),
    (NOT, True), (Rx(0.5), True), (Ry(0.5), True), (Rz(0.5), True),
    (Barrier, True), (Entangle, False)])
def test_ibm_backend_is_available(single_qubit_gate, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    ibm_backend = _ibm.IBMBackend()
    cmd = Command(eng, single_qubit_gate, (qubit1,))
    assert ibm_backend.is_available(cmd) == is_available


@pytest.mark.parametrize("num_ctrl_qubits, is_available", [
    (0, True), (1, True), (2, False), (3, False)])
def test_ibm_backend_is_available_control_not(num_ctrl_qubits, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)
    ibm_backend = _ibm.IBMBackend()
    cmd = Command(eng, NOT, (qubit1,), controls=qureg)
    assert ibm_backend.is_available(cmd) == is_available


def test_ibm_backend_init():
    backend = _ibm.IBMBackend(verbose=True, use_hardware=True)
    assert backend.qasm == ""


def test_ibm_empty_circuit():
    backend = _ibm.IBMBackend(verbose=True)
    eng = MainEngine(backend=backend)
    eng.flush()


def test_ibm_sent_error(monkeypatch):
    # patch send
    def mock_send(*args, **kwargs):
        raise TypeError
    monkeypatch.setattr(_ibm, "send", mock_send)

    backend = _ibm.IBMBackend(verbose=True)
    eng = MainEngine(backend=backend,
                     engine_list=[IBM5QubitMapper(),
                                  SwapAndCNOTFlipper(set())])
    qubit = eng.allocate_qubit()
    X | qubit
    with pytest.raises(Exception):
        qubit[0].__del__()
        eng.flush()
    # atexit sends another FlushGate, therefore we remove the backend:
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


def test_ibm_retrieve(monkeypatch):
    # patch send
    def mock_retrieve(*args, **kwargs):
        return {'date': '2017-01-19T14:28:47.622Z',
                'data': {'time': 14.429004907608032, 'counts': {'00111': 396,
                                                                '00101': 27,
                                                                '00000': 601},
                         'qasm': ('...')}}
    monkeypatch.setattr(_ibm, "retrieve", mock_retrieve)
    backend = _ibm.IBMBackend(retrieve_execution="ab1s2")
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    connectivity = set([(1, 2), (2, 4), (0, 2), (3, 2), (4, 3), (0, 1)])
    engine_list = [TagRemover(),
                   LocalOptimizer(10),
                   AutoReplacer(rule_set),
                   TagRemover(),
                   IBM5QubitMapper(),
                   SwapAndCNOTFlipper(connectivity),
                   LocalOptimizer(10)]
    eng = MainEngine(backend=backend, engine_list=engine_list)
    unused_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(3)
    # entangle the qureg
    Entangle | qureg
    Tdag | qureg[0]
    Sdag | qureg[0]
    Barrier | qureg
    Rx(0.2) | qureg[0]
    del unused_qubit
    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    eng.flush()
    prob_dict = eng.backend.get_probabilities([qureg[0], qureg[2], qureg[1]])
    assert prob_dict['111'] == pytest.approx(0.38671875)
    assert prob_dict['101'] == pytest.approx(0.0263671875)


def test_ibm_backend_functional_test(monkeypatch):
    correct_info = ('{"qasms": [{"qasm": "\\ninclude \\"qelib1.inc\\";'
                    '\\nqreg q[3];\\ncreg c[3];\\nh q[2];\\ncx q[2], q[0];'
                    '\\ncx q[2], q[1];\\ntdg q[2];\\nsdg q[2];'
                    '\\nbarrier q[2], q[0], q[1];'
                    '\\nu3(0.2, -pi/2, pi/2) q[2];\\nmeasure q[2] -> '
                    'c[2];\\nmeasure q[0] -> c[0];\\nmeasure q[1] -> c[1];"}]'
                    ', "shots": 1024, "maxCredits": 5, "backend": {"name": '
                    '"simulator"}}')

    def mock_send(*args, **kwargs):
        assert json.loads(args[0]) == json.loads(correct_info)
        return {'date': '2017-01-19T14:28:47.622Z',
                'data': {'time': 14.429004907608032, 'counts': {'00111': 396,
                                                                '00101': 27,
                                                                '00000': 601},
                         'qasm': ('...')}}
    monkeypatch.setattr(_ibm, "send", mock_send)

    backend = _ibm.IBMBackend(verbose=True)
    # no circuit has been executed -> raises exception
    with pytest.raises(RuntimeError):
        backend.get_probabilities([])
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])

    engine_list = [TagRemover(),
                   LocalOptimizer(10),
                   AutoReplacer(rule_set),
                   TagRemover(),
                   IBM5QubitMapper(),
                   SwapAndCNOTFlipper(ibmqx4_connections),
                   LocalOptimizer(10)]
    eng = MainEngine(backend=backend, engine_list=engine_list)
    unused_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(3)
    # entangle the qureg
    Entangle | qureg
    Tdag | qureg[0]
    Sdag | qureg[0]
    Barrier | qureg
    Rx(0.2) | qureg[0]
    del unused_qubit
    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    eng.flush()
    prob_dict = eng.backend.get_probabilities([qureg[0], qureg[2], qureg[1]])
    assert prob_dict['111'] == pytest.approx(0.38671875)
    assert prob_dict['101'] == pytest.approx(0.0263671875)

    with pytest.raises(RuntimeError):
        eng.backend.get_probabilities(eng.allocate_qubit())
