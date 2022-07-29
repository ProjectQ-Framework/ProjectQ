#   Copyright 2022 ProjectQ-Framework (www.projectq.ch)
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

"""Client methods to run quantum programs using Azure Quantum."""

from .._exceptions import DeviceOfflineError, RequestTimeoutError


def _get_results(job, num_retries=100, interval=1, verbose=False):
    if verbose:  # pragma: no cover
        print(f"- Waiting for results. [Job ID: {job.id}]")

    try:
        return job.get_results(timeout_secs=num_retries * interval)
    except TimeoutError:
        raise RequestTimeoutError(  # pylint: disable=raise-missing-from
            f"Timeout. The ID of your submitted job is {job.id}."
        )


def send(
    input_data, num_shots, target, num_retries=100, interval=1, verbose=False, **kwargs
):  # pylint: disable=too-many-arguments
    """
    Submit a job to the Azure Quantum.

    Args:
        input_data (any): Input data for Quantum job.
        num_shots (int): Number of runs.
        target (Target), The target to run this on.
        num_retries (int, optional): Number of times to retry while the job is
            not finished. Defaults to 100.
        interval (int, optional): Sleep interval between retries, in seconds.
            Defaults to 1.
        verbose (bool, optional): Whether to print verbose output.
            Defaults to False.

    Raises:
        DeviceOfflineError: If the desired device is not available for job
            processing.

    Returns:
        dict: An intermediate dict representation of an Azure Quantum job result.
    """
    if target.current_availability != 'Available':
        raise DeviceOfflineError('Device is offline.')

    if verbose:
        print(f"- Running code: {input_data}")

    job = target.submit(circuit=input_data, num_shots=num_shots, **kwargs)

    res = _get_results(job=job, num_retries=num_retries, interval=interval, verbose=verbose)

    if verbose:
        print("- Done.")

    return res


def retrieve(job_id, target, num_retries=100, interval=1, verbose=False):
    """
    Retrieve a job from Azure Quantum.

    Args:
        job_id (str), Azure Quantum job id.
        target (Target), The target job runs on.
        num_retries (int, optional): Number of times to retry while the job is
            not finished. Defaults to 100.
        interval (int, optional): Sleep interval between retries, in seconds.
            Defaults to 1.
        verbose (bool, optional): Whether to print verbose output.
            Defaults to False.

    Returns:
        dict: An intermediate dict representation of an Azure Quantum job result.
    """
    job = target.workspace.get_job(job_id=job_id)

    res = _get_results(job=job, num_retries=num_retries, interval=interval, verbose=verbose)

    if verbose:
        print("- Done.")

    return res
