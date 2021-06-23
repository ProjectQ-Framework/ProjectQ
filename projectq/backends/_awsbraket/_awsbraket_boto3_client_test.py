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
""" Test for projectq.backends._awsbraket._awsbraket_boto3_client.py """

import pytest

from ._awsbraket_boto3_client_test_fixtures import *  # noqa: F401,F403

# ==============================================================================

_has_boto3 = True
try:
    import botocore
    from projectq.backends._awsbraket import _awsbraket_boto3_client
except ImportError:
    _has_boto3 = False

has_boto3 = pytest.mark.skipif(not _has_boto3, reason="boto3 package is not installed")

# ==============================================================================


@has_boto3
def test_show_devices(mocker, show_devices_setup):
    creds, search_value, device_value, devicelist_result = show_devices_setup

    mock_boto3_client = mocker.MagicMock(spec=['search_devices', 'get_device'])
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    devicelist = _awsbraket_boto3_client.show_devices(credentials=creds)
    assert devicelist == devicelist_result


# ==============================================================================

completed_value = {
    'deviceArn': 'arndevice',
    'deviceParameters': 'parameters',
    'failureReason': 'None',
    'outputS3Bucket': 'amazon-braket-bucket',
    'outputS3Directory': 'complete/directory',
    'quantumTaskArn': 'arntask',
    'shots': 123,
    'status': 'COMPLETED',
    'tags': {'tagkey': 'tagvalue'},
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

# ------------------------------------------------------------------------------


@has_boto3
@pytest.mark.parametrize(
    "var_status, var_result",
    [
        ('completed', completed_value),
        ('failed', failed_value),
        ('cancelling', cancelling_value),
        ('other', other_value),
    ],
)
def test_retrieve(mocker, var_status, var_result, retrieve_setup):
    arntask, creds, device_value, res_completed, results_dict = retrieve_setup

    mock_boto3_client = mocker.MagicMock(spec=['get_quantum_task', 'get_device', 'get_object'])
    mock_boto3_client.get_quantum_task.return_value = var_result
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.get_object.return_value = results_dict
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    if var_status == 'completed':
        res = _awsbraket_boto3_client.retrieve(credentials=creds, task_arn=arntask)
        assert res == res_completed
    else:
        with pytest.raises(Exception) as exinfo:
            _awsbraket_boto3_client.retrieve(credentials=creds, task_arn=arntask, num_retries=2)
        print(exinfo.value)
        if var_status == 'failed':
            assert (
                str(exinfo.value)
                == "Error while running the code: FAILED. \
The failure reason was: This is a failure reason."
            )

        if var_status == 'cancelling':
            assert str(exinfo.value) == "The job received a CANCEL operation: CANCELLING."
        if var_status == 'other':
            assert (
                str(exinfo.value)
                == "Timeout. The Arn of your submitted job \
is arn:aws:braket:us-east-1:id:taskuuid \
and the status of the job is OTHER."
            )


# ==============================================================================


@has_boto3
def test_retrieve_devicetypes(mocker, retrieve_devicetypes_setup):
    (
        arntask,
        creds,
        device_value,
        results_dict,
        res_completed,
    ) = retrieve_devicetypes_setup

    mock_boto3_client = mocker.MagicMock(spec=['get_quantum_task', 'get_device', 'get_object'])
    mock_boto3_client.get_quantum_task.return_value = completed_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.get_object.return_value = results_dict
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    res = _awsbraket_boto3_client.retrieve(credentials=creds, task_arn=arntask)
    assert res == res_completed


# ==============================================================================


@has_boto3
def test_send_too_many_qubits(mocker, send_too_many_setup):
    (creds, s3_folder, search_value, device_value, info_too_much) = send_too_many_setup

    mock_boto3_client = mocker.MagicMock(spec=['search_devices', 'get_device'])
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    with pytest.raises(_awsbraket_boto3_client.DeviceTooSmall):
        _awsbraket_boto3_client.send(info_too_much, device='name2', credentials=creds, s3_folder=s3_folder)


# ==============================================================================


@has_boto3
@pytest.mark.parametrize(
    "var_status, var_result",
    [
        ('completed', completed_value),
        ('failed', failed_value),
        ('cancelling', cancelling_value),
        ('other', other_value),
    ],
)
def test_send_real_device_online_verbose(mocker, var_status, var_result, real_device_online_setup):

    (
        qtarntask,
        creds,
        s3_folder,
        info,
        search_value,
        device_value,
        res_completed,
        results_dict,
    ) = real_device_online_setup

    mock_boto3_client = mocker.MagicMock(
        spec=['search_devices', 'get_device', 'create_quantum_task', 'get_quantum_task', 'get_object']
    )
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.return_value = qtarntask
    mock_boto3_client.get_quantum_task.return_value = var_result
    mock_boto3_client.get_object.return_value = results_dict
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    # This is a ficticios situation because the job will be always queued
    # at the beginning. After that the status will change at some point in time
    # If the status change while the _get_result loop with num_retries, is
    # active the result will change. We mock this using some preconfigured
    # statuses in var_status for the tests

    if var_status == 'completed':
        res = _awsbraket_boto3_client.send(info, device='name2', credentials=creds, s3_folder=s3_folder, verbose=True)
        assert res == res_completed
    else:
        with pytest.raises(Exception) as exinfo:
            _awsbraket_boto3_client.send(
                info,
                device='name2',
                credentials=creds,
                s3_folder=s3_folder,
                verbose=True,
                num_retries=2,
            )
        print(exinfo.value)
        if var_status == 'failed':
            assert (
                str(exinfo.value)
                == "Error while running the code: FAILED. The failure \
reason was: This is a failure reason."
            )

        if var_status == 'cancelling':
            assert str(exinfo.value) == "The job received a CANCEL operation: CANCELLING."
        if var_status == 'other':
            assert (
                str(exinfo.value)
                == "Timeout. The Arn of your submitted job \
is arn:aws:braket:us-east-1:id:taskuuid \
and the status of the job is OTHER."
            )


# ==============================================================================


@has_boto3
@pytest.mark.parametrize(
    "var_error",
    [
        ('AccessDeniedException'),
        ('DeviceOfflineException'),
        ('InternalServiceException'),
        ('ServiceQuotaExceededException'),
        ('ValidationException'),
    ],
)
def test_send_that_errors_are_caught(mocker, var_error, send_that_error_setup):
    creds, s3_folder, info, search_value, device_value = send_that_error_setup

    mock_boto3_client = mocker.MagicMock(spec=['search_devices', 'get_device', 'create_quantum_task'])
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value
    mock_boto3_client.create_quantum_task.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": var_error, "Message": "Msg error for " + var_error}},
        "create_quantum_task",
    )
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    with pytest.raises(botocore.exceptions.ClientError):
        _awsbraket_boto3_client.send(info, device='name2', credentials=creds, s3_folder=s3_folder, num_retries=2)

    with pytest.raises(_awsbraket_boto3_client.DeviceOfflineError):
        _awsbraket_boto3_client.send(
            info,
            device='unknown',
            credentials=creds,
            s3_folder=s3_folder,
            num_retries=2,
        )


# ==============================================================================


@has_boto3
@pytest.mark.parametrize("var_error", [('ResourceNotFoundException')])
def test_retrieve_error_arn_not_exist(mocker, var_error, arntask, creds):

    mock_boto3_client = mocker.MagicMock(spec=['get_quantum_task'])
    mock_boto3_client.get_quantum_task.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": var_error, "Message": "Msg error for " + var_error}},
        "get_quantum_task",
    )
    mocker.patch('boto3.client', return_value=mock_boto3_client, autospec=True)

    with pytest.raises(botocore.exceptions.ClientError):
        _awsbraket_boto3_client.retrieve(credentials=creds, task_arn=arntask)


# ==============================================================================
