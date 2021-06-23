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
"""Tests for projectq.setup.awsbraket."""

import pytest
from unittest.mock import patch
import json

# ==============================================================================

_has_boto3 = True
try:
    import projectq.setups.awsbraket

except ImportError:
    _has_boto3 = False

has_boto3 = pytest.mark.skipif(not _has_boto3, reason="boto3 package is not installed")

# ==============================================================================

search_value = {
    "devices": [
        {
            "deviceArn": "arn1",
            "deviceName": "SV1",
            "deviceType": "SIMULATOR",
            "deviceStatus": "ONLINE",
            "providerName": "pname1",
        },
        {
            "deviceArn": "arn2",
            "deviceName": "Aspen-8",
            "deviceType": "QPU",
            "deviceStatus": "OFFLINE",
            "providerName": "pname1",
        },
        {
            "deviceArn": "arn3",
            "deviceName": "IonQ Device",
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
                "fullyConnected": False,
                "connectivityGraph": {"1": ["2", "3"]},
            },
        },
        "deviceParameters": {
            "properties": {
                "braketSchemaHeader": {
                    "const": {
                        "name": "braket.device_schema.rigetti.rigetti_device_parameters",
                        "version": "1",
                    }
                }
            },
            "definitions": {
                "GateModelParameters": {
                    "properties": {
                        "braketSchemaHeader": {
                            "const": {
                                "name": "braket.device_schema.gate_model_parameters",
                                "version": "1",
                            }
                        }
                    }
                }
            },
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

creds = {
    'AWS_ACCESS_KEY_ID': 'aws_access_key_id',
    'AWS_SECRET_KEY': 'aws_secret_key',
}


@has_boto3
@patch('boto3.client')
@pytest.mark.parametrize("var_device", ['SV1', 'Aspen-8', 'IonQ Device'])
def test_awsbraket_get_engine_list(mock_boto3_client, var_device):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value

    engine_list = projectq.setups.awsbraket.get_engine_list(credentials=creds, device=var_device)
    assert len(engine_list) == 12


@has_boto3
@patch('boto3.client')
def test_awsbraket_error(mock_boto3_client):

    mock_boto3_client.return_value = mock_boto3_client
    mock_boto3_client.search_devices.return_value = search_value
    mock_boto3_client.get_device.return_value = device_value

    with pytest.raises(projectq.setups.awsbraket.DeviceOfflineError):
        projectq.setups.awsbraket.get_engine_list(credentials=creds, device='Imaginary')
