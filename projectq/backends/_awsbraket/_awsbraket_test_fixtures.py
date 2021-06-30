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
#
# ==============================================================================
# This file contains:
#
# - Helper fixtures:
#   * arntask
#   * creds
#   * s3_folder
#   * device_value
#   * search_value
#   * completed_value
# - Setup fixtures for specific tests:
#   * sent_error_setup
#   * retrieve_setup
#   * functional_setup
# ==============================================================================

"""Define test fixtures for the AWSBraket backend."""

import json
from io import StringIO

import pytest

try:
    from botocore.response import StreamingBody
except ImportError:

    class StreamingBody:
        """Dummy implementation of a StreamingBody."""

        def __init__(self, raw_stream, content_length):
            """Initialize a dummy StreamingBody."""


# ==============================================================================


@pytest.fixture
def arntask():
    """Define an ARNTask test setup."""
    return 'arn:aws:braket:us-east-1:id:retrieve_execution'


@pytest.fixture
def creds():
    """Credentials test setup."""
    return {
        'AWS_ACCESS_KEY_ID': 'aws_access_key_id',
        'AWS_SECRET_KEY': 'aws_secret_key',
    }


@pytest.fixture
def s3_folder():
    """S3 folder value test setup."""
    return ['S3Bucket', 'S3Directory']


@pytest.fixture
def device_value():
    """Device value test setup."""
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

    return {
        "deviceName": "Aspen-8",
        "deviceType": "QPU",
        "providerName": "provider1",
        "deviceStatus": "OFFLINE",
        "deviceCapabilities": device_value_devicecapabilities,
    }


@pytest.fixture
def search_value():
    """Search value test setup."""
    return {
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


@pytest.fixture
def completed_value():
    """Completed value test setup."""
    return {
        'deviceArn': 'arndevice',
        'deviceParameters': 'parameters',
        'outputS3Bucket': 'amazon-braket-bucket',
        'outputS3Directory': 'complete/directory',
        'quantumTaskArn': 'arntask',
        'shots': 123,
        'status': 'COMPLETED',
        'tags': {'tagkey': 'tagvalue'},
    }


# ==============================================================================


@pytest.fixture
def sent_error_setup(creds, s3_folder, device_value, search_value):
    """Send error test setup."""
    return creds, s3_folder, search_value, device_value


@pytest.fixture
def results_json():
    """Results test setup."""
    return json.dumps(
        {
            "braketSchemaHeader": {
                "name": "braket.task_result.gate_model_task_result",
                "version": "1",
            },
            "measurementProbabilities": {
                "0000": 0.04,
                "0010": 0.06,
                "0110": 0.2,
                "0001": 0.3,
                "1001": 0.5,
            },
            "measuredQubits": [0, 1, 2],
        }
    )


@pytest.fixture
def retrieve_setup(arntask, creds, device_value, completed_value, results_json):
    """Retrieve test setup."""
    body = StreamingBody(StringIO(results_json), len(results_json))

    results_dict = {
        'ResponseMetadata': {
            'RequestId': 'CF4CAA48CC18836C',
            'HTTPHeaders': {},
        },
        'Body': body,
    }

    return arntask, creds, completed_value, device_value, results_dict


@pytest.fixture
def functional_setup(arntask, creds, s3_folder, search_value, device_value, completed_value, results_json):
    """Functional test setup."""
    qtarntask = {'quantumTaskArn': arntask}
    body2 = StreamingBody(StringIO(results_json), len(results_json))
    results_dict = {
        'ResponseMetadata': {
            'RequestId': 'CF4CAA48CC18836C',
            'HTTPHeaders': {},
        },
        'Body': body2,
    }

    return (
        creds,
        s3_folder,
        search_value,
        device_value,
        qtarntask,
        completed_value,
        results_dict,
    )


# ==============================================================================
