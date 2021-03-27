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

"""
Back-end to run quantum program on AWS Braket supported devices.

This backend requires the official AWS SDK for Python, Boto3.
The installation is very simple
> pip install boto3
"""

import getpass
import signal
import re
import time
import boto3
import botocore

import json


class AWSBraket():
    """
    Manage a session between ProjectQ and AWS Braket service.
    """
    def __init__(self):
        self.backends = dict()
        self.timeout = 5.0
        self._credentials = dict()
        self._s3_folder = []

    def _authenticate(self, credentials=None):
        """
        Args:
            credentials (dict): mapping the AWS key credentials as
                the AWS_ACCESS_KEY_ID and AWS_SECRET_KEY.
        """
        if credentials is None:
            credentials['AWS_ACCESS_KEY_ID'] = getpass.getpass(
                prompt="Enter AWS_ACCESS_KEY_ID: ")
            credentials['AWS_SECRET_KEY'] = getpass.getpass(
                prompt="Enter AWS_SECRET_KEY: ")

        self._credentials = credentials

    def _get_s3_folder(self, s3_folder=None):
        """
        Args:
           s3_folder (list): contains the S3 bucket and directory
           to store the results.
        """
        if s3_folder is None:
            S3Bucket = input("Enter the S3 Bucket configured in Braket: ")
            S3Directory = input(
                "Enter the Directory created in the S3 Bucket: ")
            s3_folder = [S3Bucket, S3Directory]

        self._s3_folder = s3_folder

    def get_list_devices(self, verbose=False):
        """
        Get the list of available devices with their basic properties

        Args:
            verbose (bool): print the returned dictionnary if True

        Returns:
            (dict) backends dictionary by deviceName, containing the qubit
                   size 'nq', the coupling map 'coupling_map' if applicable
                   (IonQ device as an ion device is having full connectivity)
                   and the Schema Header version 'version', because it seems
                   that no device version is available by now
        """
        # TODO: refresh region_names if more regions get devices available
        self.backends = dict()
        region_names = ['us-west-1', 'us-east-1']
        for region in region_names:
            client = boto3.client('braket', region_name=region,
                aws_access_key_id=self._credentials['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=self._credentials['AWS_SECRET_KEY'])
            filters = []
            devicelist = client.search_devices(filters=filters)
            for result in devicelist['devices']:
                if result['deviceType'] not in ['QPU', 'SIMULATOR']:
                    continue
                if result['deviceType'] == 'QPU':
                    deviceCapabilities = json.loads(client.get_device(
                        deviceArn=result['deviceArn'])['deviceCapabilities'])
                    self.backends[result['deviceName']] = {
                        'nq': deviceCapabilities['paradigm']['qubitCount'],
                        'coupling_map':
                            deviceCapabilities['paradigm']['connectivity'][
                                'connectivityGraph'],
                        'version':
                            deviceCapabilities['braketSchemaHeader'][
                                'version'],
                        'location':
                            deviceCapabilities['service']['deviceLocation'],
                        'deviceArn': result['deviceArn'],
                        'deviceParameters':
                            deviceCapabilities['deviceParameters'][
                                'properties']['braketSchemaHeader'][
                                    'const'],
                        'deviceModelParameters':
                            deviceCapabilities['deviceParameters'][
                                'definitions']['GateModelParameters'][
                                    'properties']['braketSchemaHeader'][
                                        'const'],
                    }
                # Unfortunatelly the Capabilities schemas are not homogeneus
                # for real devices and simulators
                elif result['deviceType'] == 'SIMULATOR':
                    deviceCapabilities = json.loads(client.get_device(
                        deviceArn=result['deviceArn'])['deviceCapabilities'])
                    self.backends[result['deviceName']] = {
                        'nq': deviceCapabilities['paradigm']['qubitCount'],
                        'coupling_map': {},
                        'version':
                            deviceCapabilities['braketSchemaHeader'][
                                'version'],
                        'location': 'us-east-1',
                        'deviceArn': result['deviceArn'],
                        'deviceParameters':
                            deviceCapabilities['deviceParameters'][
                                'properties']['braketSchemaHeader'][
                                    'const'],
                        'deviceModelParameters':
                            deviceCapabilities['deviceParameters'][
                                'definitions']['GateModelParameters'][
                                    'properties']['braketSchemaHeader'][
                                        'const'],
                    }

        if verbose:
            print('- List of AWSBraket devices available:')
            print(list(self.backends))

        return self.backends

    def is_online(self, device):
        """
        Check if the device is in the list of available backends.

        Args:
            device (str): name of the device to check

        Returns:
            (bool) True if device is available, False otherwise
        """
        # TODO: Add info for the device if it is actually ONLINE
        return device in self.backends

    def can_run_experiment(self, info, device):
        """
        Check if the device is big enough to run the code.

        Args:
            info (dict): dictionary sent by the backend containing the code to
                run
            device (str): name of the device to use

        Returns:
            (tuple): (bool) True if device is big enough, False otherwise
                     (int) maximum number of qubit available on the device
                     (int) number of qubit needed for the circuit

        """
        nb_qubit_max = self.backends[device]['nq']
        nb_qubit_needed = info['nq']
        return nb_qubit_needed <= nb_qubit_max, nb_qubit_max, nb_qubit_needed

    def _run(self, info, device):
        """
        Run the quantum code to the AWS Braket selected device.

        Args:
            info (dict): dictionary sent by the backend containing the code to
                run
            device (str): name of the device to use

        Returns:
            taskArn (str): The Arn of the task


        """
        argument = {
            'circ': info['circuit'],
            's3_folder': self._s3_folder,
            'shots': info['shots'],
        }

        credentials = self._credentials
        region_name = self.backends[device]['location']
        deviceParameters = {
            'braketSchemaHeader': self.backends[device]['deviceParameters'],
            'paradigmParameters': {
                'braketSchemaHeader':
                    self.backends[device]['deviceModelParameters'],
                'qubitCount': info['nq'],
                'disableQubitRewiring': False,
            },
        }
        deviceParameters = json.dumps(deviceParameters)

        client_braket = boto3.client('braket', region_name=region_name,
                    aws_access_key_id=self._credentials['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=self._credentials['AWS_SECRET_KEY'])

        deviceArn = self.backends[device]['deviceArn']
        response = client_braket.create_quantum_task(
            action=argument['circ'],
            deviceArn=deviceArn,
            deviceParameters=deviceParameters,
            outputS3Bucket=argument['s3_folder'][0],
            outputS3KeyPrefix=argument['s3_folder'][1],
            shots=argument['shots'])
        taskArn = response['quantumTaskArn']

        return taskArn

    def _get_result(self,
                    execution_id,
                    num_retries=30,
                    interval=1,
                    verbose=False):

        if verbose:
            print("Waiting for results. [Job Arn: {}]".format(execution_id))

        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def _handle_sigint_during_get_result(*_):  # pragma: no cover
            raise Exception(
                "Interrupted. The Arn of your submitted job is {}.".format(
                    execution_id))

        def _calculate_measurement_probs(measurements):
            """
            Calculate the measurement probabilities based on the
            list of measurements for a job sent to a SV1 Braket simulator

            Args:
                measurements (list): list of measurements

            Returns:
                measurementsProbabilities (dict): The measurements
                with their probabilities
            """
            total_mes = len(measurements)
            unique_mes = [list(x) for x in set(tuple(x) for x in measurements)]
            total_unique_mes = len(unique_mes)
            len_qubits = len(unique_mes[0])
            measurementsProbabilities = {}
            for i in range(total_unique_mes):
                strqubits = ''
                for nq in range(len_qubits):
                    strqubits += str(unique_mes[i][nq])
                prob = measurements.count(unique_mes[i])/total_mes
                measurementsProbabilities[strqubits] = prob

            return measurementsProbabilities

        # The region_name is obtained from the taskArn itself
        region_name = re.split(':', execution_id)[3]
        client_braket = boto3.client('braket', region_name=region_name,
                    aws_access_key_id=self._credentials['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=self._credentials['AWS_SECRET_KEY'])

        try:
            signal.signal(signal.SIGINT, _handle_sigint_during_get_result)

            for retries in range(num_retries):

                quantum_task = client_braket.get_quantum_task(
                    quantumTaskArn=execution_id)
                status = quantum_task['status']
                bucket = quantum_task['outputS3Bucket']
                directory = quantum_task['outputS3Directory']
                resultsojectname = directory + '/results.json'
                if status == 'COMPLETED':
                    # Get the device type
                    # to obtian the correct measurement structure
                    deviceArn = quantum_task['deviceArn']
                    devicetype_used = client_braket.get_device(
                        deviceArn=deviceArn)['deviceType']
                    # Get the results from S3
                    client_s3 = boto3.client('s3',
                        aws_access_key_id=self._credentials[
                            'AWS_ACCESS_KEY_ID'],
                        aws_secret_access_key=self._credentials[
                            'AWS_SECRET_KEY'])
                    s3result = client_s3.get_object(Bucket=bucket,
                                                    Key=resultsojectname)
                    if verbose:
                        print("Results obtained. [Status: {}]".format(status))
                    result_content = json.loads(s3result['Body'].read())

                    if devicetype_used == 'QPU':
                        return result_content['measurementProbabilities']
                    if devicetype_used == 'SIMULATOR':
                        measurementProb = _calculate_measurement_probs(
                            result_content['measurements'])
                        return measurementProb
                if status == 'FAILED':
                    failurereason = quantum_task['failureReason']
                    raise Exception("Error while running the code: {}. "
                                    "The failure reason was: {}.".format(
                                        status, failurereason))
                if status == 'CANCELLING':
                    raise Exception("The job received a CANCEL "
                                    "operation: {}.".format(status))
                time.sleep(interval)
                # NOTE: Be aware that AWS is billing if a lot of API calls
                # are executed, therefore the num_repetitions is set to a small
                # number by default.
                # For QPU devices the job is always queued and there are
                # some working hours available.
                # In addition the results and state is writen in the
                # results.json file in the S3 Bucket and do not depend
                # on the status of the device

        finally:
            if original_sigint_handler is not None:
                signal.signal(signal.SIGINT, original_sigint_handler)

        raise Exception("Timeout. "
                        "The Arn of your submitted job is {} and the status "
                        "of the job is {}.".format(execution_id, status))


class DeviceTooSmall(Exception):
    pass


class DeviceOfflineError(Exception):
    pass


def show_devices(credentials=None, verbose=False):
    """
    Access the list of available devices and their properties (ex: for setup
    configuration)

    Args:
        credentials (dict): mapping the AWS key credentials as
            the AWS_ACCESS_KEY_ID and AWS_SECRET_KEY.
        verbose (bool): If True, additional information is printed

    Returns:
        (list) list of available devices and their properties
    """
    awsbraket_session = AWSBraket()
    awsbraket_session._authenticate(credentials=credentials)
    return awsbraket_session.get_list_devices(verbose=verbose)

# TODO: Create a Show Online properties per device


def retrieve(credentials,
             taskArn,
             num_retries=30,
             interval=1,
             verbose=False):
    """
    Retrieves a job/task by its Arn.

    Args:
        credentials (dict): mapping the AWS key credentials as
            the AWS_ACCESS_KEY_ID and AWS_SECRET_KEY.
        taskArn (str): The Arn of the task to retreive

    Returns:
        (dict) measurement probabilities from the result
        stored in the S3 folder
    """
    awsbraket_session = AWSBraket()
    if verbose:
        print("- Authenticating...")
        if credentials is not None:
            print("AWS credentials: "
                  + credentials['AWS_ACCESS_KEY_ID'] + ", "
                  + credentials['AWS_SECRET_KEY'])
    awsbraket_session._authenticate(credentials=credentials)
    res = awsbraket_session._get_result(taskArn,
                                        num_retries=num_retries,
                                        interval=interval,
                                        verbose=verbose)
    return res


def send(info,
         device,
         credentials,
         s3_folder,
         num_retries=30,
         interval=1,
         verbose=False):
    """
    Sends cicruit through the Boto3 SDK and runs the quantum circuit.

    Args:
        info(dict): Contains representation of the circuit to run.
        device (str): name of the AWS Braket device.
        credentials (dict): mapping the AWS key credentials as
            the AWS_ACCESS_KEY_ID and AWS_SECRET_KEY.
        s3_folder (list): contains the S3 bucket and directory
            to store the results.
        verbose (bool): If True, additional information is printed, such as
            measurement statistics. Otherwise, the backend simply registers
            one measurement result (same behavior as the projectq Simulator).

    Returns:
        (list) samples from the AWS Braket device

    """
    try:
        awsbraket_session = AWSBraket()
        if verbose:
            print("- Authenticating...")
            if credentials is not None:
                print("AWS credentials: "
                      + credentials['AWS_ACCESS_KEY_ID'] + ", "
                      + credentials['AWS_SECRET_KEY'])
        awsbraket_session._authenticate(credentials=credentials)
        awsbraket_session._get_s3_folder(s3_folder=s3_folder)

        # check if the device is online/is available
        awsbraket_session.get_list_devices(verbose)
        online = awsbraket_session.is_online(device)
        print("The job will be Queued in any case, "
              "plase take this into account")
        if not online:
            print("The device is not available. Use the "
                  "simulator instead or try another device.")
            raise DeviceOfflineError("Device is not available.")

        # check if the device has enough qubit to run the code
        runnable, qmax, qneeded = \
            awsbraket_session.can_run_experiment(info, device)
        if not runnable:
            print(
                ("The device is too small ({} qubits available) for the code "
                 + "requested({} qubits needed) Try to look for another "
                 + "device with more qubits").format(qmax, qneeded))
            raise DeviceTooSmall("Device is too small.")
        if verbose:
            print("- Running code: {}".format(info))
        taskArn = awsbraket_session._run(info, device)
        print("The task Arn is: ", taskArn,
              ". Please take note for future reference")
        if verbose:
            print("- Waiting for results...")
        res = awsbraket_session._get_result(taskArn,
                                            num_retries=num_retries,
                                            interval=interval,
                                            verbose=verbose)
        if verbose:
            print("- Done.")
        return res

    except botocore.exceptions.ClientError as error:
        error_code = error.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print("- There was an error: the access to Braket was denied")
        if error_code == 'DeviceOfflineException':
            print("- There was an error: the device is offline")
        if error_code == 'InternalServiceException':
            print("- There was an interal Bracket service error")
        if error_code == 'ServiceQuotaExceededException':
            print("- There was an error: the quota on Braket was exceed")
        if error_code == 'ValidationException':
            print("- There was a Validation error")
        print(error, error_code)
        raise
