# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Tests for projectq.backends._ionq._ionq_http_client.py."""

from unittest import mock

import pytest
import requests
from requests.compat import urljoin

from projectq.backends._ionq import _ionq_http_client
from projectq.backends._ionq._ionq_exc import JobSubmissionError, RequestTimeoutError


# Insure that no HTTP request can be made in all tests in this module
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr('requests.sessions.Session.request')


_api_url = 'https://api.ionq.co/v0.1/jobs/'


def test_authenticate():
    ionq_session = _ionq_http_client.IonQ()
    ionq_session.authenticate('NotNone')
    assert 'Authorization' in ionq_session.headers
    assert ionq_session.token == 'NotNone'
    assert ionq_session.headers['Authorization'] == 'apiKey NotNone'


def test_authenticate_prompt_requires_token(monkeypatch):
    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return ''

    monkeypatch.setattr('getpass.getpass', user_password_input)
    ionq_session = _ionq_http_client.IonQ()
    with pytest.raises(RuntimeError) as excinfo:
        ionq_session.authenticate()
    assert str(excinfo.value) == 'An authentication token is required!'


def test_is_online():
    ionq_session = _ionq_http_client.IonQ()
    ionq_session.authenticate('not none')
    ionq_session.update_devices_list()
    assert ionq_session.is_online('ionq_simulator')
    assert ionq_session.is_online('ionq_qpu')
    assert not ionq_session.is_online('ionq_unknown')


def test_show_devices():
    device_list = _ionq_http_client.show_devices()
    assert isinstance(device_list, dict)
    for info in device_list.values():
        assert 'nq' in info
        assert 'target' in info


def test_send_too_many_qubits(monkeypatch):
    # Patch the method to give back dummy devices
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 3, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )
    info = {
        'nq': 4,
        'shots': 1,
        'meas_mapped': [2, 3],
        'circuit': [
            {'gate': 'x', 'targets': [0]},
            {'gate': 'x', 'targets': [1]},
            {'controls': [0], 'gate': 'cnot', 'targets': [2]},
            {'controls': [1], 'gate': 'cnot', 'targets': [2]},
            {'controls': [0, 1], 'gate': 'cnot', 'targets': [3]},
        ],
    }
    with pytest.raises(_ionq_http_client.DeviceTooSmall):
        _ionq_http_client.send(
            info,
            device='dummy',
            token='NotNone',
            verbose=True,
        )


def test_send_real_device_online_verbose(monkeypatch):
    # Patch the method to give back dummy devices
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )
    # What the IonQ JSON API request should look like.
    expected_request = {
        'target': 'dummy',
        'metadata': {'sdk': 'ProjectQ', 'meas_qubit_ids': '[2, 3]'},
        'shots': 1,
        'registers': {'meas_mapped': [2, 3]},
        'lang': 'json',
        'body': {
            'qubits': 4,
            'circuit': [
                {'gate': 'x', 'targets': [0]},
                {'gate': 'x', 'targets': [1]},
                {'controls': [0], 'gate': 'cnot', 'targets': [2]},
                {'controls': [1], 'gate': 'cnot', 'targets': [2]},
                {'controls': [0, 1], 'gate': 'cnot', 'targets': [3]},
            ],
        },
    }

    def mock_post(_self, path, *args, **kwargs):
        assert path == _api_url[:-1]
        assert 'json' in kwargs
        assert expected_request == kwargs['json']
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json = mock.MagicMock(
            return_value={
                'id': 'new-job-id',
                'status': 'ready',
            }
        )
        return mock_response

    def mock_get(_self, path, *args, **kwargs):
        assert urljoin(_api_url, 'new-job-id') == path
        mock_response = mock.MagicMock()
        mock_response.json = mock.MagicMock(
            return_value={
                'id': 'new-job-id',
                'status': 'completed',
                'qubits': 4,
                'metadata': {'meas_qubit_ids': '[2, 3]'},
                'registers': {'meas_mapped': [2, 3]},
                'data': {
                    'registers': {'meas_mapped': {'2': 1}},
                },
            }
        )
        return mock_response

    monkeypatch.setattr('requests.sessions.Session.post', mock_post)
    monkeypatch.setattr('requests.sessions.Session.get', mock_get)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return 'NotNone'

    monkeypatch.setattr('getpass.getpass', user_password_input)

    # Code to test:
    info = {
        'nq': 4,
        'shots': 1,
        'meas_mapped': [2, 3],
        'meas_qubit_ids': [2, 3],
        'circuit': [
            {'gate': 'x', 'targets': [0]},
            {'gate': 'x', 'targets': [1]},
            {'controls': [0], 'gate': 'cnot', 'targets': [2]},
            {'controls': [1], 'gate': 'cnot', 'targets': [2]},
            {'controls': [0, 1], 'gate': 'cnot', 'targets': [3]},
        ],
    }
    expected = {
        'nq': 4,
        'output_probs': {'2': 1},
        'meas_mapped': [2, 3],
        'meas_qubit_ids': [2, 3],
    }
    actual = _ionq_http_client.send(info, device='dummy')
    assert expected == actual


@pytest.mark.parametrize(
    'error_type',
    [
        requests.exceptions.HTTPError,
        requests.exceptions.RequestException,
    ],
)
def test_send_requests_errors_are_caught(monkeypatch, error_type):
    # Patch the method to give back dummy devices
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )
    mock_post = mock.MagicMock(side_effect=error_type())
    monkeypatch.setattr('requests.sessions.Session.post', mock_post)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return 'NotNone'

    monkeypatch.setattr('getpass.getpass', user_password_input)

    # Code to test:
    info = {
        'nq': 1,
        'shots': 1,
        'meas_mapped': [],
        'meas_qubit_ids': [],
        'circuit': [],
    }
    _ionq_http_client.send(info, device='dummy')
    mock_post.assert_called_once()


def test_send_auth_errors_reraise(monkeypatch):
    # Patch the method to give back dummy devices
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )

    mock_response = mock.MagicMock()
    mock_response.status_code = 401
    auth_error = requests.exceptions.HTTPError(response=mock_response)
    mock_post = mock.MagicMock(side_effect=auth_error)
    monkeypatch.setattr('requests.sessions.Session.post', mock_post)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return 'NotNone'

    monkeypatch.setattr('getpass.getpass', user_password_input)

    # Code to test:
    info = {
        'nq': 1,
        'shots': 1,
        'meas_mapped': [],
        'meas_qubit_ids': [],
        'circuit': [],
    }
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        _ionq_http_client.send(info, device='dummy')
    mock_post.assert_called_once()
    assert auth_error is excinfo.value


def test_send_bad_requests_reraise(monkeypatch):
    # Patch the method to give back dummy devices
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )

    mock_response = mock.MagicMock()
    mock_response.status_code = 400
    mock_response.json = mock.MagicMock(
        return_value={
            'error': 'Bad Request',
            'message': 'Invalid request body',
        }
    )
    auth_error = requests.exceptions.HTTPError(response=mock_response)
    mock_post = mock.MagicMock(side_effect=auth_error)
    monkeypatch.setattr('requests.sessions.Session.post', mock_post)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return 'NotNone'

    monkeypatch.setattr('getpass.getpass', user_password_input)

    # Code to test:
    info = {
        'nq': 1,
        'shots': 1,
        'meas_mapped': [],
        'meas_qubit_ids': [],
        'circuit': [],
    }
    with pytest.raises(JobSubmissionError) as excinfo:
        _ionq_http_client.send(info, device='dummy')
    mock_post.assert_called_once()
    assert str(excinfo.value) == "Bad Request: Invalid request body"


def test_send_auth_token_required(monkeypatch):
    # Patch the method to give back dummy devices
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )

    mock_post = mock.MagicMock(side_effect=Exception())
    monkeypatch.setattr('requests.sessions.Session.post', mock_post)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return None

    monkeypatch.setattr('getpass.getpass', user_password_input)

    # Code to test:
    info = {
        'nq': 1,
        'shots': 1,
        'meas_mapped': [],
        'meas_qubit_ids': [],
        'circuit': [],
    }
    with pytest.raises(RuntimeError) as excinfo:
        _ionq_http_client.send(info, device='dummy')
    mock_post.assert_not_called()
    assert 'An authentication token is required!' == str(excinfo.value)


@pytest.mark.parametrize(
    "expected_err, err_data",
    [
        (
            "UnknownError: An unknown error occurred! (status=unknown)",
            {'status': 'unknown'},
        ),
        (
            'APIError: Something failed! (status=failed)',
            {
                'status': 'failed',
                'failure': {
                    'error': 'Something failed!',
                    'code': 'APIError',
                },
            },
        ),
    ],
)
def test_send_api_errors_are_raised(monkeypatch, expected_err, err_data):
    # Patch the method to give back dummy devices
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )

    def mock_post(_self, path, **kwargs):
        assert _api_url[:-1] == path
        mock_response = mock.MagicMock()
        mock_response.json = mock.MagicMock(return_value=err_data)
        return mock_response

    monkeypatch.setattr('requests.sessions.Session.post', mock_post)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return 'NotNone'

    monkeypatch.setattr('getpass.getpass', user_password_input)

    # Code to test:
    info = {
        'nq': 1,
        'shots': 1,
        'meas_mapped': [],
        'meas_qubit_ids': [],
        'circuit': [],
    }
    with pytest.raises(JobSubmissionError) as excinfo:
        _ionq_http_client.send(info, device='dummy')

    assert expected_err == str(excinfo.value)


def test_timeout_exception(monkeypatch):
    # Patch the method to give back dummy devices
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )

    def mock_post(_self, path, *args, **kwargs):
        assert path == _api_url[:-1]
        mock_response = mock.MagicMock()
        mock_response.json = mock.MagicMock(
            return_value={
                'id': 'new-job-id',
                'status': 'ready',
            }
        )
        return mock_response

    def mock_get(_self, path, *args, **kwargs):
        assert urljoin(_api_url, 'new-job-id') == path
        mock_response = mock.MagicMock()
        mock_response.json = mock.MagicMock(
            return_value={
                'id': 'new-job-id',
                'status': 'running',
            }
        )
        return mock_response

    monkeypatch.setattr('requests.sessions.Session.post', mock_post)
    monkeypatch.setattr('requests.sessions.Session.get', mock_get)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return 'NotNone'

    monkeypatch.setattr('getpass.getpass', user_password_input)

    # Called once per loop in _get_result while the job is not ready.
    mock_sleep = mock.MagicMock()
    monkeypatch.setattr(_ionq_http_client.time, 'sleep', mock_sleep)

    # RequestTimeoutErrors are not caught, and so will raise out.
    with pytest.raises(RequestTimeoutError) as excinfo:
        info = {
            'nq': 1,
            'shots': 1,
            'meas_mapped': [],
            'meas_qubit_ids': [],
            'circuit': [],
        }
        _ionq_http_client.send(info, device='dummy', num_retries=1)
    mock_sleep.assert_called_once()
    assert 'Timeout. The ID of your submitted job is new-job-id.' == str(excinfo.value)


@pytest.mark.parametrize('token', [None, 'NotNone'])
def test_retrieve(monkeypatch, token):
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )
    request_num = [0]

    def mock_get(_self, path, *args, **kwargs):
        assert urljoin(_api_url, 'old-job-id') == path
        json_response = {
            'id': 'old-job-id',
            'status': 'running',
        }
        if request_num[0] > 1:
            json_response = {
                'id': 'old-job-id',
                'status': 'completed',
                'qubits': 4,
                'registers': {'meas_mapped': [2, 3]},
                'metadata': {'meas_qubit_ids': '[2, 3]'},
                'data': {
                    'registers': {'meas_mapped': {'2': 1}},
                },
            }
        mock_response = mock.MagicMock()
        mock_response.json = mock.MagicMock(return_value=json_response)
        request_num[0] += 1
        return mock_response

    monkeypatch.setattr('requests.sessions.Session.get', mock_get)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return 'NotNone'

    monkeypatch.setattr('getpass.getpass', user_password_input)

    expected = {
        'nq': 4,
        'output_probs': {'2': 1},
        'meas_qubit_ids': [2, 3],
        'meas_mapped': [2, 3],
    }

    # Code to test:
    # Called once per loop in _get_result while the job is not ready.
    mock_sleep = mock.MagicMock()
    monkeypatch.setattr(_ionq_http_client.time, 'sleep', mock_sleep)
    result = _ionq_http_client.retrieve('dummy', token, 'old-job-id')
    assert expected == result
    # We only sleep twice.
    assert 2 == mock_sleep.call_count


def test_retrieve_that_errors_are_caught(monkeypatch):
    def _dummy_update(_self):
        _self.backends = {'dummy': {'nq': 4, 'target': 'dummy'}}

    monkeypatch.setattr(
        _ionq_http_client.IonQ,
        'update_devices_list',
        _dummy_update.__get__(None, _ionq_http_client.IonQ),
    )
    request_num = [0]

    def mock_get(_self, path, *args, **kwargs):
        assert urljoin(_api_url, 'old-job-id') == path
        json_response = {
            'id': 'old-job-id',
            'status': 'running',
        }
        if request_num[0] > 0:
            json_response = {
                'id': 'old-job-id',
                'status': 'failed',
                'failure': {
                    'code': 'ErrorCode',
                    'error': 'A descriptive error message.',
                },
            }
        mock_response = mock.MagicMock()
        mock_response.json = mock.MagicMock(return_value=json_response)
        request_num[0] += 1
        return mock_response

    monkeypatch.setattr('requests.sessions.Session.get', mock_get)

    def user_password_input(prompt):
        if prompt == 'IonQ apiKey > ':
            return 'NotNone'

    monkeypatch.setattr('getpass.getpass', user_password_input)

    # Code to test:
    mock_sleep = mock.MagicMock()
    monkeypatch.setattr(_ionq_http_client.time, 'sleep', mock_sleep)
    with pytest.raises(Exception):
        _ionq_http_client.retrieve('dummy', 'NotNone', 'old-job-id')
    mock_sleep.assert_called_once()
