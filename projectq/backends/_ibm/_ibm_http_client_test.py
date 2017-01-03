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

import pytest
import requests
from requests.compat import urljoin

from projectq.backends._ibm import _ibm_http_client


# Insure that no HTTP request can be made in all tests in this module
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


_api_url = 'https://quantumexperience.ng.bluemix.net/api/'
_api_url_status = 'https://quantumexperience.ng.bluemix.net/api/'


def test_send_real_device_online_verbose(monkeypatch):
	json_qasm = "my_json_qasm"
	name = 'projectq_test'
	access_token = "access"
	user_id = 2016
	code_id = 11
	name_item = '"name":"{name}", "jsonQASM":'.format(name=name)
	json_body = ''.join([name_item, json_qasm])
	json_data = ''.join(['{', json_body, '}'])
	shots = 1
	device = "real"
	json_data_run = ''.join(['{"jsonQasm":', json_qasm, '}'])
	execution_id = 3
	result_ready = [False]
	result = "my_result"
	request_num = [0] # To assert correct order of calls
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
		if (args[0] == urljoin(_api_url_status, "Status/queue") and
			kwargs["params"]["device"] == "chip_real" and
			request_num[0] == 0):
			request_num[0] += 1
			return MockResponse({"state": True}, 200)
		# Getting result
		elif (args[0] == urljoin(_api_url, 
		  "Executions/{execution_id}".format(execution_id=execution_id)) and
		  kwargs["params"]["access_token"] == access_token and 
		  not result_ready[0] and request_num[0] == 4):
			result_ready[0] = True
			return MockResponse({"status":{"id": "NotDone"}}, 200)
		elif (args[0] == urljoin(_api_url, 
		  "Executions/{execution_id}".format(execution_id=execution_id)) and
		  kwargs["params"]["access_token"] == access_token and 
		  result_ready[0] and request_num[0] == 4):
			return MockResponse({"status":{"id": "DONE"}, 
			                     "result": result}, 200)

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
		if (args[0] == urljoin(_api_url, "users/login") and
			    kwargs["data"]["email"] == email and
			    kwargs["data"]["password"] == password and
			    request_num[0] == 1):
			request_num[0] += 1 
			return MockPostResponse({"userId": user_id, "id": access_token})
		# Save code
		elif (args[0] == urljoin(_api_url, 
		                 "users/{user_id}/codes".format(user_id=user_id)) and
		        kwargs["data"] == json_data and
		        kwargs["params"]["access_token"] == access_token and
		        kwargs["headers"]["Content-Type"] == "application/json" and
		        request_num[0] == 2):
			request_num[0] += 1
			return MockPostResponse({"idCode": code_id})
		# Run code
		elif (args[0] == urljoin(_api_url, 
		  "users/{user_id}/codes/{code_id}/executions".format(user_id=user_id,
		                                                 code_id=code_id)) and
		        kwargs["data"] == json_data_run and
		        kwargs["params"]["access_token"] == access_token and
		        kwargs["params"]["deviceRunType"] == device and
		        kwargs["params"]["fromCache"] == "false" and
		        kwargs["params"]["shots"] == shots and
		        kwargs["headers"]["Content-Type"] == "application/json" and
		        request_num[0] == 3):
			request_num[0] += 1
			return MockPostResponse({"execution": {"id": execution_id}})

	monkeypatch.setattr("requests.get", mocked_requests_get)
	monkeypatch.setattr("requests.post", mocked_requests_post)
	# Patch login data
	password = 12345
	email = "test@projectq.ch"
	monkeypatch.setitem(__builtins__, "input", lambda x: email)
	monkeypatch.setitem(__builtins__, "raw_input", lambda x: email)
	def user_password_input(prompt):
		if prompt == "IBM QE password > ":
			return password
	monkeypatch.setattr("getpass.getpass", user_password_input)

	# Code to test:
	res = _ibm_http_client.send(json_qasm, name=name, 
	                            device="real",
	                            user=None, password=None, 
	                            shots=shots, verbose=True)
	print(res)
	assert res == result


def test_send_real_device_offline(monkeypatch):
	def mocked_requests_get(*args, **kwargs):
		class MockResponse:
			def __init__(self, json_data, status_code):
				self.json_data = json_data
				self.status_code = status_code

			def json(self):
				return self.json_data

		# Accessing status of device. Return online.
		if (args[0] == urljoin(_api_url_status, "Status/queue") and
			kwargs["params"]["device"] == "chip_real"):
			return MockResponse({"state": False}, 200)
	monkeypatch.setattr("requests.get", mocked_requests_get)
	shots = 1
	json_qasm = "my_json_qasm"
	name = 'projectq_test'
	with pytest.raises(_ibm_http_client.DeviceOfflineError):
		_ibm_http_client.send(json_qasm, name=name, 
		                            device="real",
		                            user=None, password=None, 
		                            shots=shots, verbose=True)


def test_send_that_errors_are_caught(monkeypatch):
	def mocked_requests_get(*args, **kwargs):
		class MockResponse:
			def __init__(self, json_data, status_code):
				self.json_data = json_data
				self.status_code = status_code

			def json(self):
				return self.json_data

		# Accessing status of device. Return online.
		if (args[0] == urljoin(_api_url_status, "Status/queue") and
			kwargs["params"]["device"] == "chip_real"):
			return MockResponse({"state": True}, 200)
	def mocked_requests_post(*args, **kwargs):
		# Test that this error gets caught
		raise requests.exceptions.HTTPError
	monkeypatch.setattr("requests.get", mocked_requests_get)
	monkeypatch.setattr("requests.post", mocked_requests_post)
	# Patch login data
	password = 12345
	email = "test@projectq.ch"
	monkeypatch.setitem(__builtins__, "input", lambda x: email)
	monkeypatch.setitem(__builtins__, "raw_input", lambda x: email)
	def user_password_input(prompt):
		if prompt == "IBM QE password > ":
			return password
	monkeypatch.setattr("getpass.getpass", user_password_input)
	shots = 1
	json_qasm = "my_json_qasm"
	name = 'projectq_test'
	_ibm_http_client.send(json_qasm, name=name, 
	                            device="real",
	                            user=None, password=None, 
	                            shots=shots, verbose=True)


def test_send_that_errors_are_caught2(monkeypatch):
	def mocked_requests_get(*args, **kwargs):
		class MockResponse:
			def __init__(self, json_data, status_code):
				self.json_data = json_data
				self.status_code = status_code

			def json(self):
				return self.json_data

		# Accessing status of device. Return online.
		if (args[0] == urljoin(_api_url_status, "Status/queue") and
			kwargs["params"]["device"] == "chip_real"):
			return MockResponse({"state": True}, 200)
	def mocked_requests_post(*args, **kwargs):
		# Test that this error gets caught
		raise requests.exceptions.RequestException 
	monkeypatch.setattr("requests.get", mocked_requests_get)
	monkeypatch.setattr("requests.post", mocked_requests_post)
	# Patch login data
	password = 12345
	email = "test@projectq.ch"
	monkeypatch.setitem(__builtins__, "input", lambda x: email)
	monkeypatch.setitem(__builtins__, "raw_input", lambda x: email)
	def user_password_input(prompt):
		if prompt == "IBM QE password > ":
			return password
	monkeypatch.setattr("getpass.getpass", user_password_input)
	shots = 1
	json_qasm = "my_json_qasm"
	name = 'projectq_test'
	_ibm_http_client.send(json_qasm, name=name, 
	                            device="real",
	                            user=None, password=None, 
	                            shots=shots, verbose=True)


def test_send_that_errors_are_caught3(monkeypatch):
	def mocked_requests_get(*args, **kwargs):
		class MockResponse:
			def __init__(self, json_data, status_code):
				self.json_data = json_data
				self.status_code = status_code

			def json(self):
				return self.json_data

		# Accessing status of device. Return online.
		if (args[0] == urljoin(_api_url_status, "Status/queue") and
			kwargs["params"]["device"] == "chip_real"):
			return MockResponse({"state": True}, 200)
	def mocked_requests_post(*args, **kwargs):
		# Test that this error gets caught
		raise KeyError 
	monkeypatch.setattr("requests.get", mocked_requests_get)
	monkeypatch.setattr("requests.post", mocked_requests_post)
	# Patch login data
	password = 12345
	email = "test@projectq.ch"
	monkeypatch.setitem(__builtins__, "input", lambda x: email)
	monkeypatch.setitem(__builtins__, "raw_input", lambda x: email)
	def user_password_input(prompt):
		if prompt == "IBM QE password > ":
			return password
	monkeypatch.setattr("getpass.getpass", user_password_input)
	shots = 1
	json_qasm = "my_json_qasm"
	name = 'projectq_test'
	_ibm_http_client.send(json_qasm, name=name, 
	                            device="real",
	                            user=None, password=None, 
	                            shots=shots, verbose=True)
