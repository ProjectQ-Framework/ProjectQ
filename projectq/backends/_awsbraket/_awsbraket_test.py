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
""" Test for projectq.backends._awsbraket._awsbraket.py"""

import pytest

import copy
import math
from projectq import MainEngine


from projectq.types import WeakQubitRef
from projectq.cengines import (
    BasicMapperEngine,
    DummyEngine,
    AutoReplacer,
    DecompositionRuleSet,
)
from projectq.cengines._replacer import NoGateDecompositionError

from projectq.ops import (
    R,
    Swap,
    H,
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
    CNOT,
    SqrtX,
    MatrixGate,
    Entangle,
    Ph,
    NOT,
    C,
    Measure,
    Allocate,
    Deallocate,
    Barrier,
    All,
    Command,
)

from ._awsbraket_test_fixtures import *  # noqa: F401,F403

# ==============================================================================

_has_boto3 = True
try:
    import botocore
    from projectq.backends._awsbraket import _awsbraket
except ImportError:
    _has_boto3 = False

has_boto3 = pytest.mark.skipif(not _has_boto3, reason="boto3 package is not installed")

# ==============================================================================


@pytest.fixture(params=["mapper", "no_mapper"])
def mapper(request):
    """
    Adds a mapper which changes qubit ids by adding 1
    """
    if request.param == "mapper":

        class TrivialMapper(BasicMapperEngine):
            def __init__(self):
                super().__init__()
                self.current_mapping = dict()

            def receive(self, command_list):
                for cmd in command_list:
                    for qureg in cmd.all_qubits:
                        for qubit in qureg:
                            if qubit.id == -1:
                                continue
                            elif qubit.id not in self.current_mapping:
                                previous_map = self.current_mapping
                                previous_map[qubit.id] = qubit.id
                                self.current_mapping = previous_map
                    self._send_cmd_with_mapped_ids(cmd)

        return TrivialMapper()
    if request.param == "no_mapper":
        return None


# ==============================================================================
'''
Gate availability Tests
'''


@has_boto3
@pytest.mark.parametrize(
    "single_qubit_gate_aspen, is_available_aspen",
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
        (SqrtX, False),
        (Measure, True),
        (Rx(0.5), True),
        (Ry(0.5), True),
        (Rz(0.5), True),
        (Ph(0.5), False),
        (R(0.5), True),
        (Barrier, True),
        (Entangle, False),
    ],
)
def test_awsbraket_backend_is_available_aspen(single_qubit_gate_aspen, is_available_aspen):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='Aspen-8')
    cmd = Command(eng, single_qubit_gate_aspen, (qubit1,))
    assert aws_backend.is_available(cmd) == is_available_aspen


@has_boto3
@pytest.mark.parametrize(
    "single_qubit_gate_ionq, is_available_ionq",
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
        (Ph(0.5), False),
        (R(0.5), False),
        (Barrier, True),
        (Entangle, False),
    ],
)
def test_awsbraket_backend_is_available_ionq(single_qubit_gate_ionq, is_available_ionq):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='IonQ Device')
    cmd = Command(eng, single_qubit_gate_ionq, (qubit1,))
    assert aws_backend.is_available(cmd) == is_available_ionq


@has_boto3
@pytest.mark.parametrize(
    "single_qubit_gate_sv1, is_available_sv1",
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
        # use MatrixGate as unitary gate
        (MatrixGate([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]), False),
        (Ry(0.5), True),
        (Rz(0.5), True),
        (Ph(0.5), False),
        (R(0.5), True),
        (Barrier, True),
        (Entangle, False),
    ],
)
def test_awsbraket_backend_is_available_sv1(single_qubit_gate_sv1, is_available_sv1):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, single_qubit_gate_sv1, (qubit1,))
    assert aws_backend.is_available(cmd) == is_available_sv1


@has_boto3
@pytest.mark.parametrize(
    "num_ctrl_qubits_aspen, is_available_aspen",
    [(0, True), (1, True), (2, True), (3, False)],
)
def test_awsbraket_backend_is_available_control_not_aspen(num_ctrl_qubits_aspen, is_available_aspen):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits_aspen)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='Aspen-8')
    cmd = Command(eng, X, (qubit1,), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_aspen


@has_boto3
@pytest.mark.parametrize(
    "num_ctrl_qubits_ionq, is_available_ionq",
    [(0, True), (1, True), (2, False), (3, False)],
)
def test_awsbraket_backend_is_available_control_not_ionq(num_ctrl_qubits_ionq, is_available_ionq):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits_ionq)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='IonQ Device')
    cmd = Command(eng, X, (qubit1,), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_ionq


@has_boto3
@pytest.mark.parametrize(
    "num_ctrl_qubits_sv1, is_available_sv1",
    [(0, True), (1, True), (2, True), (3, False)],
)
def test_awsbraket_backend_is_available_control_not_sv1(num_ctrl_qubits_sv1, is_available_sv1):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits_sv1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, X, (qubit1,), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_sv1


@has_boto3
@pytest.mark.parametrize(
    "ctrl_singlequbit_aspen, is_available_aspen",
    [
        (X, True),
        (Y, False),
        (Z, True),
        (R(0.5), True),
        (Rx(0.5), False),
        (Ry(0.5), False),
        (Rz(0.5), False),
        (NOT, True),
    ],
)
def test_awsbraket_backend_is_available_control_singlequbit_aspen(ctrl_singlequbit_aspen, is_available_aspen):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='Aspen-8')
    cmd = Command(eng, ctrl_singlequbit_aspen, (qubit1,), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_aspen


@has_boto3
@pytest.mark.parametrize(
    "ctrl_singlequbit_ionq, is_available_ionq",
    [
        (X, True),
        (Y, False),
        (Z, False),
        (R(0.5), False),
        (Rx(0.5), False),
        (Ry(0.5), False),
        (Rz(0.5), False),
    ],
)
def test_awsbraket_backend_is_available_control_singlequbit_ionq(ctrl_singlequbit_ionq, is_available_ionq):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='IonQ Device')
    cmd = Command(eng, ctrl_singlequbit_ionq, (qubit1,), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_ionq


@has_boto3
@pytest.mark.parametrize(
    "ctrl_singlequbit_sv1, is_available_sv1",
    [
        (X, True),
        (Y, True),
        (Z, True),
        (R(0.5), True),
        (Rx(0.5), False),
        (Ry(0.5), False),
        (Rz(0.5), False),
    ],
)
def test_awsbraket_backend_is_available_control_singlequbit_sv1(ctrl_singlequbit_sv1, is_available_sv1):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, ctrl_singlequbit_sv1, (qubit1,), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_sv1


def test_awsbraket_backend_is_available_negative_control():
    backend = _awsbraket.AWSBraketBackend()

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)

    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1]))
    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='1'))
    assert not backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='0'))

    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1, qb2]))
    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1, qb2], control_state='11'))
    assert not backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1, qb2], control_state='01'))


@has_boto3
def test_awsbraket_backend_is_available_swap_aspen():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='Aspen-8')
    cmd = Command(eng, Swap, (qubit1, qubit2))
    assert aws_backend.is_available(cmd)


@has_boto3
def test_awsbraket_backend_is_available_swap_ionq():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='IonQ Device')
    cmd = Command(eng, Swap, (qubit1, qubit2))
    assert aws_backend.is_available(cmd)


@has_boto3
def test_awsbraket_backend_is_available_swap_sv1():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, Swap, (qubit1, qubit2))
    assert aws_backend.is_available(cmd)


@has_boto3
def test_awsbraket_backend_is_available_control_swap_aspen():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='Aspen-8')
    cmd = Command(eng, Swap, (qubit1, qubit2), controls=qureg)
    assert aws_backend.is_available(cmd)


@has_boto3
def test_awsbraket_backend_is_available_control_swap_sv1():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, Swap, (qubit1, qubit2), controls=qureg)
    assert aws_backend.is_available(cmd)


'''
End of Gate availability Tests
'''


@has_boto3
def test_awsbraket_backend_init():
    backend = _awsbraket.AWSBraketBackend(verbose=True, use_hardware=True)
    assert len(backend._circuit) == 0


@has_boto3
def test_awsbraket_empty_circuit():
    backend = _awsbraket.AWSBraketBackend(verbose=True)
    eng = MainEngine(backend=backend)
    eng.flush()


@has_boto3
def test_awsbraket_invalid_command():
    backend = _awsbraket.AWSBraketBackend(use_hardware=True, verbose=True)
    qb = WeakQubitRef(None, 1)
    cmd = Command(None, gate=SqrtX, qubits=[(qb,)])
    with pytest.raises(Exception):
        backend.receive([cmd])


# ==============================================================================


@has_boto3
def test_awsbraket_sent_error(mocker, sent_error_setup):
    creds, s3_folder, search_value, device_value = sent_error_setup

    var_error = 'ServiceQuotaExceededException'
    mock_boto3_client = mocker.MagicMock(spec=['search_devices', 'get_device', 'create_quantum_task'])
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": var_error, "Message": "Msg error for " + var_error}},
        "create_quantum_task",
    )
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    backend = _awsbraket.AWSBraketBackend(
        verbose=True,
        credentials=creds,
        s3_folder=s3_folder,
        use_hardware=True,
        device='Aspen-8',
        num_runs=10,
    )
    eng = MainEngine(backend=backend, verbose=True)
    qubit = eng.allocate_qubit()
    Rx(0.5) | qubit
    qubit[0].__del__()
    with pytest.raises(botocore.exceptions.ClientError):
        eng.flush()

    # atexit sends another FlushGate, therefore we remove the backend:
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


@has_boto3
def test_awsbraket_sent_error_2():
    backend = _awsbraket.AWSBraketBackend(verbose=True, use_hardware=True, device='Aspen-8')
    eng = MainEngine(
        backend=backend,
        engine_list=[AutoReplacer(DecompositionRuleSet())],
        verbose=True,
    )
    qubit = eng.allocate_qubit()
    Rx(math.pi) | qubit

    with pytest.raises(NoGateDecompositionError):
        SqrtX | qubit
        # no setup to decompose SqrtX gate for Aspen-8,
        # so not accepted by the backend
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


# ==============================================================================


@has_boto3
def test_awsbraket_retrieve(mocker, retrieve_setup):
    (arntask, creds, completed_value, device_value, results_dict) = retrieve_setup

    mock_boto3_client = mocker.MagicMock(spec=['get_quantum_task', 'get_device', 'get_object'])
    mock_boto3_client.get_quantum_task.return_value = completed_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.get_object.return_value = results_dict
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    backend = _awsbraket.AWSBraketBackend(retrieve_execution=arntask, credentials=creds, num_retries=2, verbose=True)

    mapper = BasicMapperEngine()
    res = dict()
    for i in range(4):
        res[i] = i
    mapper.current_mapping = res

    eng = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    separate_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(3)
    del separate_qubit
    eng.flush()

    prob_dict = eng.backend.get_probabilities([qureg[0], qureg[2], qureg[1]])
    assert prob_dict['000'] == 0.04
    assert prob_dict['101'] == 0.2
    assert prob_dict['010'] == 0.8

    # Unknown qubit or no mapper
    invalid_qubit = [WeakQubitRef(eng, 10)]
    with pytest.raises(RuntimeError):
        eng.backend.get_probabilities(invalid_qubit)


# ==============================================================================


@has_boto3
def test_awsbraket_backend_functional_test(mocker, functional_setup, mapper):
    (
        creds,
        s3_folder,
        search_value,
        device_value,
        qtarntask,
        completed_value,
        results_dict,
    ) = functional_setup

    mock_boto3_client = mocker.MagicMock(
        spec=['search_devices', 'get_device', 'create_quantum_task', 'get_quantum_task', 'get_object']
    )
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.return_value = qtarntask
    mock_boto3_client.get_quantum_task.return_value = completed_value
    mock_boto3_client.get_object.return_value = results_dict
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    backend = _awsbraket.AWSBraketBackend(
        verbose=True,
        credentials=creds,
        s3_folder=s3_folder,
        use_hardware=True,
        device='Aspen-8',
        num_runs=10,
        num_retries=2,
    )
    # no circuit has been executed -> raises exception
    with pytest.raises(RuntimeError):
        backend.get_probabilities([])

    from projectq.backends import ResourceCounter

    rcount = ResourceCounter()
    engine_list = [rcount]
    if mapper is not None:
        engine_list.append(mapper)
    eng = MainEngine(backend=backend, engine_list=engine_list, verbose=True)

    unused_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(3)

    H | qureg[0]
    S | qureg[1]
    T | qureg[2]
    NOT | qureg[0]
    Y | qureg[1]
    Z | qureg[2]
    Rx(0.1) | qureg[0]
    Ry(0.2) | qureg[1]
    Rz(0.3) | qureg[2]
    R(0.6) | qureg[2]
    C(X) | (qureg[1], qureg[2])
    C(Swap) | (qureg[0], qureg[1], qureg[2])
    H | qureg[0]
    C(Z) | (qureg[1], qureg[2])
    C(R(0.5)) | (qureg[1], qureg[0])
    C(NOT, 2) | ([qureg[2], qureg[1]], qureg[0])
    Swap | (qureg[2], qureg[0])
    Tdag | qureg[1]
    Sdag | qureg[0]

    All(Barrier) | qureg
    del unused_qubit
    # measure; should be all-0 or all-1
    All(Measure) | qureg
    # run the circuit
    eng.flush()

    prob_dict = eng.backend.get_probabilities([qureg[0], qureg[1]])
    assert prob_dict['00'] == pytest.approx(0.84)
    assert prob_dict['01'] == pytest.approx(0.06)

    eng.flush(deallocate_qubits=True)


@has_boto3
def test_awsbraket_functional_test_as_engine(mocker, functional_setup):
    (
        creds,
        s3_folder,
        search_value,
        device_value,
        qtarntask,
        completed_value,
        results_dict,
    ) = functional_setup

    mock_boto3_client = mocker.MagicMock(
        spec=['search_devices', 'get_device', 'create_quantum_task', 'get_quantum_task', 'get_object']
    )
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.return_value = qtarntask
    mock_boto3_client.get_quantum_task.return_value = completed_value
    mock_boto3_client.get_object.return_value = copy.deepcopy(results_dict)
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    backend = _awsbraket.AWSBraketBackend(
        verbose=True,
        credentials=creds,
        s3_folder=s3_folder,
        use_hardware=True,
        device='Aspen-8',
        num_runs=10,
        num_retries=2,
    )
    # no circuit has been executed -> raises exception
    with pytest.raises(RuntimeError):
        backend.get_probabilities([])

    eng = MainEngine(backend=DummyEngine(save_commands=True), engine_list=[backend], verbose=True)

    unused_qubit = eng.allocate_qubit()  # noqa: F841
    qureg = eng.allocate_qureg(3)

    H | qureg[0]
    CNOT | (qureg[0], qureg[1])
    eng.flush()

    assert len(eng.backend.received_commands) == 7
    assert eng.backend.received_commands[4].gate == H
    assert eng.backend.received_commands[4].qubits[0][0].id == qureg[0].id
    assert eng.backend.received_commands[5].gate == X
    assert eng.backend.received_commands[5].control_qubits[0].id == qureg[0].id
    assert eng.backend.received_commands[5].qubits[0][0].id == qureg[1].id

    # NB: also test that we can call eng.flush() multiple times

    mock_boto3_client.get_object.return_value = copy.deepcopy(results_dict)

    CNOT | (qureg[1], qureg[0])
    H | qureg[1]
    eng.flush()

    assert len(eng.backend.received_commands) == 10
    assert eng.backend.received_commands[7].gate == X
    assert eng.backend.received_commands[7].control_qubits[0].id == qureg[1].id
    assert eng.backend.received_commands[7].qubits[0][0].id == qureg[0].id
    assert eng.backend.received_commands[8].gate == H
    assert eng.backend.received_commands[8].qubits[0][0].id == qureg[1].id

    eng.flush(deallocate_qubits=True)
