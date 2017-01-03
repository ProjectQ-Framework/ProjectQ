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

# helpers to run the jsonified gate sequence on ibm quantum experience server
# api documentation is at https://qcwi-staging.mybluemix.net/explorer/
import requests
import getpass
import logging
import sys
import time
from requests.compat import urljoin


_api_url = 'https://quantumexperience.ng.bluemix.net/api/'
_api_url_status = 'https://quantumexperience.ng.bluemix.net/api/'

class DeviceOfflineError(Exception):
	pass


def send(json_qasm, name, device='sim_trivial', user=None, password=None,
         shots=1, verbose=False):
	"""
	Sends json QASM through the IBM API and runs the quantum circuit represented
	by the json data.
	
	Args:
		json_qasm: JSON QASM representation of the circuit to run.
		name (str): Name of the experiment.
		device (str): 'sim_trivial' or 'real' to run on simulator or on the real
			chip, respectively.
		user (str): IBM quantum experience user.
		password (str): IBM quantum experience user password.
		shots (int): Number of runs of the same circuit to collect statistics.
		verbose (bool): If True, additional information is printed, such as
			measurement statistics. Otherwise, the backend simply registers one
			measurement result (same behavior as the projectq Simulator).
	"""
	# check if the device is online
	if device == 'real':
		r = requests.get(urljoin(_api_url_status, 'Status/queue'),
		                 params={"device": "chip_real"})
		online = r.json()['state']
		
		if not online:
			print("The device is offline (for maintenance?). Use the simulator "
			      "instead or try again later.")
			raise DeviceOfflineError("Device is offline.")
	
	try:
		if verbose:
			print("Authenticating...")
		user_id, access_token = _authenticate(user, password)
		if verbose:
			print("Saving code...")
		code_id = _save_code(json_qasm, name, user_id, access_token)
		if verbose:
			print("Running code...")
		execution_id = _run(json_qasm, device, user_id, code_id, access_token,
		                    shots)
		if verbose:
			print("Waiting for results...")
		res = _get_result(execution_id, access_token)
		logging.info(res)
		if verbose:
			print("Done.")
		return res
	except requests.exceptions.HTTPError as err:
		print("There was an error running your code:")
		print(err)
	except requests.exceptions.RequestException as err:
		print("Looks like something is wrong with server:")
		print(err)
	except KeyError as err:
		print("Failed to parse response:")
		print(err)


def _authenticate(email=None, password=None):
	"""
	:param email:
	:param password:
	:return:
	"""
	if email is None:
		try:
			input_fun = raw_input
		except NameError:
			input_fun = input
		email = input_fun('IBM QE user (e-mail) > ')
	if password is None:
		password = getpass.getpass(prompt='IBM QE password > ')

	r = requests.post(urljoin(_api_url, 'users/login'),
	                  data={"email": email, "password": password})
	logging.info(r.text)
	r.raise_for_status()

	json_data = r.json()
	user_id = json_data['userId']
	access_token = json_data['id']

	return user_id, access_token


def _save_code(json_qasm, name, user_id, access_token):
	suffix = 'users/{user_id}/codes'.format(user_id=user_id)

	name_item = '"name":"{name}", "jsonQASM":'.format(name=name)
	json_body = ''.join([name_item, json_qasm])
	json_data = ''.join(['{', json_body, '}'])

	r = requests.post(urljoin(_api_url, suffix),
	                  data=json_data,
	                  params={"access_token": access_token},
	                  headers={"Content-Type": "application/json"})
	logging.info(r.request.body)
	logging.info(r.request.url)
	logging.info(r.text)
	r.raise_for_status()

	return r.json()['idCode']


def _run(json_qasm, device, user_id, code_id, access_token, shots):
	suffix_tmpl = 'users/{user_id}/codes/{code_id}/executions'
	suffix = suffix_tmpl.format(user_id=user_id, code_id=code_id)

	json_data = ''.join(['{"jsonQasm":', json_qasm, '}'])
	
	r = requests.post(urljoin(_api_url, suffix),
	                  data=json_data,
	                  params={"access_token": access_token,
	                          "deviceRunType": device,
	                          "fromCache": "false",
	                          "shots": shots},
	                  headers={"Content-Type": "application/json"})
	logging.info(r.request.body)
	logging.info(r.request.url)
	logging.info(r.text)
	r.raise_for_status()

	r_json = r.json()
	execution_id = r_json["execution"]["id"]
	return execution_id


def _get_result(execution_id, access_token, num_retries=100, interval=1):
	suffix = 'Executions/{execution_id}'.format(execution_id=execution_id)

	for _ in range(num_retries):
		r = requests.get(urljoin(_api_url, suffix),
		                 params={"access_token": access_token})
		logging.info(r.request.url)
		logging.info(r.text)
		r.raise_for_status()

		r_json = r.json()
		status = r_json["status"]["id"]
		if status == "DONE":
			return r_json["result"]
		time.sleep(interval)
