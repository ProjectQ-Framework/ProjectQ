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
""" Back-end to run quantum program on AWS Braket provided devices."""

import random
import json

from projectq.cengines import BasicEngine
from projectq.meta import get_control_count, LogicalQubitIDTag, has_negative_control
from projectq.types import WeakQubitRef
from projectq.ops import (
    R,
    SwapGate,
    HGate,
    Rx,
    Ry,
    Rz,
    SGate,
    Sdag,
    TGate,
    Tdag,
    XGate,
    YGate,
    ZGate,
    SqrtXGate,
    Measure,
    Allocate,
    Deallocate,
    Barrier,
    FlushGate,
    DaggeredGate,
)

# TODO: Add MatrixGate to cover the unitary operation in the SV1 simulator

from ._awsbraket_boto3_client import send, retrieve


class AWSBraketBackend(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """
    The AWS Braket Backend class, which stores the circuit, transforms it to Braket compatible, and sends the circuit
    through the Boto3 and Amazon Braket SDK.
    """

    def __init__(
        self,
        use_hardware=False,
        num_runs=1000,
        verbose=False,
        credentials=None,
        s3_folder=None,
        device='Aspen-8',
        num_retries=30,
        interval=1,
        retrieve_execution=None,
    ):  # pylint: disable=too-many-arguments
        """
        Initialize the Backend object.

        Args:
            use_hardware (bool): If True, the code is run on one of the AWS Braket backends, by default on the Rigetti
                Aspen-8 chip (instead of using the AWS Braket SV1 Simulator)
            num_runs (int): Number of runs to collect statistics.  (default is 1000)
            verbose (bool): If True, statistics are printed, in addition to the measurement result being registered
                (at the end of the circuit).
            credentials (dict): mapping the AWS key credentials as the AWS_ACCESS_KEY_ID and AWS_SECRET_KEY.
            device (str): name of the device to use. Rigetti Aspen-8 by default. Valid names are "Aspen-8", "IonQ
                Device" and "SV1"
            num_retries (int): Number of times to retry to obtain results from AWS Braket. (default is 30)
            interval (float, int): Number of seconds between successive attempts to obtain results from AWS Braket.
                (default is 1)
            retrieve_execution (str): TaskArn to retrieve instead of re-running the circuit (e.g., if previous run
                timed out).  The TaskArns have the form:
                "arn:aws:braket:us-east-1:123456789012:quantum-task/5766032b-2b47-4bf9-cg00-f11851g4015b"
        """
        BasicEngine.__init__(self)
        self._reset()
        if use_hardware:
            self.device = device
        else:
            self.device = 'SV1'
        self._clear = False
        self._num_runs = num_runs
        self._verbose = verbose
        self._credentials = credentials
        self._s3_folder = s3_folder
        self._num_retries = num_retries
        self._interval = interval
        self._probabilities = dict()
        self._circuit = ""
        self._measured_ids = []
        self._allocated_qubits = set()
        self._retrieve_execution = retrieve_execution

        # Dictionary to translate the gates from ProjectQ to AWSBraket
        self._gationary = {
            XGate: 'x',
            YGate: 'y',
            ZGate: 'z',
            HGate: 'h',
            R: 'phaseshift',
            Rx: 'rx',
            Ry: 'ry',
            Rz: 'rz',
            SGate: 's',  # NB: Sdag is 'si'
            TGate: 't',  # NB: Tdag is 'ti'
            SwapGate: 'swap',
            SqrtXGate: 'v',
        }

        # Static head and tail to be added to the circuit
        # to build the "action".
        self._circuithead = '{"braketSchemaHeader": \
{"name": "braket.ir.jaqcd.program", "version": "1"}, \
"results": [], "basis_rotation_instructions": [], \
"instructions": ['

        self._circuittail = ']}'

    def is_available(self, cmd):  # pylint: disable=too-many-return-statements,too-many-branches
        """
        Return true if the command can be executed.

        Depending on the device chosen, the operations available differ.

        The operations avialable for the Aspen-8 Rigetti device are:
        - "cz" = Control Z, "xy" = Not available in ProjectQ, "ccnot" = Toffoli (ie. controlled CNOT), "cnot" =
          Control X, "cphaseshift" = Control R, "cphaseshift00" "cphaseshift01" "cphaseshift10" = Not available
          in ProjectQ,
          "cswap" = Control Swap, "h" = H, "i" = Identity, not in ProjectQ, "iswap" = Not available in ProjectQ,
          "phaseshift" = R, "pswap" = Not available in ProjectQ, "rx" = Rx, "ry" = Ry, "rz" = Rz, "s" = S, "si" =
          Sdag, "swap" = Swap, "t" = T, "ti" = Tdag, "x" = X, "y" = Y, "z" = Z

        The operations available for the IonQ Device are:
        - "x" = X, "y" = Y, "z" = Z, "rx" = Rx, "ry" = Ry, "rz" = Rz, "h", H, "cnot" = Control X, "s" = S, "si" =
          Sdag, "t" = T, "ti" = Tdag, "v" = SqrtX, "vi" = Not available in ProjectQ, "xx" "yy" "zz" = Not available in
          ProjectQ, "swap" = Swap, "i" = Identity, not in ProjectQ

        The operations available for the StateVector simulator (SV1) are the union of the ones for Rigetti Aspen-8 and
        IonQ Device plus some more:
        - "cy" = Control Y, "unitary" = Arbitrary unitary gate defined as a matrix equivalent to the MatrixGate in
          ProjectQ, "xy" = Not available in ProjectQ

        Args:
            cmd (Command): Command for which to check availability
        """

        gate = cmd.gate
        if gate in (Measure, Allocate, Deallocate, Barrier):
            return True

        if has_negative_control(cmd):
            return False

        if self.device == 'Aspen-8':
            if get_control_count(cmd) == 2:
                return isinstance(gate, XGate)
            if get_control_count(cmd) == 1:
                return isinstance(gate, (R, ZGate, XGate, SwapGate))
            if get_control_count(cmd) == 0:
                return (
                    isinstance(
                        gate,
                        (
                            R,
                            Rx,
                            Ry,
                            Rz,
                            XGate,
                            YGate,
                            ZGate,
                            HGate,
                            SGate,
                            TGate,
                            SwapGate,
                        ),
                    )
                    or gate in (Sdag, Tdag)
                )

        if self.device == 'IonQ Device':
            if get_control_count(cmd) == 1:
                return isinstance(gate, XGate)
            if get_control_count(cmd) == 0:
                return (
                    isinstance(
                        gate,
                        (
                            Rx,
                            Ry,
                            Rz,
                            XGate,
                            YGate,
                            ZGate,
                            HGate,
                            SGate,
                            TGate,
                            SqrtXGate,
                            SwapGate,
                        ),
                    )
                    or gate in (Sdag, Tdag)
                )

        if self.device == 'SV1':
            if get_control_count(cmd) == 2:
                return isinstance(gate, XGate)
            if get_control_count(cmd) == 1:
                return isinstance(gate, (R, ZGate, YGate, XGate, SwapGate))
            if get_control_count(cmd) == 0:
                # TODO: add MatrixGate to cover the unitary operation
                # TODO: Missing XY gate in ProjectQ
                return (
                    isinstance(
                        gate,
                        (
                            R,
                            Rx,
                            Ry,
                            Rz,
                            XGate,
                            YGate,
                            ZGate,
                            HGate,
                            SGate,
                            TGate,
                            SqrtXGate,
                            SwapGate,
                        ),
                    )
                    or gate in (Sdag, Tdag)
                )
        return False

    def _reset(self):
        """Reset all temporary variables (after flush gate)."""
        self._clear = True
        self._measured_ids = []

    def _store(self, cmd):  # pylint: disable=too-many-branches
        """
        Temporarily store the command cmd.

        Translates the command and stores it in a local variable (self._circuit) in JSON format.

        Args:
            cmd: Command to store
        """
        gate = cmd.gate

        # Do not clear the self._clear flag for those gates
        if gate in (Deallocate, Barrier):
            return

        num_controls = get_control_count(cmd)
        gate_type = (
            type(gate) if not isinstance(gate, DaggeredGate) else type(gate._gate)  # pylint: disable=protected-access
        )

        if self._clear:
            self._probabilities = dict()
            self._clear = False
            self._circuit = ""
            self._allocated_qubits = set()

        if gate == Allocate:
            self._allocated_qubits.add(cmd.qubits[0][0].id)
            return
        if gate == Measure:
            qb_id = cmd.qubits[0][0].id
            logical_id = None
            for tag in cmd.tags:
                if isinstance(tag, LogicalQubitIDTag):
                    logical_id = tag.logical_qubit_id
                    break
            self._measured_ids.append(logical_id if logical_id is not None else qb_id)
            return

        # All other supported gate types
        json_cmd = {}

        if num_controls > 1:
            json_cmd['controls'] = [qb.id for qb in cmd.control_qubits]
        elif num_controls == 1:
            json_cmd['control'] = cmd.control_qubits[0].id

        qubits = [qb.id for qureg in cmd.qubits for qb in qureg]
        if len(qubits) > 1:
            json_cmd['targets'] = qubits
        else:
            json_cmd['target'] = qubits[0]

        if isinstance(gate, (R, Rx, Ry, Rz)):
            json_cmd['angle'] = gate.angle

        if isinstance(gate, DaggeredGate):
            json_cmd['type'] = 'c' * num_controls + self._gationary[gate_type] + 'i'
        elif isinstance(gate, (XGate)) and num_controls > 0:
            json_cmd['type'] = 'c' * (num_controls - 1) + 'cnot'
        else:
            json_cmd['type'] = 'c' * num_controls + self._gationary[gate_type]

        self._circuit += json.dumps(json_cmd) + ", "

        # TODO: Add unitary for the SV1 simulator as MatrixGate

    def _logical_to_physical(self, qb_id):
        """
        Return the physical location of the qubit with the given logical id.

        Args:
            qb_id (int): ID of the logical qubit whose position should be
                returned.
        """
        if self.main_engine.mapper is not None:
            mapping = self.main_engine.mapper.current_mapping
            if qb_id not in mapping:
                raise RuntimeError(
                    (
                        "Unknown qubit id {} in current mapping. Please make sure eng.flush() was called and that the"
                        "qubit was eliminated during optimization."
                    ).format(qb_id)
                )
            return mapping[qb_id]
        return qb_id

    def get_probabilities(self, qureg):
        """
        Return the list of basis states with corresponding probabilities.  If input qureg is a subset of the register
        used for the experiment, then returns the projected probabilities over the other states.

        The measured bits are ordered according to the supplied quantum register, i.e., the left-most bit in the
        state-string corresponds to the first qubit in the supplied quantum register.

        Args:
            qureg (list<Qubit>): Quantum register determining the order of the
                qubits.

        Returns:
            probability_dict (dict): Dictionary mapping n-bit strings to
                probabilities.

        Raises:
            RuntimeError: If no data is available (i.e., if the circuit has not
                been executed). Or if a qubit was supplied which was not
                present in the circuit (might have gotten optimized away).

        Warning:
            Only call this function after the circuit has been executed!

            This is maintained in the same form of IBM and AQT for compatibility but in AWSBraket, a previously
            executed circuit will store the results in the S3 bucket and it can be retreived at any point in time
            thereafter.
            No circuit execution should be required at the time of retrieving the results and probabilities if the
            circuit has already been executed.
            In order to obtain the probabilities of a previous job you have to get the TaskArn and remember the qubits
            and ordering used in the original job.

        """
        if len(self._probabilities) == 0:
            raise RuntimeError("Please, run the circuit first!")

        probability_dict = dict()
        for state in self._probabilities:
            mapped_state = ['0'] * len(qureg)
            for i, qubit in enumerate(qureg):
                if self._logical_to_physical(qubit.id) >= len(state):  # pragma: no cover
                    raise IndexError('Physical ID {} > length of internal probabilities array'.format(qubit.id))
                mapped_state[i] = state[self._logical_to_physical(qubit.id)]
            probability = self._probabilities[state]
            mapped_state = "".join(mapped_state)
            if mapped_state not in probability_dict:
                probability_dict[mapped_state] = probability
            else:
                probability_dict[mapped_state] += probability
        return probability_dict

    def _run(self):
        """
        Run the circuit.

        Send the circuit via the AWS Boto3 SDK. Use the provided Access Key and Secret key or ask for them if not
        provided
        """
        # NB: the AWS Braket API does not require explicit measurement commands at the end of a circuit; after running
        # any circuit, all qubits are implicitly measured.  Also, AWS Braket currently does not support intermediate
        # measurements.

        # If the clear flag is set, nothing to do here...
        if self._clear:
            return

        # In Braket the results for the jobs are stored in S3.  You can recover the results from previous jobs using
        # the TaskArn (self._retrieve_execution).
        if self._retrieve_execution is not None:
            res = retrieve(
                credentials=self._credentials,
                task_arn=self._retrieve_execution,
                num_retries=self._num_retries,
                interval=self._interval,
                verbose=self._verbose,
            )
        else:
            # Return if no operations have been added.
            if not self._circuit:
                return

            n_qubit = len(self._allocated_qubits)
            info = {}
            info['circuit'] = self._circuithead + self._circuit.rstrip(', ') + self._circuittail
            info['nq'] = n_qubit
            info['shots'] = self._num_runs
            info['backend'] = {'name': self.device}
            res = send(
                info,
                device=self.device,
                credentials=self._credentials,
                s3_folder=self._s3_folder,
                num_retries=self._num_retries,
                interval=self._interval,
                verbose=self._verbose,
            )

        counts = res

        # Determine random outcome
        random_outcome = random.random()
        p_sum = 0.0
        measured = ""
        for state in counts:
            probability = counts[state]
            p_sum += probability
            star = ""
            if p_sum >= random_outcome and measured == "":
                measured = state
                star = "*"
            self._probabilities[state] = probability
            if self._verbose and probability > 0:
                print(state + " with p = " + str(probability) + star)

        # register measurement result
        for qubit_id in self._measured_ids:
            result = int(measured[self._logical_to_physical(qubit_id)])
            self.main_engine.set_measurement_result(WeakQubitRef(self.main_engine, qubit_id), result)
        self._reset()

    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until completion.

        Args:
            command_list: List of commands to execute
        """
        for cmd in command_list:
            if not isinstance(cmd.gate, FlushGate):
                self._store(cmd)
            else:
                self._run()
                self._reset()
            if not self.is_last_engine:
                self.send([cmd])
