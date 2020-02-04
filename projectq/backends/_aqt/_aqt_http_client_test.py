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

"""Tests for projectq.backends._aqt._aqt_http_client.py."""

import json
import pytest
import requests
from requests.compat import urljoin

from projectq.backends._aqt import _aqt_http_client


# Insure that no HTTP request can be made in all tests in this module
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


_api_url = 'https://gateway.aqt.eu/marmot/'

def test_send_real_device_online_verbose(monkeypatch):
    json_aqt = {'data': '[["Y", 0.5, [1]], ["X", 0.5, [1]], ["X", 0.5, [1]], '
                         '["Y", 0.5, [1]], ["MS", 0.5, [1, 2]], ["X", 3.5, [1]], '
                         '["Y", 3.5, [1]], ["X", 3.5, [2]]]',
                 'access_token': 'access', 'repetitions': 1, 'no_qubits': 3}
    info = {'circuit': '[["Y", 0.5, [1]], ["X", 0.5, [1]], ["X", 0.5, [1]], '
                                '["Y", 0.5, [1]], ["MS", 0.5, [1, 2]], ["X", 3.5, [1]], '
                                '["Y", 3.5, [1]], ["X", 3.5, [2]]]',
                     'nq': 3, 'shots': 1, 'backend': {'name': 'aqt_simulator'}}
    token = "access"
    shots = 1
    device = "aqt_simulator"
    execution_id = '3'
    result_ready = [False]
    result = "my_result"
    request_num = [0]  # To assert correct order of calls

    def mocked_requests_put(*args, **kwargs):
        class MockRequest:
            def __init__(self, body="", url=""):
                self.body = body
                self.url = url

        class MockPutResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Run code
        if (args[1] == urljoin(_api_url, "sim/") and
                kwargs["data"] == json_aqt and
                request_num[0] == 0):
            request_num[0] += 1
            return MockPutResponse({"id": execution_id,"status":"queued"},200)
        elif (args[1] == urljoin(_api_url,"sim/") and
              kwargs["data"]["access_token"] == token and
              kwargs["data"]["id"] == execution_id and not
              result_ready[0] and request_num[0] == 1):
            result_ready[0] = True
            request_num[0] += 1
            return MockPutResponse({"status":'running'}, 200)
        elif (args[1] == urljoin(_api_url,"sim/") and
              kwargs["data"]["access_token"] == token and
              kwargs["data"]["id"] == execution_id and
              result_ready[0] and request_num[0] == 2):
            return MockPutResponse({"samples": result,"status": 'finished'}, 200)

    monkeypatch.setattr("requests.sessions.Session.put", mocked_requests_put)

    def user_password_input(prompt):
        if prompt == "AQT token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)

    # Code to test:
    res = _aqt_http_client.send(info,
                                device="aqt_simulator",
                                token=None,
                                shots=shots, verbose=True)
    assert res == result

def test_send_that_errors_are_caught(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def mocked_requests_put(*args, **kwargs):
        # Test that this error gets caught
        raise requests.exceptions.HTTPError

    monkeypatch.setattr("requests.sessions.Session.put", mocked_requests_put)
    # Patch login data
    token = 12345

    def user_password_input(prompt):
        if prompt == "AQT token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)
    shots = 1
    info = {'circuit': '[["Y", 0.5, [1]], ["X", 0.5, [1]], ["X", 0.5, [1]], '
                                '["Y", 0.5, [1]], ["MS", 0.5, [1, 2]], ["X", 3.5, [1]], '
                                '["Y", 3.5, [1]], ["X", 3.5, [2]]]',
                     'nq': 3, 'shots': 1, 'backend': {'name': 'aqt_simulator'}}
    _aqt_http_client.send(info,
                          device="aqt_simulator",
                          token=None,
                          shots=shots, verbose=True)


def test_send_that_errors_are_caught2(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def mocked_requests_put(*args, **kwargs):
        # Test that this error gets caught
        raise requests.exceptions.RequestException

    monkeypatch.setattr("requests.sessions.Session.put", mocked_requests_put)
    # Patch login data
    token = 12345

    def user_password_input(prompt):
        if prompt == "AQT token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)
    shots = 1
    info = {'circuit': '[["Y", 0.5, [1]], ["X", 0.5, [1]], ["X", 0.5, [1]], '
                                '["Y", 0.5, [1]], ["MS", 0.5, [1, 2]], ["X", 3.5, [1]], '
                                '["Y", 3.5, [1]], ["X", 3.5, [2]]]',
                     'nq': 3, 'shots': 1, 'backend': {'name': 'aqt_simulator'}}
    _aqt_http_client.send(info,
                          device="aqt_simulator",
                          token=None,
                          shots=shots, verbose=True)


def test_send_that_errors_are_caught3(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def mocked_requests_put(*args, **kwargs):
        # Test that this error gets caught
        raise KeyError

    monkeypatch.setattr("requests.sessions.Session.put", mocked_requests_put)
    # Patch login data
    token = 12345

    def user_password_input(prompt):
        if prompt == "AQT token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)
    shots = 1
    info = {'circuit': '[["Y", 0.5, [1]], ["X", 0.5, [1]], ["X", 0.5, [1]], '
                                '["Y", 0.5, [1]], ["MS", 0.5, [1, 2]], ["X", 3.5, [1]], '
                                '["Y", 3.5, [1]], ["X", 3.5, [2]]]',
                     'nq': 3, 'shots': 1, 'backend': {'name': 'aqt_simulator'}}
    _aqt_http_client.send(info,
                          device="aqt_simulator",
                          token=None,
                          shots=shots, verbose=True)







def test_timeout_exception(monkeypatch):
    json_aqt = {'data': '[["Y", 0.5, [1]], ["X", 0.5, [1]], ["X", 0.5, [1]], '
                         '["Y", 0.5, [1]], ["MS", 0.5, [1, 2]], ["X", 3.5, [1]], '
                         '["Y", 3.5, [1]], ["X", 3.5, [2]]]',
                 'access_token': 'access', 'repetitions': 1, 'no_qubits': 3}
    info = {'circuit': '[["Y", 0.5, [1]], ["X", 0.5, [1]], ["X", 0.5, [1]], '
                                '["Y", 0.5, [1]], ["MS", 0.5, [1, 2]], ["X", 3.5, [1]], '
                                '["Y", 3.5, [1]], ["X", 3.5, [2]]]',
                     'nq': 3, 'shots': 1, 'backend': {'name': 'aqt_simulator'}}
    token = "access"
    shots = 1
    device = "aqt_simulator"
    execution_id = '123e'
    result_ready = [False]
    tries = [0]

    def mocked_requests_put(*args, **kwargs):
        class MockRequest:
            def __init__(self, body="", url=""):
                self.body = body
                self.url = url

        class MockPutResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Run code
        if (args[1] == urljoin(_api_url, "sim/") and
                kwargs["data"] == json_aqt):
            return MockPutResponse({"id": execution_id,"status":"queued"},200)
        elif (args[1] == urljoin(_api_url,"sim/") and
              kwargs["data"]["access_token"] == token and
              kwargs["data"]["id"] == execution_id):
            tries[0] += 1
            return MockPutResponse({"status":'running'}, 200)
  
    monkeypatch.setattr("requests.sessions.Session.put", mocked_requests_put)

    def user_password_input(prompt):
        if prompt == "AQT token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)

    # Code to test:
    _aqt_http_client.time.sleep = lambda x: x
    with pytest.raises(Exception) as excinfo:
        _aqt_http_client.send(info,
                                device="aqt_simulator",
                                token=None,
                                num_retries=10,
                                shots=shots, verbose=True)
    assert "123e" in str(excinfo.value)  # check that job id is in exception
    assert tries[0] > 0
                       

def test_retrieve(monkeypatch):
    token = "access"
    device = "aqt_simulator"
    execution_id = '123e'
    result_ready = [False]
    result = "my_result"
    request_num = [0]  # To assert correct order of calls

    def mocked_requests_put(*args, **kwargs):
        class MockRequest:
            def __init__(self, body="", url=""):
                self.body = body
                self.url = url

        class MockPutResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Run code
        if (args[1] == urljoin(_api_url,"sim/") and
              kwargs["data"]["access_token"] == token and
              kwargs["data"]["id"] == execution_id and not
              result_ready[0] and request_num[0] < 1):
            result_ready[0] = True
            request_num[0] += 1
            return MockPutResponse({"status":'running'}, 200)
        elif (args[1] == urljoin(_api_url,"sim/") and
              kwargs["data"]["access_token"] == token and
              kwargs["data"]["id"] == execution_id and
              result_ready[0] and request_num[0] == 1):
            return MockPutResponse({"samples": result,"status": 'finished'}, 200)

    monkeypatch.setattr("requests.sessions.Session.put", mocked_requests_put)

    def user_password_input(prompt):
        if prompt == "AQT token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)

    # Code to test:
    _aqt_http_client.time.sleep = lambda x: x
    res = _aqt_http_client.retrieve(device="aqt_simulator",
                                    token=None, verbose=True,
                                    jobid="123e")
    assert res == result
