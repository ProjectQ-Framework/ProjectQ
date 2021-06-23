# -*- coding: utf-8 -*-
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

""" Back-end to run quantum program on IBM QE cloud platform"""


# helpers to run the jsonified gate sequence on ibm quantum experience server
# api documentation does not exist and has to be deduced from the qiskit code
# source at: https://github.com/Qiskit/qiskit-ibmq-provider

import getpass
import time
import signal
import uuid

import requests
from requests.compat import urljoin
from requests import Session

_AUTH_API_URL = 'https://auth.quantum-computing.ibm.com/api/users/loginWithToken'
_API_URL = 'https://api.quantum-computing.ibm.com/api/'

# TODO: call to get the API version automatically
CLIENT_APPLICATION = 'ibmqprovider/0.4.4'


class IBMQ(Session):
    """
    Manage a session between ProjectQ and the IBMQ web API.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        request = super().get(urljoin(_API_URL, list_device_url), **argument)
        request.raise_for_status()
        r_json = request.json()
        self.backends = dict()
        for obj in r_json:
            self.backends[obj['backend_name']] = {
                'nq': obj['n_qubits'],
                'coupling_map': obj['coupling_map'],
                'version': obj['backend_version'],
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

    def authenticate(self, token=None):
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
            'json': {'apiToken': token},
            'timeout': (self.timeout, None),
        }
        request = super().post(_AUTH_API_URL, **args)
        request.raise_for_status()
        r_json = request.json()
        self.params.update({'access_token': r_json['id']})

    def run(self, info, device):  # pylint: disable=too-many-locals
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
                'backend': {'name': device},
                'allowObjectStorage': True,
                'shareLevel': 'none',
            },
            'timeout': (self.timeout, None),
        }
        request = super().post(
            urljoin(_API_URL, 'Network/ibm-q/Groups/open/Projects/main/Jobs'),
            **json_step1,
        )
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
        data += '"backend_version": "' + self.backends[device]['version'] + '"}, '
        data += '"config": {"shots": ' + str(info['shots']) + ', '
        data += '"max_credits": ' + str(maxcredit) + ', "memory": false, '
        data += '"parameter_binds": [], "memory_slots": ' + str(n_classical_reg)
        data += ', "n_qubits": ' + str(n_qubits) + '}, "schema_version": "1.2.0", '
        data += '"type": "QASM", "experiments": [{"config": '
        data += '{"n_qubits": ' + str(n_qubits) + ', '
        data += '"memory_slots": ' + str(n_classical_reg) + '}, '
        data += '"header": {"qubit_labels": ' + str(q_label).replace('\'', '\"') + ', '
        data += '"n_qubits": ' + str(n_classical_reg) + ', '
        data += '"qreg_sizes": [["q", ' + str(n_qubits) + ']], '
        data += '"clbit_labels": ' + str(c_label).replace('\'', '\"') + ', '
        data += '"memory_slots": ' + str(n_classical_reg) + ', '
        data += '"creg_sizes": [["c", ' + str(n_classical_reg) + ']], '
        data += '"name": "circuit0", "global_phase": 0}, "instructions": ' + instruction_str + '}]}'

        json_step2 = {
            'data': data,
            'params': {'access_token': None},
            'timeout': (5.0, None),
        }
        request = super().put(upload_url, **json_step2)
        request.raise_for_status()

        # STEP3: CONFIRM UPLOAD
        json_step3 = {'data': None, 'json': None, 'timeout': (self.timeout, None)}

        upload_data_url = urljoin(
            _API_URL,
            'Network/ibm-q/Groups/open/Projects/main/Jobs/' + str(execution_id) + '/jobDataUploaded',
        )
        request = super().post(upload_data_url, **json_step3)
        request.raise_for_status()

        return execution_id

    def get_result(
        self, device, execution_id, num_retries=3000, interval=1, verbose=False
    ):  # pylint: disable=too-many-arguments,too-many-locals
        """
        Get the result of an execution
        """

        job_status_url = 'Network/ibm-q/Groups/open/Projects/main/Jobs/' + execution_id

        if verbose:
            print("Waiting for results. [Job ID: {}]".format(execution_id))

        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def _handle_sigint_during_get_result(*_):  # pragma: no cover
            raise Exception("Interrupted. The ID of your submitted job is {}.".format(execution_id))

        try:
            signal.signal(signal.SIGINT, _handle_sigint_during_get_result)
            for retries in range(num_retries):

                # STEP5: WAIT FOR THE JOB TO BE RUN
                json_step5 = {'allow_redirects': True, 'timeout': (self.timeout, None)}
                request = super().get(urljoin(_API_URL, job_status_url), **json_step5)
                request.raise_for_status()
                r_json = request.json()
                acceptable_status = ['VALIDATING', 'VALIDATED', 'RUNNING']
                if r_json['status'] == 'COMPLETED':
                    # STEP6: Get the endpoint to get the result
                    json_step6 = {
                        'allow_redirects': True,
                        'timeout': (self.timeout, None),
                    }
                    request = super().get(
                        urljoin(_API_URL, job_status_url + '/resultDownloadUrl'),
                        **json_step6,
                    )
                    request.raise_for_status()
                    r_json = request.json()

                    # STEP7: Get the result
                    json_step7 = {
                        'allow_redirects': True,
                        'params': {'access_token': None},
                        'timeout': (self.timeout, None),
                    }
                    request = super().get(r_json['url'], **json_step7)
                    r_json = request.json()
                    result = r_json['results'][0]

                    # STEP8: Confirm the data was downloaded
                    json_step8 = {'data': None, 'json': None, 'timeout': (5.0, None)}
                    request = super().post(
                        urljoin(_API_URL, job_status_url + '/resultDownloaded'),
                        **json_step8,
                    )
                    r_json = request.json()
                    return result

                # Note: if stays stuck if 'Validating' mode, then sthg went
                #       wrong in step 3
                if r_json['status'] not in acceptable_status:
                    raise Exception("Error while running the code. Last status: {}.".format(r_json['status']))
                time.sleep(interval)
                if self.is_online(device) and retries % 60 == 0:
                    self.get_list_devices()
                    if not self.is_online(device):
                        raise DeviceOfflineError(
                            "Device went offline. The ID of your submitted job is {}.".format(execution_id)
                        )

        finally:
            if original_sigint_handler is not None:
                signal.signal(signal.SIGINT, original_sigint_handler)

        raise Exception("Timeout. The ID of your submitted job is {}.".format(execution_id))


class DeviceTooSmall(Exception):
    """Exception raised if the device is too small to run the circuit"""


class DeviceOfflineError(Exception):
    """Exception raised if a selected device is currently offline"""


def show_devices(token=None, verbose=False):
    """
    Access the list of available devices and their properties (ex: for setup
    configuration)

    Args:
        token (str): IBM quantum experience user API token.
        verbose (bool): If True, additional information is printed

    Returns:
        (list) list of available devices and their properties
    """
    ibmq_session = IBMQ()
    ibmq_session.authenticate(token=token)
    return ibmq_session.get_list_devices(verbose=verbose)


def retrieve(device, token, jobid, num_retries=3000, interval=1, verbose=False):  # pylint: disable=too-many-arguments
    """
    Retrieves a previously run job by its ID.

    Args:
        device (str): Device on which the code was run / is running.
        token (str): IBM quantum experience user API token.
        jobid (str): Id of the job to retrieve

    Returns:
        (dict) result form the IBMQ server
    """
    ibmq_session = IBMQ()
    ibmq_session.authenticate(token)
    ibmq_session.get_list_devices(verbose)
    res = ibmq_session.get_result(device, jobid, num_retries=num_retries, interval=interval, verbose=verbose)
    return res


def send(
    info,
    device='ibmq_qasm_simulator',
    token=None,
    shots=None,
    num_retries=3000,
    interval=1,
    verbose=False,
):  # pylint: disable=too-many-arguments
    """
    Sends QASM through the IBM API and runs the quantum circuit.

    Args:
        info(dict): Contains representation of the circuit to run.
        device (str): name of the ibm device. Simulator chosen by default
        token (str): IBM quantum experience user API token.
        shots (int): Number of runs of the same circuit to collect statistics.
        verbose (bool): If True, additional information is printed, such as
            measurement statistics. Otherwise, the backend simply registers
            one measurement result (same behavior as the projectq Simulator).

    Returns:
        (dict) result form the IBMQ server

    """
    try:
        ibmq_session = IBMQ()
        # Shots argument deprecated, as already
        if shots is not None:
            info['shots'] = shots
        if verbose:
            print("- Authenticating...")
            if token is not None:
                print('user API token: ' + token)
        ibmq_session.authenticate(token)

        # check if the device is online
        ibmq_session.get_list_devices(verbose)
        online = ibmq_session.is_online(device)
        if not online:
            print("The device is offline (for maintenance?). Use the simulator instead or try again later.")
            raise DeviceOfflineError("Device is offline.")

        # check if the device has enough qubit to run the code
        runnable, qmax, qneeded = ibmq_session.can_run_experiment(info, device)
        if not runnable:
            print(
                (
                    "The device is too small ({} qubits available) for the code "
                    + "requested({} qubits needed) Try to look for another "
                    + "device with more qubits"
                ).format(qmax, qneeded)
            )
            raise DeviceTooSmall("Device is too small.")
        if verbose:
            print("- Running code: {}".format(info))
        execution_id = ibmq_session.run(info, device)
        if verbose:
            print("- Waiting for results...")
        res = ibmq_session.get_result(
            device,
            execution_id,
            num_retries=num_retries,
            interval=interval,
            verbose=verbose,
        )
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
    return None
