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
from unittest.mock import MagicMock, Mock, patch
from io import StringIO
import json

import math
from projectq.setups import restrictedgateset
from projectq import MainEngine

from projectq.types import WeakQubitRef, Qubit
from projectq.cengines import (BasicMapperEngine, DummyEngine)

from projectq.ops import (R, Swap, H, Rx, Ry, Rz, S, Sdag,
                          T, Tdag, X, Y, Z, SqrtX, MatrixGate,
                          Entangle, Ph, NOT,
                          C,
                          Measure, Allocate, Deallocate, Barrier,
                          All, Command)

# ==============================================================================

_has_boto3 = True
try:
    from botocore.response import StreamingBody
    import botocore
    from projectq.backends._awsbraket import _awsbraket
except ImportError:
    _has_boto3 = False

has_boto3 = pytest.mark.skipif(not _has_boto3,
                               reason="boto3 package is not installed")

# ==============================================================================


'''
Gate availability Tests
'''

@has_boto3
@pytest.mark.parametrize("single_qubit_gate_aspen, is_available_aspen",
                         [(X, True), (Y, True), (Z, True), (H, True),
                          (T, True), (Tdag, True), (S, True), (Sdag, True),
                          (Allocate, True), (Deallocate, True), (SqrtX, False),
                          (Measure, True), (Rx(0.5), True),
                          (Ry(0.5), True), (Rz(0.5), True),
                          (Ph(0.5), False), (R(0.5), True),
                          (Barrier, True), (Entangle, False)])
def test_awsbraket_backend_is_available_aspen(single_qubit_gate_aspen,
                                              is_available_aspen):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True,
                                              device='Aspen-8')
    cmd = Command(eng, single_qubit_gate_aspen, (qubit1, ))
    assert aws_backend.is_available(cmd) == is_available_aspen


@has_boto3
@pytest.mark.parametrize("single_qubit_gate_ionq, is_available_ionq",
                         [(X, True), (Y, True), (Z, True), (H, True),
                          (T, True), (Tdag, True), (S, True), (Sdag, True),
                          (Allocate, True), (Deallocate, True), (SqrtX, True),
                          (Measure, True), (Rx(0.5), True),
                          (Ry(0.5), True), (Rz(0.5), True),
                          (Ph(0.5), False), (R(0.5), False),
                          (Barrier, True), (Entangle, False)])
def test_awsbraket_backend_is_available_ionq(single_qubit_gate_ionq,
                                             is_available_ionq):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='IonQ Device')
    cmd = Command(eng, single_qubit_gate_ionq, (qubit1, ))
    assert aws_backend.is_available(cmd) == is_available_ionq


# TODO: Add MatrixGate to be used as unitary in SV1
unitary_gate = MatrixGate([[0, 1, 0, 0],
                           [1, 0, 0, 0],
                           [0, 0, 0, 1],
                           [0, 0, 1, 0]])


@has_boto3
@pytest.mark.parametrize("single_qubit_gate_sv1, is_available_sv1",
                         [(X, True), (Y, True), (Z, True), (H, True),
                          (T, True), (Tdag, True), (S, True), (Sdag, True),
                          (Allocate, True), (Deallocate, True), (SqrtX, True),
                          (Measure, True), (Rx(0.5), True),
                          (unitary_gate, False),
                          (Ry(0.5), True), (Rz(0.5), True),
                          (Ph(0.5), False), (R(0.5), True),
                          (Barrier, True), (Entangle, False)])
def test_awsbraket_backend_is_available_sv1(single_qubit_gate_sv1,
                                            is_available_sv1):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, single_qubit_gate_sv1, (qubit1, ))
    assert aws_backend.is_available(cmd) == is_available_sv1


@has_boto3
@pytest.mark.parametrize("num_ctrl_qubits_aspen, is_available_aspen",
                         [(0, True), (1, True), (2, True), (3, False)])
def test_awsbraket_backend_is_available_control_not_aspen(
                         num_ctrl_qubits_aspen, is_available_aspen):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits_aspen)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True,
                                              device='Aspen-8')
    cmd = Command(eng, X, (qubit1, ), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_aspen


@has_boto3
@pytest.mark.parametrize("num_ctrl_qubits_ionq, is_available_ionq",
                         [(0, True), (1, True), (2, False), (3, False)])
def test_awsbraket_backend_is_available_control_not_ionq(
                         num_ctrl_qubits_ionq, is_available_ionq):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits_ionq)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='IonQ Device')
    cmd = Command(eng, X, (qubit1, ), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_ionq


@has_boto3
@pytest.mark.parametrize("num_ctrl_qubits_sv1, is_available_sv1",
                         [(0, True), (1, True), (2, True), (3, False)])
def test_awsbraket_backend_is_available_control_not_sv1(
                         num_ctrl_qubits_sv1, is_available_sv1):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits_sv1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, X, (qubit1, ), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_sv1


@has_boto3
@pytest.mark.parametrize("ctrl_singlequbit_aspen, is_available_aspen",
                         [(X, True), (Y, False), (Z, True), (R(0.5), True),
                          (Rx(0.5), False), (Ry(0.5), False),
                          (Rz(0.5), False), (NOT, True)])
def test_awsbraket_backend_is_available_control_singlequbit_aspen(
                         ctrl_singlequbit_aspen, is_available_aspen):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True,
                                              device='Aspen-8')
    cmd = Command(eng, ctrl_singlequbit_aspen, (qubit1, ), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_aspen


@has_boto3
@pytest.mark.parametrize("ctrl_singlequbit_ionq, is_available_ionq",
                         [(X, True), (Y, False), (Z, False), (R(0.5), False),
                          (Rx(0.5), False), (Ry(0.5), False),
                          (Rz(0.5), False)])
def test_awsbraket_backend_is_available_control_singlequbit_ionq(
                         ctrl_singlequbit_ionq, is_available_ionq):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='IonQ Device')
    cmd = Command(eng, ctrl_singlequbit_ionq, (qubit1, ), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_ionq


@has_boto3
@pytest.mark.parametrize("ctrl_singlequbit_sv1, is_available_sv1",
                         [(X, True), (Y, True), (Z, True), (R(0.5), True),
                          (Rx(0.5), False), (Ry(0.5), False),
                          (Rz(0.5), False)])
def test_awsbraket_backend_is_available_control_singlequbit_sv1(
                         ctrl_singlequbit_sv1, is_available_sv1):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, ctrl_singlequbit_sv1, (qubit1, ), controls=qureg)
    assert aws_backend.is_available(cmd) == is_available_sv1


@has_boto3
def test_awsbraket_backend_is_available_swap_aspen():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True,
                                              device='Aspen-8')
    cmd = Command(eng, Swap, (qubit1, qubit2))
    assert aws_backend.is_available(cmd) == True


@has_boto3
def test_awsbraket_backend_is_available_swap_ionq():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True, device='IonQ Device')
    cmd = Command(eng, Swap, (qubit1, qubit2))
    assert aws_backend.is_available(cmd) == True


@has_boto3
def test_awsbraket_backend_is_available_swap_sv1():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, Swap, (qubit1, qubit2))
    assert aws_backend.is_available(cmd) == True


@has_boto3
def test_awsbraket_backend_is_available_control_swap_aspen():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=True,
                                              device='Aspen-8')
    cmd = Command(eng, Swap, (qubit1, qubit2), controls=qureg)
    assert aws_backend.is_available(cmd) == True


@has_boto3
def test_awsbraket_backend_is_available_control_swap_sv1():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    aws_backend = _awsbraket.AWSBraketBackend(use_hardware=False)
    cmd = Command(eng, Swap, (qubit1, qubit2), controls=qureg)
    assert aws_backend.is_available(cmd) == True


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
    cmd = Command(None, gate=SqrtX, qubits=[(qb, )])
    with pytest.raises(Exception) as excinfo:
        backend.receive([cmd])


creds = {
    'AWS_ACCESS_KEY_ID': 'aws_access_key_id',
    'AWS_SECRET_KEY': 'aws_secret_key',
    }

s3_folder = ['S3Bucket', 'S3Directory']

search_value = {
        "devices": [
            {
                "deviceArn": "arn1",
                "deviceName": "name1",
                "deviceType": "SIMULATOR",
                "deviceStatus": "ONLINE",
                "providerName": "pname1",
            },
            {
                "deviceArn": "arn2",
                "deviceName": "name2",
                "deviceType": "QPU",
                "deviceStatus": "OFFLINE",
                "providerName": "pname1",
            },
            {
                "deviceArn": "arn3",
                "deviceName": "Aspen-8",
                "deviceType": "QPU",
                "deviceStatus": "ONLINE",
                "providerName": "pname2",
            },
        ]
    }

device_value_devicecapabilities = json.dumps(
    {
    "braketSchemaHeader": {
        "name": "braket.device_schema.rigetti.rigetti_device_capabilities",
        "version": "1",
    },
    "service": {
        "executionWindows": [
            {
                "executionDay": "Everyday",
                "windowStartHour": "11:00",
                "windowEndHour": "12:00",
            }
        ],
        "shotsRange": [1, 10],
        "deviceLocation": "us-east-1",
    },
    "action": {
        "braket.ir.jaqcd.program": {
            "actionType": "braket.ir.jaqcd.program",
            "version": ["1"],
            "supportedOperations": ["H"],
        }
    },
    "paradigm": {
        "qubitCount": 30,
        "nativeGateSet": ["ccnot", "cy"],
        "connectivity": {"fullyConnected": False,
                         "connectivityGraph": {"1": ["2", "3"]}},
    },
    "deviceParameters": {
        "properties": {"braketSchemaHeader": {"const":
            {"name": "braket.device_schema.rigetti.rigetti_device_parameters",
             "version": "1"}
            }},
        "definitions": {"GateModelParameters": {"properties":
            {"braketSchemaHeader": {"const":
                {"name": "braket.device_schema.gate_model_parameters",
                 "version": "1"}
            }}}},
        },
    }
)

device_value = {
    "deviceName": "Aspen-8",
    "deviceType": "QPU",
    "providerName": "provider1",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": device_value_devicecapabilities,
}


@has_boto3
@patch('boto3.client')
def test_awsbraket_sent_error(mock_boto3_client):

    var_error = 'ServiceQuotaExceededException'
    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.side_effect = \
        botocore.exceptions.ClientError(
            {"Error": {"Code": var_error,
                       "Message": "Msg error for "+var_error}},
             "create_quantum_task"
        )

    backend = _awsbraket.AWSBraketBackend(verbose=True,
                                          credentials=creds,
                                          s3_folder=s3_folder,
                                          use_hardware=True,
                                          device='Aspen-8',
                                          num_runs=10)
    eng = MainEngine(backend=backend)
    qubit = eng.allocate_qubit()
    Rx(0.5) | qubit
    qubit[0].__del__()
    with pytest.raises(TypeError) as excinfo:
        eng.flush()
    # atexit sends another FlushGate, therefore we remove the backend:
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


@has_boto3
def test_awsbraket_sent_error_2():
    backend = _awsbraket.AWSBraketBackend(use_hardware=True, verbose=True)
    mapper = BasicMapperEngine()
    res = dict()
    for i in range(4):
        res[i] = i
    mapper.current_mapping = res
    eng = MainEngine(backend=backend, engine_list=[mapper])
    qubit = eng.allocate_qubit()
    Rx(math.pi) | qubit

    with pytest.raises(Exception) as excinfo:
        SqrtX | qubit
        # no setup to decompose SqrtX gate for Aspen-8,
        # so not accepted by the backend
    dummy = DummyEngine()
    dummy.is_last_engine = True
    eng.next_engine = dummy


arntask = 'arn:aws:braket:us-east-1:id:retrieve_execution'

completed_value = {
    'deviceArn': 'arndevice',
    'deviceParameters': 'parameters',
    'outputS3Bucket': 'amazon-braket-bucket',
    'outputS3Directory': 'complete/directory',
    'quantumTaskArn': 'arntask',
    'shots': 123,
    'status': 'COMPLETED',
    'tags': {
        'tagkey': 'tagvalue'
    }
}
results_json = json.dumps({
    "braketSchemaHeader": {
        "name": "braket.task_result.gate_model_task_result", "version": "1"},
    "measurementProbabilities": {
        "0000": 0.04, "0010": 0.06, "0110": 0.2, "0001": 0.3, "1001": 0.5},
    "measuredQubits": [0, 1, 2],
    }
)
body = StreamingBody(StringIO(results_json), len(results_json))

results_dict = {'ResponseMetadata': {'RequestId': 'CF4CAA48CC18836C',
                                     'HTTPHeaders': {}, },
                'Body': body}


@has_boto3
@patch('boto3.client')
def test_awsbraket_retrieve(mock_boto3_client):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.get_quantum_task.return_value = completed_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.get_object.return_value = results_dict

    backend = _awsbraket.AWSBraketBackend(retrieve_execution=arntask,
                                          credentials=creds, num_retries=2,
                                          verbose=True)

    mapper = BasicMapperEngine()
    res = dict()
    for i in range(4):
        res[i] = i
    mapper.current_mapping = res

    eng = MainEngine(backend=backend, engine_list=[mapper])

    separate_qubit = eng.allocate_qubit()
    qureg = eng.allocate_qureg(3)
    del separate_qubit
    eng.flush()

    prob_dict = eng.backend.get_probabilities([qureg[0], qureg[2], qureg[1]])
    assert prob_dict['000'] == 0.04
    assert prob_dict['101'] == 0.2
    assert prob_dict['010'] == 0.8

    # Unknown qubit and no mapper
    invalid_qubit = [Qubit(eng, 10)]
    with pytest.raises(RuntimeError):
        eng.backend.get_probabilities(invalid_qubit)


qtarntask = {'quantumTaskArn': arntask}
body2 = StreamingBody(StringIO(results_json), len(results_json))
results2_dict = {'ResponseMetadata': {'RequestId': 'CF4CAA48CC18836C',
                                      'HTTPHeaders': {}, },
                'Body': body2}


@has_boto3
@patch('boto3.client')
def test_awsbraket_backend_functional_test(mock_boto3_client):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.return_value = qtarntask
    mock_boto3_client.get_quantum_task.return_value = completed_value
    mock_boto3_client.get_object.return_value = results2_dict

    backend = _awsbraket.AWSBraketBackend(verbose=True,
                                          credentials=creds,
                                          s3_folder=s3_folder,
                                          use_hardware=True,
                                          device='Aspen-8',
                                          num_runs=10,
                                          num_retries=2)
    # no circuit has been executed -> raises exception
    with pytest.raises(RuntimeError):
        backend.get_probabilities([])

    from projectq.setups.default import get_engine_list
    from projectq.backends import CommandPrinter, ResourceCounter

    rcount = ResourceCounter()
    eng = MainEngine(backend=backend, engine_list=[rcount])

    #eng = MainEngine(backend=rcount, engine_list=[backend])

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
