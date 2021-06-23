# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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

""" HTTP Client for the IonQ API. """

import getpass
import json
import signal
import time

import requests
from requests import Session
from requests.compat import urljoin

from ._ionq_exc import (
    DeviceOfflineError,
    DeviceTooSmall,
    JobSubmissionError,
    RequestTimeoutError,
)

_API_URL = 'https://api.ionq.co/v0.1/jobs/'


class IonQ(Session):
    """A requests.Session based HTTP client for the IonQ API."""

    def __init__(self, verbose=False):
        super().__init__()
        self.backends = dict()
        self.timeout = 5.0
        self.token = None
        self._verbose = verbose

    def update_devices_list(self):
        """Update the list of devices this backend can support."""
        self.backends = {
            'ionq_simulator': {
                'nq': 29,
                'target': 'simulator',
            },
            'ionq_qpu': {
                'nq': 11,
                'target': 'qpu',
            },
        }
        if self._verbose:  # pragma: no cover
            print('- List of IonQ devices available:')
            print(self.backends)

    def is_online(self, device):
        """Check if a given device is online.

        Args:
            device (str): An IonQ device name.

        Returns:
            bool: True if device is online, else False.
        """
        return device in self.backends

    def can_run_experiment(self, info, device):
        """
        Determine whether or not the desired device has enough allocatable
        qubits to run something.

        This returns a three-element tuple with whether or not the experiment
        can be run, the max number of qubits possible, and the number of qubits
        needed to run this experiment.

        Args:
            info (dict): A dict containing number of shots, qubits, and
                a circuit.
            device (str): An IonQ device name.
        Returns:
            tuple(bool, int, int): Whether the operation can be run, max
                number of qubits the device supports, and number of qubits
                required for the experiment.
        """
        nb_qubit_max = self.backends[device]['nq']
        nb_qubit_needed = info['nq']
        return nb_qubit_needed <= nb_qubit_max, nb_qubit_max, nb_qubit_needed

    def authenticate(self, token=None):
        """Set an Authorization header for this session.

        If no token is provided, an prompt will appear to ask for one.

        Args:
            token (str): IonQ user API token.
        """
        if token is None:
            token = getpass.getpass(prompt='IonQ apiKey > ')
        if not token:
            raise RuntimeError('An authentication token is required!')
        self.headers.update({'Authorization': 'apiKey {}'.format(token)})
        self.token = token

    def run(self, info, device):
        """Run a circuit from ``info`` on the specified ``device``.

        Args:
            info (dict): A dict containing number of shots, qubits, and
                a circuit.
            device (str): An IonQ device name.

        Raises:
            JobSubmissionError: If the job creation response from IonQ's API
                had a failure result.

        Returns:
            str: The ID of a newly submitted Job.
        """
        argument = {
            'target': self.backends[device]['target'],
            'metadata': {
                'sdk': 'ProjectQ',
                'meas_qubit_ids': json.dumps(info['meas_qubit_ids']),
            },
            'shots': info['shots'],
            'registers': {'meas_mapped': info['meas_mapped']},
            'lang': 'json',
            'body': {
                'qubits': info['nq'],
                'circuit': info['circuit'],
            },
        }

        # _API_URL[:-1] strips the trailing slash.
        # TODO: Add comprehensive error parsing for non-200 responses.
        req = super().post(_API_URL[:-1], json=argument)
        req.raise_for_status()

        # Process the response.
        r_json = req.json()
        status = r_json['status']

        # Return the job id.
        if status == 'ready':
            return r_json['id']

        # Otherwise, extract any provided failure info and raise an exception.
        failure = r_json.get('failure') or {
            'code': 'UnknownError',
            'error': 'An unknown error occurred!',
        }
        raise JobSubmissionError(
            "{}: {} (status={})".format(
                failure['code'],
                failure['error'],
                status,
            )
        )

    def get_result(self, device, execution_id, num_retries=3000, interval=1):
        """Given a backend and ID, fetch the results for this job's execution.

        The return dictionary should have at least:

            * ``nq`` (int): Number of qubits for this job.
            * ``output_probs`` (dict): Map of integer states to probability values.

        Args:
            device (str): The device used to run this job.
            execution_id (str): An IonQ Job ID.
            num_retries (int, optional): Number of times to retry the fetch
                before raising a timeout error. Defaults to 3000.
            interval (int, optional): Number of seconds to wait between retries.
                Defaults to 1.

        Raises:
            Exception: If the process receives a kill signal before completion.
            Exception: If the job is in an unknown processing state.
            DeviceOfflineError: If the provided device is not online.
            RequestTimeoutError: If we were unable to retrieve the job results
                after ``num_retries`` attempts.

        Returns:
            dict: A dict of job data for an engine to consume.
        """

        if self._verbose:  # pragma: no cover
            print("Waiting for results. [Job ID: {}]".format(execution_id))

        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def _handle_sigint_during_get_result(*_):  # pragma: no cover
            raise Exception("Interrupted. The ID of your submitted job is {}.".format(execution_id))

        signal.signal(signal.SIGINT, _handle_sigint_during_get_result)

        try:
            for retries in range(num_retries):
                req = super().get(urljoin(_API_URL, execution_id))
                req.raise_for_status()
                r_json = req.json()
                status = r_json['status']

                # Check if job is completed.
                if status == 'completed':
                    meas_mapped = r_json['registers']['meas_mapped']
                    meas_qubit_ids = json.loads(r_json['metadata']['meas_qubit_ids'])
                    output_probs = r_json['data']['registers']['meas_mapped']
                    return {
                        'nq': r_json['qubits'],
                        'output_probs': output_probs,
                        'meas_mapped': meas_mapped,
                        'meas_qubit_ids': meas_qubit_ids,
                    }

                # Otherwise, make sure it is in a known healthy state.
                if status not in ('ready', 'running', 'submitted'):
                    # TODO: Add comprehensive API error processing here.
                    raise Exception("Error while running the code: {}.".format(status))

                # Sleep, then check availability before trying again.
                time.sleep(interval)
                if self.is_online(device) and retries % 60 == 0:
                    self.update_devices_list()
                    if not self.is_online(device):  # pragma: no cover
                        raise DeviceOfflineError(
                            "Device went offline. The ID of " "your submitted job is {}.".format(execution_id)
                        )
        finally:
            if original_sigint_handler is not None:
                signal.signal(signal.SIGINT, original_sigint_handler)

        raise RequestTimeoutError("Timeout. The ID of your submitted job is {}.".format(execution_id))


def show_devices(verbose=False):
    """Show the currently available device list for the IonQ provider.

    Args:
        verbose (bool): If True, additional information is printed

    Returns:
        list: list of available devices and their properties.
    """
    ionq_session = IonQ(verbose=verbose)
    ionq_session.update_devices_list()
    return ionq_session.backends


def retrieve(
    device,
    token,
    jobid,
    num_retries=3000,
    interval=1,
    verbose=False,
):  # pylint: disable=too-many-arguments
    """Retrieve an already submitted IonQ job.

    Args:
        device (str): The name of an IonQ device.
        token (str): An IonQ API token.
        jobid (str): An IonQ Job ID.
        num_retries (int, optional): Number of times to retry while the job is
            not finished. Defaults to 3000.
        interval (int, optional): Sleep interval between retries, in seconds.
            Defaults to 1.
        verbose (bool, optional): Whether to print verbose output.
            Defaults to False.

    Returns:
        dict: A dict with job submission results.
    """
    ionq_session = IonQ(verbose=verbose)
    ionq_session.authenticate(token)
    ionq_session.update_devices_list()
    res = ionq_session.get_result(
        device,
        jobid,
        num_retries=num_retries,
        interval=interval,
    )
    return res


def send(
    info,
    device='ionq_simulator',
    token=None,
    num_retries=100,
    interval=1,
    verbose=False,
):  # pylint: disable=too-many-arguments,too-many-locals
    """Submit a job to the IonQ API.

    The ``info`` dict should have at least the following keys::

        * nq (int): Number of qubits this job will need.
        * shots (dict): The number of shots to use for this job.
        * meas_mapped (list): A list of qubits to measure.
        * circuit (list): A list of JSON-serializable IonQ gate representations.

    Args:
        info (dict): A dictionary with
        device (str, optional): The IonQ device to run this on. Defaults to 'ionq_simulator'.
        token (str, optional): An IonQ API token. Defaults to None.
        num_retries (int, optional): Number of times to retry while the job is
            not finished. Defaults to 100.
        interval (int, optional): Sleep interval between retries, in seconds.
            Defaults to 1.
        verbose (bool, optional): Whether to print verbose output.
            Defaults to False.

    Raises:
        DeviceOfflineError: If the desired device is not available for job
            processing.
        DeviceTooSmall: If the job has a higher qubit requirement than the
            device supports.

    Returns:
        dict: An intermediate dict representation of an IonQ job result.
    """
    try:
        ionq_session = IonQ(verbose=verbose)

        if verbose:  # pragma: no cover
            print("- Authenticating...")
        if verbose and token is not None:  # pragma: no cover
            print('user API token: ' + token)
        ionq_session.authenticate(token)

        # check if the device is online
        ionq_session.update_devices_list()
        online = ionq_session.is_online(device)

        # useless for the moment
        if not online:  # pragma: no cover
            print("The device is offline (for maintenance?). Use the " "simulator instead or try again later.")
            raise DeviceOfflineError("Device is offline.")

        # check if the device has enough qubit to run the code
        runnable, qmax, qneeded = ionq_session.can_run_experiment(info, device)
        if not runnable:
            print(
                "The device is too small ({} qubits available) for the code "
                "requested({} qubits needed). Try to look for another device "
                "with more qubits".format(qmax, qneeded)
            )
            raise DeviceTooSmall("Device is too small.")
        if verbose:  # pragma: no cover
            print("- Running code: {}".format(info))
        execution_id = ionq_session.run(info, device)
        if verbose:  # pragma: no cover
            print("- Waiting for results...")
        res = ionq_session.get_result(
            device,
            execution_id,
            num_retries=num_retries,
            interval=interval,
        )
        if verbose:  # pragma: no cover
            print("- Done.")
        return res
    except requests.exceptions.HTTPError as err:
        # Re-raise auth errors, as literally nothing else will work.
        if err.response is not None:
            status_code = err.response.status_code
            if status_code in (401, 403):
                raise err

            # Try to parse client errors
            if status_code == 400:
                err_json = err.response.json()
                raise JobSubmissionError(
                    '{}: {}'.format(
                        err_json['error'],
                        err_json['message'],
                    )
                ) from err

        # Else, just print:
        print("- There was an error running your code:")
        print(err)
    except requests.exceptions.RequestException as err:
        print("- Looks like something is wrong with server:")
        print(err)
    return None


__all__ = [
    'send',
    'retrieve',
    'show_devices',
    'IonQ',
]
