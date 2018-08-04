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

# helpers to run the jsonified gate sequence on Rigetti's Forest API
# official SDK is at https://github.com/rigetticomputing/pyquil
import requests
import getpass
import sys
import time
import re
from requests.compat import urljoin


_api_url = 'https://job.rigetti.com/beta/'
_old_api_url = 'https://api.rigetti.com/qvm'
RIGETTI_DEVICES = ["8Q-Agave", "19Q-Acorn"]

class DeviceOfflineError(Exception):
    pass

def is_online(device, user_id, api_key):
    r = requests.get(urljoin(_api_url, "devices"), headers={
        "X-Api-Key": api_key,
        "X-User-Id": user_id,
        "Accept": "application/octet-stream"
    })
    device_list = r.json()["devices"]
    if device in device_list:
        return device_list[device]["is_online"]
    else:
        raise Exception("Did not find record of device")

def retrieve(device, user_id, api_key, jobid):
    """
    Retrieves a previously run job by its ID.

    Args:
        device (str): Device on which the code was run / is running.
        user_id (str): Rigetti User ID
        api_key (str): Rigetti API Key
        jobid (str): Id of the job to retrieve
    """
    _authenticate(user_id, api_key)
    res = _get_result(device, jobid, user_id, api_key)
    return res


def send(info, device=RIGETTI_DEVICES[0], user_id=None, api_key=None,
         shots=1, verbose=False):
    """
    Sends Quil through the Rigetti Forest/API and runs the quantum circuit.

    Args:
        info: Contains Quil representation of the circuit to run.
        device (str): Either '8Q-Agave' or '19Q-Acorn'
        user_id (str): Rigetti User ID
        api_key (str): Rigetti API Key
        shots (int): Number of runs of the same circuit to collect statistics.
        verbose (bool): If True, additional information is printed if available.
            Otherwise, the backend simply registers
            one measurement result.
    """
    try:
        # check if the device is online
        if device in RIGETTI_DEVICES:
            online = is_online(device, user_id, api_key)

            if not online:
                print("The device is offline (for maintenance?). Use the "
                      "simulator instead or try again later.")
                raise DeviceOfflineError("Device is offline.")

        if verbose:
            print("- Authenticating...")
        _authenticate(user_id, api_key)
        if verbose:
            print("- Running code: {}".format(
                info['quils'][0]['quil']))
        execution_id = _run(info, device, user_id, api_key, shots)
        if verbose:
            print("- Waiting for results...")
        res = _get_result(device, execution_id, user_id, api_key)
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


def _authenticate(user_id=None, api_key=None):
    """
    :param user_id:
    :param api_key:
    :return:
    """
    if user_id is None:
        try:
            input_fun = raw_input
        except NameError:
            input_fun = input
        email = input_fun('Rigetti User ID (not email) > ')
    if api_key is None:
        api_key = getpass.getpass(prompt='Rigetti API Key > ')

def _run(runcodes, device, user_id, api_key, shots):
    suffix = ''
    internal_code = runcodes["quils"][0]["quil"]

    # determine maximum register accessed in the code
    findDigit = re.compile(r'\d+')
    nums = findDigit.findall(internal_code)
    max_register = 0
    for num in nums:
        max_register = max(max_register, int(num))

    # r = requests.post(urljoin(_old_api_url, suffix),
    #                 json={
    #                     "type": "multishot",
    #                     "addresses": range(0, max_register + 1),
    #                     "trials": runcodes["shots"],
    #                     "quil-instructions": internal_code
    #                     # gate-noise
    #                     # measurement-noise
    #                 },
    #                 headers={
    #                     "Content-Type": "application/json",
    #                     "X-Api-Key": api_key,
    #                     "X-User-Id": user_id
    #                 })
    #   execution_id = -1

    suffix = 'job'
    r = requests.post(urljoin(_api_url, suffix),
                      json={
                        "machine": "QVM",
                        "program": {
                            "type": "multishot-measure",
                            "qubits": list(range(0, max_register + 1)),
                            "trials": runcodes["shots"],
                            "compiled-quil": internal_code + "\n"
                        }
                        # , "device": ""
                      },
                      headers={
                        "Content-Type": "application/json",
                        "X-Api-Key": api_key,
                        "X-User-Id": user_id
                      })
    r.raise_for_status()
    r_json = r.json()
    execution_id = r_json["jobId"]
    return execution_id


def _get_result(device, execution_id, user_id, api_key, num_retries=3000,
                interval=1):
    suffix = 'job/{execution_id}'.format(execution_id=execution_id)
    status_url = urljoin(_api_url, 'devices')

    print("Waiting for results. [Job ID: {}]".format(execution_id))

    for retries in range(num_retries):
        r = requests.get(urljoin(_api_url, suffix),
            headers={
              "Content-Type": "application/json",
              "X-Api-Key": api_key,
              "X-User-Id": user_id
            })
        r.raise_for_status()

        r_json = r.json()
        if 'result' in r_json and 'status' in r_json and r_json['status'] != 'RUNNING':
            return r_json['result']
        time.sleep(interval)
        if device in RIGETTI_DEVICES and retries % 60 == 0:
            r = requests.get(status_url, headers={
                "X-Api-Key": api_key,
                "X-User-Id": user_id,
                "Accept": "application/octet-stream"
            })
            r_json = r.json()
            if device not in r_json["devices"] or not r_json['devices'][device]:
                raise DeviceOfflineError("Device went offline. The ID of your "
                                         "submitted job is {}."
                                         .format(execution_id))
    #         if 'lengthQueue' in r_json:
    #             print("Currently there are {} jobs queued for execution on {}."
    #                   .format(r_json['lengthQueue'], device))
    # raise Exception("Timeout. The ID of your submitted job is {}."
    #                 .format(execution_id))
