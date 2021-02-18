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
# api documentation does not exist and has to be deduced from the qiskit code
# source at: https://github.com/Qiskit/qiskit-ibmq-provider

import getpass
import json
import signal
import uuid

import requests
from requests.compat import urljoin
from requests import Session

_AUTH_API_URL = ('https://auth.quantum-computing.ibm.com/api/users/'
                 'loginWithToken')
_API_URL = 'https://api.quantum-computing.ibm.com/api/'

# TODO: call to get the API version automatically
CLIENT_APPLICATION = 'ibmqprovider/0.4.4'


class IBMQ(Session):
    """
    Manage a session between ProjectQ and the IBMQ web API.
    """
    def __init__(self, **kwargs):
        super(IBMQ, self).__init__(**kwargs)  # Python 2 compatibility
        self.backends = dict()
        self.timeout = 5.0

    def get_list_devices(self, verbose=False):
        """
        Get the list of available IBM backends with their properties

        Args:
            verbose (bool): print the returned dictionnary if True

        Returns:
            (dict) backends dictionary by name device, containing the qubit
                    size 'nq', the coupling map 'coupling_map' as well as the
                    device version 'version'
        """
        list_device_url = 'Network/ibm-q/Groups/open/Projects/main/devices/v/1'
        argument = {'allow_redirects': True, 'timeout': (self.timeout, None)}
        request = super(IBMQ, self).get(urljoin(_API_URL, list_device_url),
                                        **argument)
        request.raise_for_status()
        r_json = request.json()
        self.backends = dict()
        for obj in r_json:
            self.backends[obj['backend_name']] = {
                'nq': obj['n_qubits'],
                'coupling_map': obj['coupling_map'],
                'version': obj['backend_version']
            }

        if verbose:
            print('- List of IBMQ devices available:')
            print(self.backends)
        return self.backends

    def is_online(self, device):
        """
        Check if the device is in the list of available IBM backends.

        Args:
            device (str): name of the device to check

        Returns:
            (bool) True if device is available, False otherwise
        """
        return device in self.backends

    def can_run_experiment(self, info, device):
        """
        Check if the device is big enough to run the code.

        Args:
            info (dict): dictionary sent by the backend containing the code to
                run
            device (str): name of the ibm device to use

        Returns:
            (tuple): (bool) True if device is big enough, False otherwise
                     (int) maximum number of qubit available on the device
                     (int) number of qubit needed for the circuit

        """
        nb_qubit_max = self.backends[device]['nq']
        nb_qubit_needed = info['nq']
        return nb_qubit_needed <= nb_qubit_max, nb_qubit_max, nb_qubit_needed

    def _authenticate(self, token=None):
        """
        Args:
            token (str): IBM quantum experience user API token.
        """
        if token is None:
            token = getpass.getpass(prompt="IBM QE token > ")
        if len(token) == 0:
            raise Exception('Error with the IBM QE token')
        self.headers.update({'X-Qx-Client-Application': CLIENT_APPLICATION})
        args = {
            'data': None,
            'json': {
                'apiToken': token
            },
            'timeout': (self.timeout, None)
        }
        request = super(IBMQ, self).post(_AUTH_API_URL, **args)
        request.raise_for_status()
        r_json = request.json()
        self.params.update({'access_token': r_json['id']})

    def _run(self, info, device):
        """
        Run the quantum code to the IBMQ machine.
        Update since September 2020: only protocol available is what they call
        'object storage' where a job request via the POST method gets in
        return a url link to which send the json data. A final http validates
        the data communication.

        Args:
            info (dict): dictionary sent by the backend containing the code to
                run
            device (str): name of the ibm device to use

        Returns:
            (tuple): (str) Execution Id

        """

        # STEP1: Obtain most of the URLs for handling communication with
        #        quantum device
        json_step1 = {
            'data': None,
            'json': {
                'backend': {
                    'name': device
                },
                'allowObjectStorage': True,
                'shareLevel': 'none'
            },
            'timeout': (self.timeout, None)
        }
        request = super(IBMQ, self).post(
            urljoin(_API_URL, 'Network/ibm-q/Groups/open/Projects/main/Jobs'),
            **json_step1)
        request.raise_for_status()
        r_json = request.json()
        upload_url = r_json['objectStorageInfo']['uploadUrl']
        execution_id = r_json['id']

        # STEP2: WE UPLOAD THE CIRCUIT DATA
        n_classical_reg = info['nq']
        # hack: easier to restrict labels to measured qubits
        n_qubits = n_classical_reg  # self.backends[device]['nq']
        instructions = info['json']
        maxcredit = info['maxCredits']
        c_label = [["c", i] for i in range(n_classical_reg)]
        q_label = [["q", i] for i in range(n_qubits)]

        # hack: the data value in the json quantum code is a string
        instruction_str = str(instructions).replace('\'', '\"')
        data = '{"qobj_id": "' + str(uuid.uuid4()) + '", '
        data += '"header": {"backend_name": "' + device + '", '
        data += ('"backend_version": "' + self.backends[device]['version']
                 + '"}, ')
        data += '"config": {"shots": ' + str(info['shots']) + ', '
        data += '"max_credits": ' + str(maxcredit) + ', "memory": false, '
        data += ('"parameter_binds": [], "memory_slots": '
                 + str(n_classical_reg))
        data += (', "n_qubits": ' + str(n_qubits)
                 + '}, "schema_version": "1.2.0", ')
        data += '"type": "QASM", "experiments": [{"config": '
        data += '{"n_qubits": ' + str(n_qubits) + ', '
        data += '"memory_slots": ' + str(n_classical_reg) + '}, '
        data += ('"header": {"qubit_labels": '
                 + str(q_label).replace('\'', '\"') + ', ')
        data += '"n_qubits": ' + str(n_classical_reg) + ', '
        data += '"qreg_sizes": [["q", ' + str(n_qubits) + ']], '
        data += '"clbit_labels": ' + str(c_label).replace('\'', '\"') + ', '
        data += '"memory_slots": ' + str(n_classical_reg) + ', '
        data += '"creg_sizes": [["c", ' + str(n_classical_reg) + ']], '
        data += ('"name": "circuit0", "global_phase": 0}, "instructions": ' + instruction_str
                 + '}]}')

        json_step2 = {
            'data': data,
            'params': {
                'access_token': None
            },
            'timeout': (5.0, None)
        }
        request = super(IBMQ, self).put(upload_url, **json_step2)
        request.raise_for_status()

        # STEP3: CONFIRM UPLOAD
        json_step3 = {
            'data': None,
            'json': None,
            'timeout': (self.timeout, None)
        }
        
        upload_data_url = urljoin(_API_URL,
                          'Network/ibm-q/Groups/open/Projects/main/Jobs/'+str(execution_id)
                                  +'/jobDataUploaded')
        request = super(IBMQ, self).post(upload_data_url, **json_step3)
        request.raise_for_status()

        return execution_id

    def _get_result(self,
                    device,
                    execution_id,
                    num_retries=3000,
                    interval=1,
                    verbose=False):

        job_status_url = ('Network/ibm-q/Groups/open/Projects/main/Jobs/'
                          + execution_id)


        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def _handle_sigint_during_get_result(*_):  # pragma: no cover
            raise Exception(
                "Interrupted. The ID of your submitted job is {}.".format(
                    execution_id))

        try:
            signal.signal(signal.SIGINT, _handle_sigint_during_get_result)
            for retries in range(num_retries):

                # STEP5: WAIT FOR THE JOB TO BE RUN
                json_step5 = {
                    'allow_redirects': True,
                    'timeout': (self.timeout, None)
                }
                request = super(IBMQ,
                                self).get(urljoin(_API_URL, job_status_url),
                                          **json_step5)
                request.raise_for_status()
                r_json = request.json()
                acceptable_status = ['VALIDATING', 'VALIDATED', 'RUNNING']
                if r_json['status'] == 'COMPLETED':
                    # STEP6: Get the endpoint to get the result
                    json_step6 = {
                        'allow_redirects': True,
                        'timeout': (self.timeout, None)
                    }
                    request = super(IBMQ, self).get(
                        urljoin(_API_URL,
                                job_status_url + '/resultDownloadUrl'),
                        **json_step6)
                    request.raise_for_status()
                    r_json = request.json()

                    # STEP7: Get the result
                    json_step7 = {
                        'allow_redirects': True,
                        'params': {
                            'access_token': None
                        },
                        'timeout': (self.timeout, None)
                    }
                    request = super(IBMQ, self).get(r_json['url'],
                                                    **json_step7)
                    r_json = request.json()
                    result = r_json['results'][0]

                    # STEP8: Confirm the data was downloaded
                    json_step8 = {
                        'data': None,
                        'json': None,
                        'timeout': (5.0, None)
                    }
                    request = super(IBMQ, self).post(
                        urljoin(_API_URL,
                                job_status_url + '/resultDownloaded'),
                        **json_step8)
                    r_json = request.json()
                    return result

                # Note: if stays stuck if 'Validating' mode, then sthg went
                #       wrong in step 3
                if r_json['status'] not in acceptable_status:
                    raise Exception(
                        "Error while running the code. Last status: {}.".
                        format(r_json['status']))
                time.sleep(interval)
                if self.is_online(device) and retries % 60 == 0:
                    self.get_list_devices()
                    if not self.is_online(device):
                        raise DeviceOfflineError(
                            "Device went offline. The ID of "
                            "your submitted job is {}.".format(execution_id))

        finally:
            if original_sigint_handler is not None:
                signal.signal(signal.SIGINT, original_sigint_handler)

        raise Exception("Timeout. The ID of your submitted job is {}.".format(
            execution_id))


class DeviceTooSmall(Exception):
    pass


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
        except NameError:  # pragma: no cover
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

    def _handle_sigint_during_get_result(*_):  # pragma: no cover
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
