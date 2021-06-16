# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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

"""Tests for projectq.backends._ionq._ionq.py."""

import math
from unittest import mock

import pytest

from projectq import MainEngine
from projectq.backends._ionq import _ionq, _ionq_http_client
from projectq.backends._ionq._ionq_exc import (
    InvalidCommandError,
    MidCircuitMeasurementError,
)
from projectq.backends._ionq._ionq_mapper import BoundedQubitMapper
from projectq.cengines import DummyEngine
from projectq.ops import (
    CNOT,
    All,
    Allocate,
    Barrier,
    Command,
    Deallocate,
    Entangle,
    H,
    Measure,
    Ph,
    R,
    Rx,
    Rxx,
    Ry,
    Rz,
    S,
    Sdag,
    SqrtX,
    T,
    Tdag,
    Toffoli,
    X,
    Y,
    Z,
)
from projectq.types import WeakQubitRef


@pytest.fixture(scope='function')
def mapper_factory():
    def _factory(n=4):
        return BoundedQubitMapper(n)

    return _factory


# Prevent any requests from making it out.
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.mark.parametrize(
    "single_qubit_gate, is_available",
    [
        (X, True),
        (Y, True),
        (Z, True),
        (H, True),
        (T, True),
        (Tdag, True),
        (S, True),
        (Sdag, True),
        (Allocate, True),
        (Deallocate, True),
        (SqrtX, True),
        (Measure, True),
        (Rx(0.5), True),
        (Ry(0.5), True),
        (Rz(0.5), True),
        (R(0.5), False),
        (Barrier, True),
        (Entangle, False),
    ],
)
def test_ionq_backend_is_available(single_qubit_gate, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    ionq_backend = _ionq.IonQBackend()
    cmd = Command(eng, single_qubit_gate, (qubit1,))
    assert ionq_backend.is_available(cmd) is is_available


# IonQ supports up to 7 control qubits.
@pytest.mark.parametrize(
    "num_ctrl_qubits, is_available",
    [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
        (8, False),
    ],
)
def test_ionq_backend_is_available_control_not(num_ctrl_qubits, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)
    ionq_backend = _ionq.IonQBackend()
    cmd = Command(eng, X, (qubit1,), controls=qureg)
    assert ionq_backend.is_available(cmd) is is_available


def test_ionq_backend_is_available_negative_control():
    backend = _ionq.IonQBackend()

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)

    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1]))
    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='1'))
    assert not backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='0'))

    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1, qb2]))
    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1, qb2], control_state='11'))
    assert not backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1, qb2], control_state='01'))


def test_ionq_backend_init():
    """Test initialized backend has an empty circuit"""
    backend = _ionq.IonQBackend(verbose=True, use_hardware=True)
    assert hasattr(backend, '_circuit')
    circuit = getattr(backend, '_circuit')
    assert isinstance(circuit, list)
    assert len(circuit) == 0


def test_ionq_empty_circuit():
    """Test that empty circuits are still flushable."""
    backend = _ionq.IonQBackend(verbose=True)
    eng = MainEngine(backend=backend)
    eng.flush()


def test_ionq_no_circuit_executed():
    """Test that one can't retrieve probabilities if no circuit was run."""
    backend = _ionq.IonQBackend(verbose=True)
    eng = MainEngine(backend=backend)
    # no circuit has been executed -> raises exception
    with pytest.raises(RuntimeError):
        backend.get_probabilities([])
    eng.flush()


def test_ionq_get_probability(monkeypatch, mapper_factory):
    """Test a shortcut for getting a specific state's probability"""

    def mock_retrieve(*args, **kwargs):
        return {
            'nq': 3,
            'shots': 10,
            'output_probs': {'3': 0.4, '0': 0.6},
            'meas_mapped': [0, 1],
            'meas_qubit_ids': [1, 2],
        }

    monkeypatch.setattr(_ionq_http_client, "retrieve", mock_retrieve)
    backend = _ionq.IonQBackend(
        retrieve_execution="a3877d18-314f-46c9-86e7-316bc4dbe968",
        verbose=True,
    )
    eng = MainEngine(backend=backend, engine_list=[mapper_factory()])

    unused_qubit = eng.allocate_qubit()  # noqa: F841
    qureg = eng.allocate_qureg(2)
    # entangle the qureg
    Ry(math.pi / 2) | qureg[0]
    Rx(math.pi / 2) | qureg[0]
    Rx(math.pi / 2) | qureg[0]
    Ry(math.pi / 2) | qureg[0]
    Rxx(math.pi / 2) | (qureg[0], qureg[1])
    Rx(7 * math.pi / 2) | qureg[0]
    Ry(7 * math.pi / 2) | qureg[0]
    Rx(7 * math.pi / 2) | qureg[1]

    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    eng.flush()
    assert eng.backend.get_probability('11', qureg) == pytest.approx(0.4)
    assert eng.backend.get_probability('00', qureg) == pytest.approx(0.6)

    with pytest.raises(ValueError) as excinfo:
        eng.backend.get_probability('111', qureg)
    assert str(excinfo.value) == 'Desired state and register must be the same length!'


def test_ionq_get_probabilities(monkeypatch, mapper_factory):
    """Test a shortcut for getting a specific state's probability"""

    def mock_retrieve(*args, **kwargs):
        return {
            'nq': 3,
            'shots': 10,
            'output_probs': {'1': 0.4, '0': 0.6},
            'meas_mapped': [1],
            'meas_qubit_ids': [1],
        }

    monkeypatch.setattr(_ionq_http_client, "retrieve", mock_retrieve)
    backend = _ionq.IonQBackend(
        retrieve_execution="a3877d18-314f-46c9-86e7-316bc4dbe968",
        verbose=True,
    )
    eng = MainEngine(backend=backend, engine_list=[mapper_factory()])
    qureg = eng.allocate_qureg(2)
    q0, q1 = qureg
    H | q0
    CNOT | (q0, q1)
    Measure | q1
    # run the circuit
    eng.flush()
    assert eng.backend.get_probability('01', qureg) == pytest.approx(0.4)
    assert eng.backend.get_probability('00', qureg) == pytest.approx(0.6)
    assert eng.backend.get_probability('1', [qureg[1]]) == pytest.approx(0.4)
    assert eng.backend.get_probability('0', [qureg[1]]) == pytest.approx(0.6)


def test_ionq_invalid_command():
    """Test that this backend raises out with invalid commands."""

    # Ph gate is not a valid gate
    qb = WeakQubitRef(None, 1)
    cmd = Command(None, gate=Ph(math.pi), qubits=[(qb,)])
    backend = _ionq.IonQBackend(verbose=True)
    with pytest.raises(InvalidCommandError):
        backend.receive([cmd])


def test_ionq_sent_error(monkeypatch, mapper_factory):
    """Test that errors on "send" will raise back out."""
    # patch send
    type_error = TypeError()
    mock_send = mock.MagicMock(side_effect=type_error)
    monkeypatch.setattr(_ionq_http_client, "send", mock_send)

    backend = _ionq.IonQBackend()
    eng = MainEngine(
        backend=backend,
        engine_list=[mapper_factory()],
        verbose=True,
    )
    qubit = eng.allocate_qubit()
    Rx(0.5) | qubit
    with pytest.raises(Exception) as excinfo:
        qubit[0].__del__()
        eng.flush()

    # verbose=True on the engine re-raises errors instead of compacting them.
    assert type_error is excinfo.value

    # atexit sends another FlushGate, therefore we remove the backend:
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


def test_ionq_send_nonetype_response_error(monkeypatch, mapper_factory):
    """Test that no return value from "send" will raise a runtime error."""
    # patch send
    mock_send = mock.MagicMock(return_value=None)
    monkeypatch.setattr(_ionq_http_client, "send", mock_send)

    backend = _ionq.IonQBackend()
    eng = MainEngine(
        backend=backend,
        engine_list=[mapper_factory()],
        verbose=True,
    )
    qubit = eng.allocate_qubit()
    Rx(0.5) | qubit
    with pytest.raises(RuntimeError) as excinfo:
        eng.flush()

    # verbose=True on the engine re-raises errors instead of compacting them.
    assert str(excinfo.value) == "Failed to submit job to the server!"

    # atexit sends another FlushGate, therefore we remove the backend:
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


def test_ionq_retrieve(monkeypatch, mapper_factory):
    """Test that initializing a backend with a jobid will fetch that job's results to use as its own"""

    def mock_retrieve(*args, **kwargs):
        return {
            'nq': 3,
            'shots': 10,
            'output_probs': {'3': 0.4, '0': 0.6},
            'meas_mapped': [0, 1],
            'meas_qubit_ids': [1, 2],
        }

    monkeypatch.setattr(_ionq_http_client, "retrieve", mock_retrieve)
    backend = _ionq.IonQBackend(
        retrieve_execution="a3877d18-314f-46c9-86e7-316bc4dbe968",
        verbose=True,
    )
    eng = MainEngine(backend=backend, engine_list=[mapper_factory()])

    unused_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(2)
    # entangle the qureg
    Ry(math.pi / 2) | qureg[0]
    Rx(math.pi / 2) | qureg[0]
    Rx(math.pi / 2) | qureg[0]
    Ry(math.pi / 2) | qureg[0]
    Rxx(math.pi / 2) | (qureg[0], qureg[1])
    Rx(7 * math.pi / 2) | qureg[0]
    Ry(7 * math.pi / 2) | qureg[0]
    Rx(7 * math.pi / 2) | qureg[1]
    del unused_qubit
    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    eng.flush()
    prob_dict = eng.backend.get_probabilities([qureg[0], qureg[1]])
    assert prob_dict['11'] == pytest.approx(0.4)
    assert prob_dict['00'] == pytest.approx(0.6)

    # Unknown qubit
    invalid_qubit = [WeakQubitRef(eng, 10)]
    probs = eng.backend.get_probabilities(invalid_qubit)
    assert {'0': 1} == probs


def test_ionq_retrieve_nonetype_response_error(monkeypatch, mapper_factory):
    """Test that initializing a backend with a jobid will fetch that job's results to use as its own"""

    def mock_retrieve(*args, **kwargs):
        return None

    monkeypatch.setattr(_ionq_http_client, "retrieve", mock_retrieve)
    backend = _ionq.IonQBackend(
        retrieve_execution="a3877d18-314f-46c9-86e7-316bc4dbe968",
        verbose=True,
    )
    eng = MainEngine(
        backend=backend,
        engine_list=[mapper_factory()],
        verbose=True,
    )

    unused_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(2)
    # entangle the qureg
    Ry(math.pi / 2) | qureg[0]
    Rx(math.pi / 2) | qureg[0]
    Rx(math.pi / 2) | qureg[0]
    Ry(math.pi / 2) | qureg[0]
    Rxx(math.pi / 2) | (qureg[0], qureg[1])
    Rx(7 * math.pi / 2) | qureg[0]
    Ry(7 * math.pi / 2) | qureg[0]
    Rx(7 * math.pi / 2) | qureg[1]
    del unused_qubit
    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    with pytest.raises(RuntimeError) as excinfo:
        eng.flush()

    exc = excinfo.value
    expected_err = "Failed to retrieve job with id: 'a3877d18-314f-46c9-86e7-316bc4dbe968'!"
    assert str(exc) == expected_err


def test_ionq_backend_functional_test(monkeypatch, mapper_factory):
    """Test that the backend can handle a valid circuit with valid results."""
    expected = {
        'nq': 3,
        'shots': 10,
        'meas_mapped': [1, 2],
        'meas_qubit_ids': [1, 2],
        'circuit': [
            {'gate': 'ry', 'rotation': 0.5, 'targets': [1]},
            {'gate': 'rx', 'rotation': 0.5, 'targets': [1]},
            {'gate': 'rx', 'rotation': 0.5, 'targets': [1]},
            {'gate': 'ry', 'rotation': 0.5, 'targets': [1]},
            {'gate': 'xx', 'rotation': 0.5, 'targets': [1, 2]},
            {'gate': 'rx', 'rotation': 3.5, 'targets': [1]},
            {'gate': 'ry', 'rotation': 3.5, 'targets': [1]},
            {'gate': 'rx', 'rotation': 3.5, 'targets': [2]},
        ],
    }

    def mock_send(*args, **kwargs):
        assert args[0] == expected
        return {
            'nq': 3,
            'shots': 10,
            'output_probs': {'3': 0.4, '0': 0.6},
            'meas_mapped': [1, 2],
            'meas_qubit_ids': [1, 2],
        }

    monkeypatch.setattr(_ionq_http_client, "send", mock_send)
    backend = _ionq.IonQBackend(verbose=True, num_runs=10)
    eng = MainEngine(
        backend=backend,
        engine_list=[mapper_factory()],
        verbose=True,
    )
    unused_qubit = eng.allocate_qubit()  # noqa: F841
    qureg = eng.allocate_qureg(2)

    # entangle the qureg
    Ry(0.5) | qureg[0]
    Rx(0.5) | qureg[0]
    Rx(0.5) | qureg[0]
    Ry(0.5) | qureg[0]
    Rxx(0.5) | (qureg[0], qureg[1])
    Rx(3.5) | qureg[0]
    Ry(3.5) | qureg[0]
    Rx(3.5) | qureg[1]
    All(Barrier) | qureg
    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    eng.flush()
    prob_dict = eng.backend.get_probabilities([qureg[0], qureg[1]])
    assert prob_dict['11'] == pytest.approx(0.4)
    assert prob_dict['00'] == pytest.approx(0.6)


def test_ionq_backend_functional_aliases_test(monkeypatch, mapper_factory):
    """Test that sub-classed or aliased gates are handled correctly."""
    # using alias gates, for coverage
    expected = {
        'nq': 4,
        'shots': 10,
        'meas_mapped': [2, 3],
        'meas_qubit_ids': [2, 3],
        'circuit': [
            {'gate': 'x', 'targets': [0]},
            {'gate': 'x', 'targets': [1]},
            {'controls': [0], 'gate': 'x', 'targets': [2]},
            {'controls': [1], 'gate': 'x', 'targets': [2]},
            {'controls': [0, 1], 'gate': 'x', 'targets': [3]},
            {'gate': 's', 'targets': [2]},
            {'gate': 'si', 'targets': [3]},
        ],
    }

    def mock_send(*args, **kwargs):
        assert args[0] == expected
        return {
            'nq': 4,
            'shots': 10,
            'output_probs': {'1': 0.9},
            'meas_mapped': [2, 3],
        }

    monkeypatch.setattr(_ionq_http_client, "send", mock_send)
    backend = _ionq.IonQBackend(verbose=True, num_runs=10)
    eng = MainEngine(
        backend=backend,
        engine_list=[mapper_factory(9)],
        verbose=True,
    )
    # Do some stuff with a circuit. Get weird with it.
    circuit = eng.allocate_qureg(4)
    qubit1, qubit2, qubit3, qubit4 = circuit
    All(X) | [qubit1, qubit2]
    CNOT | (qubit1, qubit3)
    CNOT | (qubit2, qubit3)
    Toffoli | (qubit1, qubit2, qubit4)
    Barrier | circuit
    S | qubit3
    Sdag | qubit4
    All(Measure) | [qubit3, qubit4]

    # run the circuit
    eng.flush()
    prob_dict = eng.backend.get_probabilities([qubit3, qubit4])
    assert prob_dict['10'] == pytest.approx(0.9)


def test_ionq_no_midcircuit_measurement(monkeypatch, mapper_factory):
    """Test that attempts to measure mid-circuit raise exceptions."""

    def mock_send(*args, **kwargs):
        return {
            'nq': 1,
            'shots': 10,
            'output_probs': {'0': 0.4, '1': 0.6},
        }

    monkeypatch.setattr(_ionq_http_client, "send", mock_send)

    # Create a backend to use with an engine.
    backend = _ionq.IonQBackend(verbose=True, num_runs=10)
    eng = MainEngine(
        backend=backend,
        engine_list=[mapper_factory()],
        verbose=True,
    )
    qubit = eng.allocate_qubit()
    X | qubit
    Measure | qubit
    with pytest.raises(MidCircuitMeasurementError):
        X | qubit

    # atexit sends another FlushGate, therefore we remove the backend:
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.active_qubits = []
    eng.next_engine = dummy
