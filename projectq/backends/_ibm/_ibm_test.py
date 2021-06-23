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
"""Tests for projectq.backends._ibm._ibm.py."""

import pytest
import math
from projectq.backends._ibm import _ibm
from projectq.cengines import MainEngine, BasicMapperEngine, DummyEngine
from projectq.meta import LogicalQubitIDTag
from projectq.ops import (
    All,
    Allocate,
    Barrier,
    Command,
    Deallocate,
    Entangle,
    Measure,
    NOT,
    Rx,
    Ry,
    Rz,
    S,
    Sdag,
    T,
    Tdag,
    X,
    Y,
    Z,
    H,
    CNOT,
)
from projectq.setups import restrictedgateset
from projectq.types import WeakQubitRef


# Insure that no HTTP request can be made in all tests in this module
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.mark.parametrize(
    "single_qubit_gate, is_available",
    [
        (X, False),
        (Y, False),
        (Z, False),
        (H, True),
        (T, False),
        (Tdag, False),
        (S, False),
        (Sdag, False),
        (Allocate, True),
        (Deallocate, True),
        (Measure, True),
        (NOT, False),
        (Rx(0.5), True),
        (Ry(0.5), True),
        (Rz(0.5), True),
        (Barrier, True),
        (Entangle, False),
    ],
)
def test_ibm_backend_is_available(single_qubit_gate, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    ibm_backend = _ibm.IBMBackend()
    cmd = Command(eng, single_qubit_gate, (qubit1,))
    assert ibm_backend.is_available(cmd) == is_available


@pytest.mark.parametrize("num_ctrl_qubits, is_available", [(0, False), (1, True), (2, False), (3, False)])
def test_ibm_backend_is_available_control_not(num_ctrl_qubits, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)
    ibm_backend = _ibm.IBMBackend()
    cmd = Command(eng, NOT, (qubit1,), controls=qureg)
    assert ibm_backend.is_available(cmd) == is_available


def test_ibm_backend_is_available_negative_control():
    backend = _ibm.IBMBackend()

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)

    assert backend.is_available(Command(None, NOT, qubits=([qb0],), controls=[qb1]))
    assert backend.is_available(Command(None, NOT, qubits=([qb0],), controls=[qb1], control_state='1'))
    assert not backend.is_available(Command(None, NOT, qubits=([qb0],), controls=[qb1], control_state='0'))


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
    mapper = BasicMapperEngine()
    res = dict()
    for i in range(4):
        res[i] = i
    mapper.current_mapping = res
    eng = MainEngine(backend=backend, engine_list=[mapper])
    qubit = eng.allocate_qubit()
    Rx(math.pi) | qubit
    with pytest.raises(Exception):
        qubit[0].__del__()
        eng.flush()
    # atexit sends another FlushGate, therefore we remove the backend:
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


def test_ibm_sent_error_2(monkeypatch):
    backend = _ibm.IBMBackend(verbose=True)
    mapper = BasicMapperEngine()
    res = dict()
    for i in range(4):
        res[i] = i
    mapper.current_mapping = res
    eng = MainEngine(backend=backend, engine_list=[mapper])
    qubit = eng.allocate_qubit()
    Rx(math.pi) | qubit

    with pytest.raises(Exception):
        S | qubit  # no setup to decompose S gate, so not accepted by the backend
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


def test_ibm_retrieve(monkeypatch):
    # patch send
    def mock_retrieve(*args, **kwargs):
        return {
            'data': {'counts': {'0x0': 504, '0x2': 8, '0xc': 6, '0xe': 482}},
            'header': {
                'clbit_labels': [['c', 0], ['c', 1], ['c', 2], ['c', 3]],
                'creg_sizes': [['c', 4]],
                'memory_slots': 4,
                'n_qubits': 32,
                'name': 'circuit0',
                'qreg_sizes': [['q', 32]],
                'qubit_labels': [
                    ['q', 0],
                    ['q', 1],
                    ['q', 2],
                    ['q', 3],
                    ['q', 4],
                    ['q', 5],
                    ['q', 6],
                    ['q', 7],
                    ['q', 8],
                    ['q', 9],
                    ['q', 10],
                    ['q', 11],
                    ['q', 12],
                    ['q', 13],
                    ['q', 14],
                    ['q', 15],
                    ['q', 16],
                    ['q', 17],
                    ['q', 18],
                    ['q', 19],
                    ['q', 20],
                    ['q', 21],
                    ['q', 22],
                    ['q', 23],
                    ['q', 24],
                    ['q', 25],
                    ['q', 26],
                    ['q', 27],
                    ['q', 28],
                    ['q', 29],
                    ['q', 30],
                    ['q', 31],
                ],
            },
            'metadata': {
                'measure_sampling': True,
                'method': 'statevector',
                'parallel_shots': 1,
                'parallel_state_update': 16,
            },
            'seed_simulator': 465435780,
            'shots': 1000,
            'status': 'DONE',
            'success': True,
            'time_taken': 0.0045786460000000005,
        }

    monkeypatch.setattr(_ibm, "retrieve", mock_retrieve)
    backend = _ibm.IBMBackend(retrieve_execution="ab1s2", num_runs=1000)
    mapper = BasicMapperEngine()
    res = dict()
    for i in range(4):
        res[i] = i
    mapper.current_mapping = res
    ibm_setup = [mapper]
    setup = restrictedgateset.get_engine_list(one_qubit_gates=(Rx, Ry, Rz, H), two_qubit_gates=(CNOT,))
    setup.extend(ibm_setup)
    eng = MainEngine(backend=backend, engine_list=setup)
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
    assert prob_dict['000'] == pytest.approx(0.504)
    assert prob_dict['111'] == pytest.approx(0.482)
    assert prob_dict['011'] == pytest.approx(0.006)


def test_ibm_backend_functional_test(monkeypatch):
    correct_info = {
        'json': [
            {'qubits': [1], 'name': 'u2', 'params': [0, 3.141592653589793]},
            {'qubits': [1, 2], 'name': 'cx'},
            {'qubits': [1, 3], 'name': 'cx'},
            {'qubits': [1], 'name': 'u3', 'params': [6.28318530718, 0, 0]},
            {'qubits': [1], 'name': 'u1', 'params': [11.780972450962]},
            {'qubits': [1], 'name': 'u3', 'params': [6.28318530718, 0, 0]},
            {'qubits': [1], 'name': 'u1', 'params': [10.995574287564]},
            {'qubits': [1, 2, 3], 'name': 'barrier'},
            {
                'qubits': [1],
                'name': 'u3',
                'params': [0.2, -1.5707963267948966, 1.5707963267948966],
            },
            {'qubits': [1], 'name': 'measure', 'memory': [1]},
            {'qubits': [2], 'name': 'measure', 'memory': [2]},
            {'qubits': [3], 'name': 'measure', 'memory': [3]},
        ],
        'nq': 4,
        'shots': 1000,
        'maxCredits': 10,
        'backend': {'name': 'ibmq_qasm_simulator'},
    }

    def mock_send(*args, **kwargs):
        assert args[0] == correct_info
        return {
            'data': {'counts': {'0x0': 504, '0x2': 8, '0xc': 6, '0xe': 482}},
            'header': {
                'clbit_labels': [['c', 0], ['c', 1], ['c', 2], ['c', 3]],
                'creg_sizes': [['c', 4]],
                'memory_slots': 4,
                'n_qubits': 32,
                'name': 'circuit0',
                'qreg_sizes': [['q', 32]],
                'qubit_labels': [
                    ['q', 0],
                    ['q', 1],
                    ['q', 2],
                    ['q', 3],
                    ['q', 4],
                    ['q', 5],
                    ['q', 6],
                    ['q', 7],
                    ['q', 8],
                    ['q', 9],
                    ['q', 10],
                    ['q', 11],
                    ['q', 12],
                    ['q', 13],
                    ['q', 14],
                    ['q', 15],
                    ['q', 16],
                    ['q', 17],
                    ['q', 18],
                    ['q', 19],
                    ['q', 20],
                    ['q', 21],
                    ['q', 22],
                    ['q', 23],
                    ['q', 24],
                    ['q', 25],
                    ['q', 26],
                    ['q', 27],
                    ['q', 28],
                    ['q', 29],
                    ['q', 30],
                    ['q', 31],
                ],
            },
            'metadata': {
                'measure_sampling': True,
                'method': 'statevector',
                'parallel_shots': 1,
                'parallel_state_update': 16,
            },
            'seed_simulator': 465435780,
            'shots': 1000,
            'status': 'DONE',
            'success': True,
            'time_taken': 0.0045786460000000005,
        }

    monkeypatch.setattr(_ibm, "send", mock_send)

    backend = _ibm.IBMBackend(verbose=True, num_runs=1000)
    import sys

    # no circuit has been executed -> raises exception
    with pytest.raises(RuntimeError):
        backend.get_probabilities([])
    mapper = BasicMapperEngine()
    res = dict()
    for i in range(4):
        res[i] = i
    mapper.current_mapping = res
    ibm_setup = [mapper]
    setup = restrictedgateset.get_engine_list(
        one_qubit_gates=(Rx, Ry, Rz, H), two_qubit_gates=(CNOT,), other_gates=(Barrier,)
    )
    setup.extend(ibm_setup)
    eng = MainEngine(backend=backend, engine_list=setup)
    # 4 qubits circuit is run, but first is unused to test ability for
    # get_probability to return the correct values for a subset of the total
    # register
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
    prob_dict = eng.backend.get_probabilities([qureg[2], qureg[1]])
    assert prob_dict['00'] == pytest.approx(0.512)
    assert prob_dict['11'] == pytest.approx(0.488)
    result = "\nu2(0,pi/2) q[1];\ncx q[1], q[2];\ncx q[1], q[3];"
    if sys.version_info.major == 3:
        result += "\nu3(6.28318530718, 0, 0) q[1];\nu1(11.780972450962) q[1];"
        result += "\nu3(6.28318530718, 0, 0) q[1];\nu1(10.995574287564) q[1];"
    else:
        result += "\nu3(6.28318530718, 0, 0) q[1];\nu1(11.780972451) q[1];"
        result += "\nu3(6.28318530718, 0, 0) q[1];\nu1(10.9955742876) q[1];"
    result += "\nbarrier q[1], q[2], q[3];"
    result += "\nu3(0.2, -pi/2, pi/2) q[1];\nmeasure q[1] -> c[1];"
    result += "\nmeasure q[2] -> c[2];\nmeasure q[3] -> c[3];"

    assert eng.backend.get_qasm() == result

    with pytest.raises(RuntimeError):
        eng.backend.get_probabilities(eng.allocate_qubit())


def test_ibm_errors():
    backend = _ibm.IBMBackend(verbose=True, num_runs=1000)
    mapper = BasicMapperEngine()
    mapper.current_mapping = {0: 0}
    eng = MainEngine(backend=backend, engine_list=[mapper])

    qb0 = WeakQubitRef(engine=None, idx=0)

    # No LogicalQubitIDTag
    with pytest.raises(RuntimeError):
        eng.backend._store(Command(engine=eng, gate=Measure, qubits=([qb0],)))

    eng = MainEngine(backend=backend, engine_list=[])

    # No mapper
    with pytest.raises(RuntimeError):
        eng.backend._store(Command(engine=eng, gate=Measure, qubits=([qb0],), tags=(LogicalQubitIDTag(1),)))
