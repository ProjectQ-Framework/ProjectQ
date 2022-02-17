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

from azure.quantum import Workspace
from azure.quantum.target import IonQ, Honeywell

from ._exceptions import InvalidAzureQuantumProvider, InvalidAzureQuantumTarget


def _send_ionq(
    info,
    workspace,
    job_id=None,
    target_name='ionq.simulator',
    num_retries=100,
    interval=1,
    verbose=False,
    **kwargs
):
    if target_name not in IonQ.target_names:  # pragma: no cover
        raise InvalidAzureQuantumTarget()

    target = IonQ(
        workspace=workspace,
        name=target_name,
        **kwargs
    )

    target.submit(
        circuit=info['circuit'],
        name=job_id,
        num_shots=info['num_shots']
    )


def _send_honeywell(
    info,
    workspace,
    job_id=None,
    target_name='honeywell.hqs-lt-s1-apival',
    num_retries=100,
    interval=1,
    verbose=False,
    **kwargs
):
    if target_name not in Honeywell.target_names:  # pragma: no cover
        raise InvalidAzureQuantumTarget()


def send(
    info,
    workspace,
    provider='ionq',
    target_name='ionq.simulator',
    num_retries=100,
    interval=1,
    verbose=False,
    **kwargs
):
    """Submit a job to the Azure Quantum.

    The ``info`` dict should have at least the following keys::

        * nq (int): Number of qubits this job will need.
        * shots (dict): The number of shots to use for this job.
        * meas_mapped (list): A list of qubits to measure.
        * circuit (list): A list of JSON-serializable IonQ gate representations.

    Args:
        info (dict): A dictionary with
        workspace (Workspace): Azure Quantum Workspace.
        provider (str, optional), The provider to run this on. Defaults to ```ionq```
        target_name (str, optional): The device to run this on. Defaults to ```ionq.simulator```.
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

    if provider == 'ionq':
        _send_ionq(info, workspace, None, target_name, num_retries, interval, verbose, **kwargs)
    elif provider == 'honeywell':
        _send_honeywell(info, workspace, None, target_name, num_retries, interval, verbose, **kwargs)
    else:  # pragma: no cover
        raise InvalidAzureQuantumProvider()


def retrieve(
    workspace,
    job_id,
    provider='ionq',
    target_name='ionq.simulator',
    num_retries=100,
    interval=1,
    verbose=False,
    **kwargs
):
    pass


def estimate_cost(
    circuit,
    num_shots
):
    pass
