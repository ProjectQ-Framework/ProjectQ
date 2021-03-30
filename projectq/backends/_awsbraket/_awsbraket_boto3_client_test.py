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

""" Test for projectq.backends._awsbraket._awsbraket_boto3_client.py """

import pytest
from unittest.mock import MagicMock, Mock, patch

from io import StringIO

import json

# ==============================================================================

_has_boto3 = True
try:
    from botocore.response import StreamingBody
    import botocore
    from projectq.backends._awsbraket import _awsbraket_boto3_client
except ImportError:
    _has_boto3 = False

has_boto3 = pytest.mark.skipif(not _has_boto3,
                               reason="boto3 package is not installed")

# ==============================================================================

results_json = json.dumps({
    "braketSchemaHeader": {
        "name": "braket.task_result.gate_model_task_result", "version": "1"},
    "measurementProbabilities": {
        "000": 0.1, "010": 0.4, "110": 0.1, "001": 0.1, "111": 0.3},
    "measuredQubits": [0, 1, 2],
}
                          )

@pytest.fixture
def results_dict():
    body = StreamingBody(StringIO(results_json), len(results_json))
    return {
        'ResponseMetadata': {
            'RequestId': 'CF4CAA48CC18836C',  'HTTPHeaders': {}, }, 'Body': body}


res_completed = {"000": 0.1, "010": 0.4, "110": 0.1, "001": 0.1, "111": 0.3}

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
                "deviceName": "name3",
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
        "connectivity": {
            "fullyConnected": False, "connectivityGraph": {"1": ["2", "3"]}},
    },
    "deviceParameters": {
        "properties": {"braketSchemaHeader": {"const":
            {"name": "braket.device_schema.rigetti.rigetti_device_parameters",
             "version": "1"}
            }},
        "definitions": {
            "GateModelParameters": {"properties": {
                "braketSchemaHeader": {
                    "const": {
                        "name": "braket.device_schema.gate_model_parameters",
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

devicelist_result = {
    'name1': {'coupling_map': {},
              'deviceArn': 'arn1', 'location': 'us-east-1',
              'nq': 30, 'version': '1',
              'deviceParameters':
                    {'name':
                     'braket.device_schema.rigetti.rigetti_device_parameters',
                     'version': '1'},
              'deviceModelParameters':
                    {'name': 'braket.device_schema.gate_model_parameters',
                     'version': '1'}
            },
    'name2': {'coupling_map': {'1': ['2', '3']},
              'deviceArn': 'arn2', 'location': 'us-east-1',
              'nq': 30, 'version': '1',
              'deviceParameters':
                    {'name':
                     'braket.device_schema.rigetti.rigetti_device_parameters',
                     'version': '1'},
              'deviceModelParameters':
                    {'name': 'braket.device_schema.gate_model_parameters',
                     'version': '1'}
            },
    'name3': {'coupling_map': {'1': ['2', '3']},
              'deviceArn': 'arn3', 'location': 'us-east-1',
              'nq': 30, 'version': '1',
              'deviceParameters': {
                  'name':
                    'braket.device_schema.rigetti.rigetti_device_parameters',
                  'version': '1'},
              'deviceModelParameters':
                    {'name': 'braket.device_schema.gate_model_parameters',
                     'version': '1'}
        }
    }

creds = {
    'AWS_ACCESS_KEY_ID': 'aws_access_key_id',
    'AWS_SECRET_KEY': 'aws_secret_key',
    }

arntask = 'arn:aws:braket:us-east-1:id:taskuuid'

qtarntask = {'quantumTaskArn': arntask}


@has_boto3
@patch('boto3.client')
def test_show_devices(mock_boto3_client):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value

    devicelist = _awsbraket_boto3_client.show_devices(credentials=creds)
    assert devicelist == devicelist_result


completed_value = {
    'deviceArn': 'arndevice',
    'deviceParameters': 'parameters',
    'failureReason': 'None',
    'outputS3Bucket': 'amazon-braket-bucket',
    'outputS3Directory': 'complete/directory',
    'quantumTaskArn': 'arntask',
    'shots': 123,
    'status': 'COMPLETED',
    'tags': {
        'tagkey': 'tagvalue'
    }
}

failed_value = {
    'failureReason': 'This is a failure reason',
    'outputS3Bucket': 'amazon-braket-bucket',
    'outputS3Directory': 'complete/directory',
    'status': 'FAILED',
}

cancelling_value = {
    'failureReason': 'None',
    'outputS3Bucket': 'amazon-braket-bucket',
    'outputS3Directory': 'complete/directory',
    'status': 'CANCELLING',
}

other_value = {
    'failureReason': 'None',
    'outputS3Bucket': 'amazon-braket-bucket',
    'outputS3Directory': 'complete/directory',
    'status': 'OTHER',
}


@has_boto3
@patch('boto3.client')
@pytest.mark.parametrize(
    "var_status, var_result", [(
        'completed', completed_value), ('failed', failed_value), (
            'cancelling', cancelling_value), ('other', other_value)])
def test_retrieve(mock_boto3_client, var_status, var_result, results_dict):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.get_quantum_task.return_value = var_result
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.get_object.return_value = results_dict

    if var_status == 'completed':
        res = _awsbraket_boto3_client.retrieve(
            credentials=creds, taskArn=arntask)
        assert res == res_completed
    else:
        with pytest.raises(Exception) as exinfo:
            _awsbraket_boto3_client.retrieve(
                credentials=creds, taskArn=arntask, num_retries=2)
        print(exinfo.value)
        if var_status == 'failed':
            assert str(exinfo.value) == \
                "Error while running the code: FAILED. \
The failure reason was: This is a failure reason."
        if var_status == 'cancelling':
            assert str(exinfo.value) == \
                "The job received a CANCEL operation: CANCELLING."
        if var_status == 'other':
            assert str(exinfo.value) == \
                "Timeout. The Arn of your submitted job \
is arn:aws:braket:us-east-1:id:taskuuid \
and the status of the job is OTHER."


@pytest.fixture(params=["qpu", "sim"])
def var(request):
    if request.param == "qpu":
        body_qpu = StreamingBody(StringIO(results_json), len(results_json))
        results_dict = {
            'ResponseMetadata': {
                'RequestId': 'CF4CAA48CC18836C',
                'HTTPHeaders': {}, }, 'Body': body_qpu}

        device_value = {
            "deviceName": "Aspen-8",
            "deviceType": "QPU",
            "providerName": "provider1",
            "deviceStatus": "OFFLINE",
            "deviceCapabilities": device_value_devicecapabilities,
        }

        res_completed = {"000": 0.1, "010": 0.4, "110": 0.1, "001": 0.1, "111": 0.3}
    else:
        results_json_simulator = json.dumps({
            "braketSchemaHeader": {
                "name": "braket.task_result.gate_model_task_result", "version": "1"},
            "measurements": [[0, 0], [0, 1], [1, 1], [0, 1], [0, 1],
                             [1, 1], [1, 1], [1, 1], [1, 1], [1, 1]],
            "measuredQubits": [0, 1],
            }
        )
        body_simulator = \
            StreamingBody(
                StringIO(results_json_simulator), len(
                    results_json_simulator))
        results_dict = {
            'ResponseMetadata': {
                'RequestId': 'CF4CAA48CC18836C',
                'HTTPHeaders': {}, }, 'Body': body_simulator}

        device_value = {
            "deviceName": "SV1",
            "deviceType": "SIMULATOR",
            "providerName": "providerA",
            "deviceStatus": "ONLINE",
            "deviceCapabilities": device_value_devicecapabilities,
        }

        res_completed = {"00": 0.1, "01": 0.3, "11": 0.6}
    return (device_value, results_dict, res_completed)


@has_boto3
@patch('boto3.client')
def test_retrieve_devicetypes(mock_boto3_client, var):
    var_device_value, var_result_dict, var_res_completed = var
    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.get_quantum_task.return_value = completed_value
    mock_boto3_client.get_device.return_value = var_device_value
    mock_boto3_client.get_object.return_value = var_result_dict

    res = _awsbraket_boto3_client.retrieve(credentials=creds, taskArn=arntask)
    assert res == var_res_completed


info_too_much = {
    'circuit':
    '{"braketSchemaHeader":'
    '{"name": "braket.ir.jaqcd.program", "version": "1"}, '
    '"results": [], "basis_rotation_instructions": [], '
    '"instructions": [{"target": 0, "type": "h"}, {\
        "target": 1, "type": "h"}, {\
            "control": 1, "target": 2, "type": "cnot"}]}',
    'nq':
    100,
    'shots':
    1,
    'backend': {
        'name': 'name2'
    }
}
s3_folder = ['S3Bucket', "S3Directory"]


@has_boto3
@patch('boto3.client')
def test_send_too_many_qubits(mock_boto3_client):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value

    with pytest.raises(_awsbraket_boto3_client.DeviceTooSmall):
        _awsbraket_boto3_client.send(info_too_much,
                                     device='name2',
                                     credentials=creds,
                                     s3_folder=s3_folder)


info = {
    'circuit':
    '{"braketSchemaHeader":'
    '{"name": "braket.ir.jaqcd.program", "version": "1"}, '
    '"results": [], "basis_rotation_instructions": [], '
    '"instructions": [{"target": 0, "type": "h"}, {\
        "target": 1, "type": "h"}, {\
            "control": 1, "target": 2, "type": "cnot"}]}',
    'nq':
    10,
    'shots':
    1,
    'backend': {
        'name': 'name2'
    }
}

@pytest.fixture
def results2_dict():
    body2 = StreamingBody(StringIO(results_json), len(results_json))
    return {
        'ResponseMetadata': {
            'RequestId': 'CF4CAA48CC18836C',  'HTTPHeaders': {}, }, 'Body': body2}


@has_boto3
@patch('boto3.client')
@pytest.mark.parametrize(
    "var_status, var_result", [(
        'completed', completed_value), ('failed', failed_value), (
            'cancelling', cancelling_value), ('other', other_value)])
def test_send_real_device_online_verbose(mock_boto3_client,
                                         var_status, var_result, results2_dict):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.return_value = qtarntask
    mock_boto3_client.get_quantum_task.return_value = var_result
    mock_boto3_client.get_object.return_value = results2_dict

    # This is a ficticios situation because the job will be always queued
    # at the beginning. After that the status will change at some point in time
    # If the status change while the _get_result loop with num_retries, is
    # active the result will change. We mock this using some preconfigured
    # statuses in var_status for the tests

    if var_status == 'completed':
        res = _awsbraket_boto3_client.send(info,
                                           device='name2',
                                           credentials=creds,
                                           s3_folder=s3_folder,
                                           verbose=True)
        assert res == res_completed
    else:
        with pytest.raises(Exception) as exinfo:
            _awsbraket_boto3_client.send(info,
                                         device='name2',
                                         credentials=creds,
                                         s3_folder=s3_folder,
                                         verbose=True,
                                         num_retries=2)
        print(exinfo.value)
        if var_status == 'failed':
            assert str(exinfo.value) == \
                "Error while running the code: FAILED. The failure \
reason was: This is a failure reason."
        if var_status == 'cancelling':
            assert str(exinfo.value) == \
                "The job received a CANCEL operation: CANCELLING."
        if var_status == 'other':
            assert str(exinfo.value) == \
                "Timeout. The Arn of your submitted job \
is arn:aws:braket:us-east-1:id:taskuuid \
and the status of the job is OTHER."


body3 = StreamingBody(StringIO(results_json), len(results_json))
results3_dict = {
    'ResponseMetadata': {
        'RequestId': 'CF4CAA48CC18836C',  'HTTPHeaders': {}, }, 'Body': body3}


@has_boto3
@patch('boto3.client')
@pytest.mark.parametrize(
    "var_error", [('AccessDeniedException'), (
        'DeviceOfflineException'), ('InternalServiceException'), (
            'ServiceQuotaExceededException'), ('ValidationException')])
def test_send_that_errors_are_caught(mock_boto3_client, var_error):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.side_effect = \
        botocore.exceptions.ClientError(
            {"Error": {
                "Code": var_error,
                "Message": "Msg error for "+var_error}}, "create_quantum_task")

    with pytest.raises(botocore.exceptions.ClientError) as exinfo:
        _awsbraket_boto3_client.send(info,
                                     device='name2',
                                     credentials=creds,
                                     s3_folder=s3_folder,
                                     num_retries=2)

@has_boto3
@patch('boto3.client')
@pytest.mark.parametrize("var_error", [('ResourceNotFoundException')])
def test_retrieve_error_arn_not_exist(mock_boto3_client, var_error):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.get_quantum_task.side_effect = \
        botocore.exceptions.ClientError(
            {"Error": {
                "Code": var_error,
                "Message": "Msg error for "+var_error}}, "get_quantum_task")
    
    with pytest.raises(botocore.exceptions.ClientError) as exinfo:
        _awsbraket_boto3_client.retrieve(credentials=creds, taskArn=arntask)

