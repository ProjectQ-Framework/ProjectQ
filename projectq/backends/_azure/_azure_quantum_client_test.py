#   Copyright 2022 ProjectQ-Framework (www.projectq.ch)
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

"""Tests for projectq.backends._azure._azure_quantum_client.py."""

from unittest import mock

import pytest

from .._exceptions import DeviceOfflineError, RequestTimeoutError

_has_azure_quantum = True
try:
    import azure.quantum  # noqa: F401

    from projectq.backends._azure._azure_quantum_client import retrieve, send
except ImportError:
    _has_azure_quantum = False

has_azure_quantum = pytest.mark.skipif(not _has_azure_quantum, reason="azure quantum package is not installed")

ZERO_GUID = '00000000-0000-0000-0000-000000000000'


@has_azure_quantum
def test_is_online():
    def get_mock_target():
        mock_target = mock.MagicMock()
        mock_target.current_availability = 'Offline'

        return mock_target

    with pytest.raises(DeviceOfflineError):
        send(
            input_data={},
            metadata={},
            num_shots=100,
            target=get_mock_target(),
            num_retries=1000,
            interval=1,
            verbose=True,
        )


@has_azure_quantum
@pytest.mark.parametrize('verbose', (False, True))
def test_send_ionq(verbose):
    expected_res = {'0': 0.125, '1': 0.125, '2': 0.125, '3': 0.125, '4': 0.125, '5': 0.125, '6': 0.125, '7': 0.125}

    def get_mock_target():
        mock_job = mock.MagicMock()
        mock_job.id = ZERO_GUID
        mock_job.get_results = mock.MagicMock(return_value=expected_res)

        mock_target = mock.MagicMock()
        mock_target.current_availability = 'Available'
        mock_target.submit = mock.MagicMock(return_value=mock_job)

        return mock_target

    input_data = {
        'qubits': 3,
        'circuit': [{'gate': 'h', 'targets': [0]}, {'gate': 'h', 'targets': [1]}, {'gate': 'h', 'targets': [2]}],
    }
    metadata = {'num_qubits': 3, 'meas_map': [0, 1, 2]}

    actual_res = send(
        input_data=input_data,
        metadata=metadata,
        num_shots=100,
        target=get_mock_target(),
        num_retries=1000,
        interval=1,
        verbose=verbose,
    )

    assert actual_res == expected_res


@has_azure_quantum
@pytest.mark.parametrize('verbose', (False, True))
def test_send_quantinuum(verbose):
    expected_res = {
        'c': [
            '010',
            '100',
            '110',
            '000',
            '101',
            '111',
            '000',
            '100',
            '000',
            '110',
            '111',
            '100',
            '100',
            '000',
            '101',
            '110',
            '111',
            '011',
            '101',
            '100',
            '001',
            '110',
            '001',
            '001',
            '100',
            '011',
            '110',
            '000',
            '101',
            '101',
            '010',
            '100',
            '110',
            '111',
            '010',
            '000',
            '010',
            '110',
            '000',
            '110',
            '001',
            '100',
            '110',
            '011',
            '010',
            '111',
            '100',
            '110',
            '100',
            '100',
            '011',
            '000',
            '001',
            '101',
            '000',
            '011',
            '111',
            '101',
            '101',
            '001',
            '011',
            '110',
            '001',
            '010',
            '001',
            '110',
            '101',
            '000',
            '010',
            '001',
            '011',
            '100',
            '110',
            '100',
            '110',
            '101',
            '110',
            '111',
            '110',
            '001',
            '011',
            '101',
            '111',
            '011',
            '100',
            '111',
            '100',
            '001',
            '111',
            '111',
            '100',
            '100',
            '110',
            '101',
            '100',
            '110',
            '100',
            '000',
            '011',
            '000',
        ]
    }

    def get_mock_target():
        mock_job = mock.MagicMock()
        mock_job.id = ZERO_GUID
        mock_job.get_results = mock.MagicMock(return_value=expected_res)

        mock_target = mock.MagicMock()
        mock_target.current_availability = 'Available'
        mock_target.submit = mock.MagicMock(return_value=mock_job)

        return mock_target

    input_data = ''''OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[3];
        creg c[3];
        h q[0];
        h q[1];
        h q[2];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
        measure q[2] -> c[2];
'''

    metadata = {'num_qubits': 3, 'meas_map': [0, 1, 2]}

    actual_res = send(
        input_data=input_data,
        metadata=metadata,
        num_shots=100,
        target=get_mock_target(),
        num_retries=1000,
        interval=1,
        verbose=verbose,
    )

    assert actual_res == expected_res


@has_azure_quantum
@pytest.mark.parametrize('verbose', (False, True))
def test_retrieve_ionq(verbose):
    expected_res = {'0': 0.125, '1': 0.125, '2': 0.125, '3': 0.125, '4': 0.125, '5': 0.125, '6': 0.125, '7': 0.125}

    def get_mock_target():
        mock_job = mock.MagicMock()
        mock_job.id = ZERO_GUID
        mock_job.get_results = mock.MagicMock(return_value=expected_res)

        mock_workspace = mock.MagicMock()
        mock_workspace.get_job = mock.MagicMock(return_value=mock_job)

        mock_target = mock.MagicMock()
        mock_target.current_availability = 'Available'
        mock_target.workspace = mock_workspace
        mock_target.submit = mock.MagicMock(return_value=mock_job)

        return mock_target

    actual_res = retrieve(job_id=ZERO_GUID, target=get_mock_target(), num_retries=1000, interval=1, verbose=verbose)

    assert actual_res == expected_res


@has_azure_quantum
@pytest.mark.parametrize('verbose', (False, True))
def test_retrieve_quantinuum(verbose):
    expected_res = {
        'c': [
            '010',
            '100',
            '110',
            '000',
            '101',
            '111',
            '000',
            '100',
            '000',
            '110',
            '111',
            '100',
            '100',
            '000',
            '101',
            '110',
            '111',
            '011',
            '101',
            '100',
            '001',
            '110',
            '001',
            '001',
            '100',
            '011',
            '110',
            '000',
            '101',
            '101',
            '010',
            '100',
            '110',
            '111',
            '010',
            '000',
            '010',
            '110',
            '000',
            '110',
            '001',
            '100',
            '110',
            '011',
            '010',
            '111',
            '100',
            '110',
            '100',
            '100',
            '011',
            '000',
            '001',
            '101',
            '000',
            '011',
            '111',
            '101',
            '101',
            '001',
            '011',
            '110',
            '001',
            '010',
            '001',
            '110',
            '101',
            '000',
            '010',
            '001',
            '011',
            '100',
            '110',
            '100',
            '110',
            '101',
            '110',
            '111',
            '110',
            '001',
            '011',
            '101',
            '111',
            '011',
            '100',
            '111',
            '100',
            '001',
            '111',
            '111',
            '100',
            '100',
            '110',
            '101',
            '100',
            '110',
            '100',
            '000',
            '011',
            '000',
        ]
    }

    def get_mock_target():
        mock_job = mock.MagicMock()
        mock_job.id = ZERO_GUID
        mock_job.get_results = mock.MagicMock(return_value=expected_res)

        mock_workspace = mock.MagicMock()
        mock_workspace.get_job = mock.MagicMock(return_value=mock_job)

        mock_target = mock.MagicMock()
        mock_target.current_availability = 'Available'
        mock_target.workspace = mock_workspace
        mock_target.submit = mock.MagicMock(return_value=mock_job)

        return mock_target

    actual_res = retrieve(job_id=ZERO_GUID, target=get_mock_target(), num_retries=1000, interval=1, verbose=verbose)

    assert actual_res == expected_res


@has_azure_quantum
@pytest.mark.parametrize('verbose', (False, True))
def test_send_timeout_error(verbose):
    def get_mock_target():
        mock_job = mock.MagicMock()
        mock_job.id = ZERO_GUID
        mock_job.get_results = mock.MagicMock()
        mock_job.get_results.side_effect = TimeoutError()

        mock_target = mock.MagicMock()
        mock_target.current_availability = 'Available'
        mock_target.submit = mock.MagicMock(return_value=mock_job)

        return mock_target

    input_data = {
        'qubits': 3,
        'circuit': [{'gate': 'h', 'targets': [0]}, {'gate': 'h', 'targets': [1]}, {'gate': 'h', 'targets': [2]}],
    }
    metadata = {'num_qubits': 3, 'meas_map': [0, 1, 2]}

    with pytest.raises(RequestTimeoutError):
        _ = send(
            input_data=input_data,
            metadata=metadata,
            num_shots=100,
            target=get_mock_target(),
            num_retries=1000,
            interval=1,
            verbose=verbose,
        )
