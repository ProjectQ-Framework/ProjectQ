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

# helpers to run the jsonified gate sequence on ibm quantum experience server
# api documentation is at https://qcwi-staging.mybluemix.net/explorer/
import requests
import getpass
import json
import signal
import sys
import time
from requests.compat import urljoin


_api_url = 'https://quantumexperience.ng.bluemix.net/api/'


class DeviceOfflineError(Exception):
    pass


def is_online(device):
    url = 'Backends/{}/queue/status'.format(device)
    r = requests.get(urljoin(_api_url, url))
    return r.json()['state']


def retrieve(device, user, password, jobid, num_retries=3000,
             interval=1, verbose=False):
    """
    Retrieves a previously run job by its ID.

    Args:
        device (str): Device on which the code was run / is running.
        user (str): IBM quantum experience user (e-mail)
        password (str): IBM quantum experience password
        jobid (str): Id of the job to retrieve
    """
    user_id, access_token = _authenticate(user, password)
    res = _get_result(device, jobid, access_token, num_retries=num_retries,
                      interval=interval, verbose=verbose)
    return res


def send(info, device='sim_trivial_2', user=None, password=None,
         shots=1, num_retries=3000, interval=1, verbose=False):
    """
    Sends QASM through the IBM API and runs the quantum circuit.

    Args:
        info: Contains QASM representation of the circuit to run.
        device (str): Either 'simulator', 'ibmqx4', or 'ibmqx5'.
        user (str): IBM quantum experience user.
        password (str): IBM quantum experience user password.
        shots (int): Number of runs of the same circuit to collect statistics.
        verbose (bool): If True, additional information is printed, such as
            measurement statistics. Otherwise, the backend simply registers
            one measurement result (same behavior as the projectq Simulator).
    """
    try:
        # check if the device is online
        if device in ['ibmqx4', 'ibmqx5']:
            online = is_online(device)

            if not online:
                print("The device is offline (for maintenance?). Use the "
                      "simulator instead or try again later.")
                raise DeviceOfflineError("Device is offline.")

        if verbose:
            print("- Authenticating...")
        user_id, access_token = _authenticate(user, password)
        if verbose:
            print("- Running code: {}".format(
                json.loads(info)['qasms'][0]['qasm']))
        execution_id = _run(info, device, user_id, access_token, shots)
        if verbose:
            print("- Waiting for results...")
        res = _get_result(device, execution_id, access_token,
                          num_retries=num_retries,
                          interval=interval, verbose=verbose)
        if verbose:
            print("- Done.")
        return res
    except requests.exceptions.HTTPError as err:
        print("- There was an error running your code:")
        print(err)
    except requests.exceptions.RequestException as err:
        print("- Looks like something is wrong with server:")
        print(err)
    except KeyError as err:
        print("- Failed to parse response:")
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
    r.raise_for_status()

    json_data = r.json()
    user_id = json_data['userId']
    access_token = json_data['id']

    return user_id, access_token


def _run(qasm, device, user_id, access_token, shots):
    suffix = 'Jobs'

    r = requests.post(urljoin(_api_url, suffix),
                      data=qasm,
                      params={"access_token": access_token,
                              "deviceRunType": device,
                              "fromCache": "false",
                              "shots": shots},
                      headers={"Content-Type": "application/json"})
    r.raise_for_status()

    r_json = r.json()
    execution_id = r_json["id"]
    return execution_id


def _get_result(device, execution_id, access_token, num_retries=3000,
                interval=1, verbose=False):
    suffix = 'Jobs/{execution_id}'.format(execution_id=execution_id)
    status_url = urljoin(_api_url, 'Backends/{}/queue/status'.format(device))

    if verbose:
        print("Waiting for results. [Job ID: {}]".format(execution_id))

    original_sigint_handler = signal.getsignal(signal.SIGINT)

    def _handle_sigint_during_get_result(*_):
        raise Exception("Interrupted. The ID of your submitted job is {}."
                        .format(execution_id))

    try:
        signal.signal(signal.SIGINT, _handle_sigint_during_get_result)

        for retries in range(num_retries):
            r = requests.get(urljoin(_api_url, suffix),
                             params={"access_token": access_token})
            r.raise_for_status()
            r_json = r.json()
            if 'qasms' in r_json:
                qasm = r_json['qasms'][0]
                if 'result' in qasm and qasm['result'] is not None:
                    return qasm['result']
            time.sleep(interval)
            if device in ['ibmqx4', 'ibmqx5'] and retries % 60 == 0:
                r = requests.get(status_url)
                r_json = r.json()
                if 'state' in r_json and not r_json['state']:
                    raise DeviceOfflineError("Device went offline. The ID of "
                                             "your submitted job is {}."
                                             .format(execution_id))
                if verbose and 'lengthQueue' in r_json:
                    print("Currently there are {} jobs queued for execution "
                          "on {}."
                          .format(r_json['lengthQueue'], device))

    finally:
        if original_sigint_handler is not None:
            signal.signal(signal.SIGINT, original_sigint_handler)

    raise Exception("Timeout. The ID of your submitted job is {}."
                    .format(execution_id))
