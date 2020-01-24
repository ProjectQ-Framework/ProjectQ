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

"""Tests for projectq.backends._ibm_http_client._ibm.py."""

import json
import pytest
import requests
from requests.compat import urljoin

from projectq.backends._ibm import _ibm_http_client


# Insure that no HTTP request can be made in all tests in this module
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


_api_url = 'https://api.quantum-computing.ibm.com/api/'
_auth_api_url = 'https://auth.quantum-computing.ibm.com/api/users/loginWithToken'

def test_send_real_device_online_verbose(monkeypatch):
    json_qasm = {'qasms': [{'qasm': 'my qasm'}],'shots': 1, 
            'json': 'instructions','maxCredits': 10,'nq': 1}
    name = 'projectq_test'
    token = '12345'
    access_token = "access"
    user_id = 2016
    code_id = 11
    name_item = '"name":"{name}", "jsonQASM":'.format(name=name)
    json_body = ''.join([name_item, json.dumps(json_qasm)])
    json_data = ''.join(['{', json_body, '}'])
    shots = 1
    device = "ibmqx4"
    execution_id = '3'
    result_ready = [False]
    result = "my_result"
    request_num = [0]  # To assert correct order of calls

    # Mock of IBM server:
    def mocked_requests_get(*args, **kwargs):
        class MockRequest:
            def __init__(self, url=""):
                self.url = url

        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.request = MockRequest()
                self.text = ""

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Accessing status of device. Return online.
        status_url = 'Network/ibm-q/Groups/open/Projects/main/devices/v/1'
        if (args[1] == urljoin(_api_url, status_url) and
                (request_num[0] == 1 or request_num[0] == 4)):
            request_num[0] += 1
            connections=set([(0, 1), (1, 0), (1, 2), (1, 3), (1, 4),
                                 (2, 1), (2, 3), (2, 4), (3, 1), (3, 4), (4, 3)])
            return MockResponse([{'backend_name': 'ibmqx4', 'coupling_map': connections, 'backend_version': '0.1.547', 'n_qubits': 32}], 200)
        # Getting result
        elif (args[1] == urljoin(_api_url,
              "Network/ibm-q/Groups/open/Projects/main/Jobs/{execution_id}".format(execution_id=execution_id)) and not
              result_ready[0] and request_num[0] == 3):
            result_ready[0] = True
            request_num[0] += 1
            return MockResponse({"status": "RUNNING"}, 200)
        elif (args[1] == urljoin(_api_url,
              "Network/ibm-q/Groups/open/Projects/main/Jobs/{execution_id}".format(execution_id=execution_id)) and
              result_ready[0] and request_num[0] == 5):
            return MockResponse({'qObjectResult':{"results": [result]},"status": "COMPLETED"}, 200)

    def mocked_requests_post(*args, **kwargs):
        class MockRequest:
            def __init__(self, body="", url=""):
                self.body = body
                self.url = url

        class MockPostResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass
        jobs_url='Network/ibm-q/Groups/open/Projects/main/Jobs'
        # Authentication
        if (args[1] == _auth_api_url and
                kwargs["json"]["apiToken"] == token and
                request_num[0] == 0):
            request_num[0] += 1
            return MockPostResponse({"userId": user_id, "id": access_token})
        # Run code
        elif (args[1] == urljoin(_api_url, jobs_url) and
                kwargs["data"] == None and
                kwargs["json"]["backend"]["name"] == device and
                kwargs["json"]["qObject"]['config']['shots'] == shots and
                request_num[0] == 2):
            request_num[0] += 1
            return MockPostResponse({"id": execution_id})
    
    monkeypatch.setattr("requests.sessions.Session.get", mocked_requests_get)
    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)

    def user_password_input(prompt):
        if prompt == "IBM QE token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)

    # Code to test:
    res = _ibm_http_client.send(json_qasm,
                                device="ibmqx4",
                                token=None,
                                shots=shots, verbose=True)
    assert res == result
    json_qasm['nq']=40
    request_num[0]=0
    with pytest.raises(_ibm_http_client.DeviceTooSmall):
        res = _ibm_http_client.send(json_qasm,
                                device="ibmqx4",
                                token=None,
                                shots=shots, verbose=True)


def test_no_password_given(monkeypatch):
    token = ''  
    json_qasm  = ''
    def user_password_input(prompt):
        if prompt == "IBM QE token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)

    with pytest.raises(Exception):
        res = _ibm_http_client.send(json_qasm,
                                device="ibmqx4",
                                token=None,
                                shots=1, verbose=True)

def test_send_real_device_offline(monkeypatch):
    token = '12345'
    access_token = "access"
    user_id = 2016
    def mocked_requests_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Accessing status of device. Return offline.
        status_url = 'Network/ibm-q/Groups/open/Projects/main/devices/v/1'
        if args[1] == urljoin(_api_url, status_url):
            return MockResponse({}, 200)
    
    def mocked_requests_post(*args, **kwargs):
        class MockRequest:
            def __init__(self, body="", url=""):
                self.body = body
                self.url = url

        class MockPostResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass
        # Authentication
        if (args[1] == _auth_api_url and kwargs["json"]["apiToken"] == token):
            return MockPostResponse({"userId": user_id, "id": access_token})

    monkeypatch.setattr("requests.sessions.Session.get", mocked_requests_get)
    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)

    shots = 1
    token='12345'
    json_qasm = {'qasms': [{'qasm': 'my qasm'}],'shots': 1, 
            'json': 'instructions','maxCredits': 10,'nq': 1}
    name = 'projectq_test'
    with pytest.raises(_ibm_http_client.DeviceOfflineError):
        _ibm_http_client.send(json_qasm,
                              device="ibmqx4",
                              token=token,
                              shots=shots, verbose=True)


def test_show_device(monkeypatch):
    access_token = "access"
    user_id = 2016
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            pass

    def mocked_requests_get(*args, **kwargs):
        # Accessing status of device. Return online.
        status_url = 'Network/ibm-q/Groups/open/Projects/main/devices/v/1'
        if args[1] == urljoin(_api_url, status_url):
            connections=set([(0, 1), (1, 0), (1, 2), (1, 3), (1, 4),
                                 (2, 1), (2, 3), (2, 4), (3, 1), (3, 4), (4, 3)])
            return MockResponse([{'backend_name': 'ibmqx4', 'coupling_map': connections, 'backend_version': '0.1.547', 'n_qubits': 32}], 200)

    def mocked_requests_post(*args, **kwargs):
        class MockRequest:
            def __init__(self, body="", url=""):
                self.body = body
                self.url = url

        class MockPostResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Authentication
        if (args[1] == _auth_api_url and
                kwargs["json"]["apiToken"] == token):
            return MockPostResponse({"userId": user_id, "id": access_token})

    monkeypatch.setattr("requests.sessions.Session.get", mocked_requests_get)
    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)
    # Patch login data
    token = '12345'

    def user_password_input(prompt):
        if prompt == "IBM QE token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)
    assert _ibm_http_client.show_devices() == {'ibmqx4':{'coupling_map': {(0, 1), (1, 0), (1, 2), (1, 3), (1, 4),
                                 (2, 1), (2, 3), (2, 4), (3, 1), (3, 4), (4, 3)}, 'version': '0.1.547', 'nq': 32}}

def test_send_that_errors_are_caught(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code):
            pass
 
    def mocked_requests_post(*args, **kwargs):
        # Test that this error gets caught
        raise requests.exceptions.HTTPError

    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)
    # Patch login data
    token = '12345'

    def user_password_input(prompt):
        if prompt == "IBM QE token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)
    shots = 1
    json_qasm = {'qasms': [{'qasm': 'my qasm'}],'shots': 1, 
            'json': 'instructions','maxCredits': 10,'nq': 1}
    name = 'projectq_test'
    _ibm_http_client.send(json_qasm,
                          device="ibmqx4",
                          token=None,
                          shots=shots, verbose=True)




def test_send_that_errors_are_caught2(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code):
            pass
  
    def mocked_requests_post(*args, **kwargs):
        # Test that this error gets caught
        raise requests.exceptions.RequestException

    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)
    # Patch login data
    token = '12345'

    def user_password_input(prompt):
        if prompt == "IBM QE token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)
    shots = 1
    json_qasm = {'qasms': [{'qasm': 'my qasm'}],'shots': 1, 
            'json': 'instructions','maxCredits': 10,'nq': 1}
    name = 'projectq_test'
    _ibm_http_client.send(json_qasm,
                          device="ibmqx4",
                          token=None,
                          shots=shots, verbose=True)



def test_send_that_errors_are_caught3(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code):
            pass

    def mocked_requests_post(*args, **kwargs):
        # Test that this error gets caught
        raise KeyError

    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)
    # Patch login data
    token = '12345'

    def user_password_input(prompt):
        if prompt == "IBM QE token > ":
            return token

    monkeypatch.setattr("getpass.getpass", user_password_input)
    shots = 1
    json_qasm = {'qasms': [{'qasm': 'my qasm'}],'shots': 1, 
            'json': 'instructions','maxCredits': 10,'nq': 1}
    name = 'projectq_test'
    _ibm_http_client.send(json_qasm,
                          device="ibmqx4",
                          token=None,
                          shots=shots, verbose=True)




def test_timeout_exception(monkeypatch):
    qasms = {'qasms': [{'qasm': 'my qasm'}],'shots': 1, 
            'json': 'instructions','maxCredits': 10,'nq': 1}
    json_qasm = qasms
    tries = [0]

    def mocked_requests_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Accessing status of device. Return device info.
        status_url = 'Network/ibm-q/Groups/open/Projects/main/devices/v/1'
        if args[1] == urljoin(_api_url, status_url):
            connections=set([(0, 1), (1, 0), (1, 2), (1, 3), (1, 4),
                                 (2, 1), (2, 3), (2, 4), (3, 1), (3, 4), (4, 3)])
            return MockResponse([{'backend_name': 'ibmqx4', 'coupling_map': connections, 'backend_version': '0.1.547', 'n_qubits': 32}], 200)
        job_url = "Network/ibm-q/Groups/open/Projects/main/Jobs/{}".format("123e")
        if args[1] == urljoin(_api_url, job_url):
            tries[0] += 1
            return MockResponse({"status": "RUNNING"}, 200)

    def mocked_requests_post(*args, **kwargs):
        class MockRequest:
            def __init__(self, url=""):
                self.url = url

        class MockPostResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        jobs_url='Network/ibm-q/Groups/open/Projects/main/Jobs'
        if args[1] == _auth_api_url:
            return MockPostResponse({"userId": "1", "id": "12"})
        if args[1] == urljoin(_api_url, jobs_url):
            return MockPostResponse({"id": "123e"})

    monkeypatch.setattr("requests.sessions.Session.get", mocked_requests_get)
    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)

    _ibm_http_client.time.sleep = lambda x: x
    with pytest.raises(Exception) as excinfo:
        _ibm_http_client.send(json_qasm,
                              device="ibmqx4",
                              token="test",
                              shots=1,num_retries=10, verbose=False)
    assert "123e" in str(excinfo.value)  # check that job id is in exception
    assert tries[0] > 0


def test_retrieve_and_device_offline_exception(monkeypatch):
    request_num = [0]

    def mocked_requests_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Accessing status of device. Return online.
        status_url = 'Network/ibm-q/Groups/open/Projects/main/devices/v/1'
        if args[1] == urljoin(_api_url, status_url) and request_num[0] < 2:
            return MockResponse([{'backend_name': 'ibmqx4', 'coupling_map': None, 'backend_version': '0.1.547', 'n_qubits': 32}], 200)
        elif args[1] == urljoin(_api_url, status_url):#ibmqx4 gets disconnected, replaced by ibmqx5
            return MockResponse([{'backend_name': 'ibmqx5', 'coupling_map': None, 'backend_version': '0.1.547', 'n_qubits': 32}], 200)
        job_url = job_url = "Network/ibm-q/Groups/open/Projects/main/Jobs/{}".format("123e")
        if args[1] == urljoin(_api_url, job_url):
            request_num[0] += 1
            return MockResponse({"status": "RUNNING",'iteration':request_num[0]}, 200)

    def mocked_requests_post(*args, **kwargs):
        class MockRequest:
            def __init__(self, url=""):
                self.url = url

        class MockPostResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        if args[1] == _auth_api_url:
            return MockPostResponse({"userId": "1", "id": "12"})

    monkeypatch.setattr("requests.sessions.Session.get", mocked_requests_get)
    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)

    _ibm_http_client.time.sleep = lambda x: x
    with pytest.raises(_ibm_http_client.DeviceOfflineError):
        _ibm_http_client.retrieve(device="ibmqx4",
                                  token="test",
                                  jobid="123e",
                                  num_retries=200)


def test_retrieve(monkeypatch):
    request_num = [0]

    def mocked_requests_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        # Accessing status of device. Return online.
        status_url = 'Network/ibm-q/Groups/open/Projects/main/devices/v/1'
        if args[1] == urljoin(_api_url, status_url):
            return MockResponse([{'backend_name': 'ibmqx4', 'coupling_map': None, 'backend_version': '0.1.547', 'n_qubits': 32}], 200)
        job_url = 'Network/ibm-q/Groups/open/Projects/main/Jobs/{}'.format("123e")
        if args[1] == urljoin(_api_url, job_url) and request_num[0] < 1:
            request_num[0] += 1
            return MockResponse({"status": "RUNNING"}, 200)
        elif args[1] == urljoin(_api_url, job_url):
            return MockResponse({"qObjectResult": {'qasm': 'qasm',
                                            'results': ['correct']},"status": "COMPLETED"}, 200)

    def mocked_requests_post(*args, **kwargs):
        class MockRequest:
            def __init__(self, url=""):
                self.url = url

        class MockPostResponse:
            def __init__(self, json_data, text=" "):
                self.json_data = json_data
                self.text = text
                self.request = MockRequest()

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        if args[1] == _auth_api_url:
            return MockPostResponse({"userId": "1", "id": "12"})

    monkeypatch.setattr("requests.sessions.Session.get", mocked_requests_get)
    monkeypatch.setattr("requests.sessions.Session.post", mocked_requests_post)

    _ibm_http_client.time.sleep = lambda x: x
    res = _ibm_http_client.retrieve(device="ibmqx4",
                                    token="test",
                                    jobid="123e")
    assert res == 'correct'
