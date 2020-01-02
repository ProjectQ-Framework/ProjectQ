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
from requests import Session

_auth_api_url = 'https://auth.quantum-computing.ibm.com/api/users/loginWithToken'
_api_url = 'https://api.quantum-computing.ibm.com/api/'
CLIENT_APPLICATION = 'ibmqprovider/0.4.4'#TODO: call to get the API version automatically


class IBMQ(Session):
    def __init__(self):
        super().__init__()
        self.backends=dict()
        self.timeout=5.0

    def get_list_devices(self,verbose=False):
        list_device_url='Network/ibm-q/Groups/open/Projects/main/devices/v/1'
        argument={'allow_redirects': True, 'timeout': (self.timeout, None)}
        r = super().request('GET', urljoin(_api_url, list_device_url), **argument)

        r.raise_for_status()
        r_json=r.json()
        self.backends=dict()
        for el in r_json:
            self.backends[el['backend_name']]={'nq':el['n_qubits'],'coupling_map':el['coupling_map'],'version':el['backend_version']}
        if verbose==True:
            print('- List of IBMQ devices available:')
            print(self.backends)
        return self.backends

    def is_online(self,device):
        return device in self.backends

    def can_run_experiment(self,info,device):
        """
        check if the device is big enough to run the code

        Args:
            info (dict): dictionary sent by the backend containing the code to run
            device (str): name of the ibm device to use
        :return:
            (bool): True if device is big enough, False otherwise
        """
        nb_qubit_max=self.backends[device]['nq']
        nb_qubit_needed=info['nq']
        return nb_qubit_needed<=nb_qubit_max,nb_qubit_max,nb_qubit_needed

    def _authenticate(self,token=None):
        """
        :param token:
        :return:
        """
        if token is None:
            token = getpass.getpass(prompt='IBM Q token > ')
        self.headers.update({'X-Qx-Client-Application': CLIENT_APPLICATION})
        args={'data': None, 'json': {'apiToken': token}, 'timeout': (self.timeout, None)}
        r = super().request('POST', _auth_api_url, **args)

        r.raise_for_status()
        r_json=r.json()
        self.params.update({'access_token': r_json['id']}) 
        return 


    def _run(self,info, device):
        post_job_url='Network/ibm-q/Groups/open/Projects/main/Jobs'
        shots=info['shots']
        nq=info['nq']
        mq=self.backends[device]['nq']
        version=self.backends[device]['version']
        instructions=info['json']
        maxcredit=info['maxCredits']

        c_label=[]
        q_label=[]
        for i in range(nq):
            c_label.append(['c',i])
        for i in range(mq):
            q_label.append(['q',i])
        experiment=[{'header': {'qreg_sizes': [['q', mq]], 'n_qubits': mq, 'memory_slots': nq, 'creg_sizes': [['c', nq]], 'clbit_labels': c_label, 'qubit_labels': q_label, 'name': 'circuit0'}, 'config': {'n_qubits': mq, 'memory_slots': nq}, 'instructions':instructions}]
        argument={'data': None, 'json': {'qObject': {'type': 'QASM', 'schema_version': '1.1.0', 'config': {'shots': shots, 'max_credits': maxcredit, 'n_qubits': mq, 'memory_slots': nq, 'memory': False, 'parameter_binds': []}, 'experiments': experiment, 'header': {'backend_version': version, 'backend_name': device}, 'qobj_id': 'e72443f5-7752-4e32-9ac8-156f1f3fee18'}, 'backend': {'name': device}, 'shots': shots}, 'timeout': (self.timeout, None)}
        r = super().request('POST', urljoin(_api_url, post_job_url), **argument)
        r.raise_for_status()
        r_json=r.json()
        execution_id = r_json["id"]
        return execution_id

    def _get_result(self,device, execution_id, num_retries=3000,
                    interval=1, verbose=False):
        
        job_status_url='Network/ibm-q/Groups/open/Projects/main/Jobs/'+execution_id
        
        if verbose:
            print("Waiting for results. [Job ID: {}]".format(execution_id))

        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def _handle_sigint_during_get_result(*_):
            raise Exception("Interrupted. The ID of your submitted job is {}."
                            .format(execution_id))

        try:
            signal.signal(signal.SIGINT, _handle_sigint_during_get_result)

            for retries in range(num_retries):
                
                argument={'allow_redirects': True, 'timeout': (self.timeout, None)}
                r = super().request('GET', urljoin(_api_url, job_status_url), **argument)
                r.raise_for_status()
                r_json = r.json()
                if r_json['status']=='COMPLETED':
                    return r_json['qObjectResult']['results'][0]
                elif r_json['status']!='RUNNING':
                    raise Exception("Error while running the code: {}."
                        .format(r_json['status']))
                time.sleep(interval)
                if self.is_online(device) and retries % 60 == 0:
                    self.get_list_devices()
                    if not self.is_online(device):
                        raise DeviceOfflineError("Device went offline. The ID of "
                                                "your submitted job is {}."
                                                .format(execution_id))

        finally:
            if original_sigint_handler is not None:
                signal.signal(signal.SIGINT, original_sigint_handler)

        raise Exception("Timeout. The ID of your submitted job is {}."
                        .format(execution_id))

class DeviceTooSmall(Exception):
    pass

class DeviceOfflineError(Exception):
    pass

def show_devices(token,verbose=False):    
    """
    Access the list of available devices and their properties (ex: for setup configuration)

    Args:
        token (str): IBM quantum experience user password.
        verbose (bool): If True, additional information is printed

    Return:
        (list) list of available devices and their properties
    """
    ibmq_session=IBMQ()
    ibmq_session._authenticate(token=token)
    return ibmq_session.get_list_devices(verbose=verbose)

def retrieve(device, token, jobid, num_retries=3000,
             interval=1, verbose=False):
    """
    Retrieves a previously run job by its ID.

    Args:
        device (str): Device on which the code was run / is running.
        token (str): IBM quantum experience user password.
        jobid (str): Id of the job to retrieve
    
    Return:
        (dict) result form the IBMQ server
    """
    ibmq_session=IBMQ()
    imbq_session._authenticate(token)
    res = imbq_session._get_result(device, jobid, num_retries=num_retries,
                      interval=interval, verbose=verbose)
    return res


def send(info, device='ibmq_qasm_simulator',token=None,
         shots=1, num_retries=3000, interval=1, verbose=False):
    """
    Sends QASM through the IBM API and runs the quantum circuit.

    Args:
        info(dict): Contains representation of the circuit to run.
        device (str): name of the ibm device. Simulator chosen by default
        token (str): IBM quantum experience user password.
        shots (int): Number of runs of the same circuit to collect statistics.
        verbose (bool): If True, additional information is printed, such as
            measurement statistics. Otherwise, the backend simply registers
            one measurement result (same behavior as the projectq Simulator).

    Return:
        (dict) result form the IBMQ server

    """
    try:
        ibmq_session=IBMQ()

        if verbose:
            print("- Authenticating...")
            print('TOKEN: '+token)
        ibmq_session._authenticate(token)

        # check if the device is online
        ibmq_session.get_list_devices(verbose)
        online = ibmq_session.is_online(device)
        if not online:
            print("The device is offline (for maintenance?). Use the "
                  "simulator instead or try again later.")
            raise DeviceOfflineError("Device is offline.")
            
        # check if the device has enough qubit to run the code
        runnable,qmax,qneeded = ibmq_session.can_run_experiment(info,device)
        if not runnable:
            print("The device is too small ({} qubits available) for the code requested({} qubits needed"
                    "Try to look for another device with more qubits".format(qmax,qneeded))
            raise DeviceTooSmall("Device is too small.")
        if verbose:
            print("- Running code: {}".format(info))
        execution_id = ibmq_session._run(info, device)
        if verbose:
            print("- Waiting for results...")
        res = ibmq_session._get_result(device, execution_id,num_retries=num_retries,interval=interval, verbose=verbose)
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
