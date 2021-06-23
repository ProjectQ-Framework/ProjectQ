# -*- coding: utf-8 -*-
#   Copyright 2020, 2021 ProjectQ-Framework (www.projectq.ch)
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
""" Back-end to run quantum program on AQT's API."""

import math
import random

from projectq.cengines import BasicEngine
from projectq.meta import get_control_count, LogicalQubitIDTag
from projectq.ops import Rx, Ry, Rxx, Measure, Allocate, Barrier, Deallocate, FlushGate
from projectq.types import WeakQubitRef

from ._aqt_http_client import send, retrieve


# _rearrange_result & _format_counts imported and modified from qiskit
def _rearrange_result(input_result, length):
    bin_input = list(bin(input_result)[2:].rjust(length, '0'))
    return ''.join(bin_input)[::-1]


def _format_counts(samples, length):
    counts = {}
    for result in samples:
        h_result = _rearrange_result(result, length)
        if h_result not in counts:
            counts[h_result] = 1
        else:
            counts[h_result] += 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


class AQTBackend(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """
    The AQT Backend class, which stores the circuit, transforms it to the
    appropriate data format, and sends the circuit through the AQT API.
    """

    def __init__(
        self,
        use_hardware=False,
        num_runs=100,
        verbose=False,
        token='',
        device='simulator',
        num_retries=3000,
        interval=1,
        retrieve_execution=None,
    ):  # pylint: disable=too-many-arguments
        """
        Initialize the Backend object.

        Args:
            use_hardware (bool): If True, the code is run on the AQT quantum
                chip (instead of using the AQT simulator)
            num_runs (int): Number of runs to collect statistics.
                (default is 100, max is usually around 200)
            verbose (bool): If True, statistics are printed, in addition to
                the measurement result being registered (at the end of the
                circuit).
            token (str): AQT user API token.
            device (str): name of the AQT device to use. simulator By default
            num_retries (int): Number of times to retry to obtain
                results from the AQT API. (default is 3000)
            interval (float, int): Number of seconds between successive
                attempts to obtain results from the AQT API.
                (default is 1)
            retrieve_execution (int): Job ID to retrieve instead of re-
                running the circuit (e.g., if previous run timed out).
        """
        BasicEngine.__init__(self)
        self._reset()
        if use_hardware:
            self.device = device
        else:
            self.device = 'simulator'
        self._clear = True
        self._num_runs = num_runs
        self._verbose = verbose
        self._token = token
        self._num_retries = num_retries
        self._interval = interval
        self._probabilities = dict()
        self._circuit = []
        self._mapper = []
        self._measured_ids = []
        self._allocated_qubits = set()
        self._retrieve_execution = retrieve_execution

    def is_available(self, cmd):
        """
        Return true if the command can be executed.

        The AQT ion trap can only do Rx,Ry and Rxx.

        Args:
            cmd (Command): Command for which to check availability
        """
        if get_control_count(cmd) == 0:
            if isinstance(cmd.gate, (Rx, Ry, Rxx)):
                return True
        if cmd.gate in (Measure, Allocate, Deallocate, Barrier):
            return True
        return False

    def _reset(self):
        """Reset all temporary variables (after flush gate)."""
        self._clear = True
        self._measured_ids = []

    def _store(self, cmd):
        """
        Temporarily store the command cmd.

        Translates the command and stores it in a local variable (self._cmds).

        Args:
            cmd: Command to store
        """
        if self._clear:
            self._probabilities = dict()
            self._clear = False
            self._circuit = []
            self._allocated_qubits = set()

        gate = cmd.gate
        if gate == Allocate:
            self._allocated_qubits.add(cmd.qubits[0][0].id)
            return
        if gate == Deallocate:
            return
        if gate == Measure:
            qb_id = cmd.qubits[0][0].id
            logical_id = None
            for tag in cmd.tags:
                if isinstance(tag, LogicalQubitIDTag):
                    logical_id = tag.logical_qubit_id
                    break
            if logical_id is None:
                logical_id = qb_id
                self._mapper.append(qb_id)
            self._measured_ids += [logical_id]
            return
        if isinstance(gate, (Rx, Ry, Rxx)):
            qubits = []
            qubits.append(cmd.qubits[0][0].id)
            if len(cmd.qubits) == 2:
                qubits.append(cmd.qubits[1][0].id)
            angle = gate.angle / math.pi
            instruction = []
            u_name = {'Rx': "X", 'Ry': "Y", 'Rxx': "MS"}
            instruction.append(u_name[str(gate)[0 : int(len(cmd.qubits) + 1)]])  # noqa: E203
            instruction.append(round(angle, 2))
            instruction.append(qubits)
            self._circuit.append(instruction)
            return
        if gate == Barrier:
            return
        raise Exception('Invalid command: ' + str(cmd))

    def _logical_to_physical(self, qb_id):
        """
        Return the physical location of the qubit with the given logical id.
        If no mapper is present then simply returns the qubit ID.

        Args:
            qb_id (int): ID of the logical qubit whose position should be
                returned.
        """
        try:
            mapping = self.main_engine.mapper.current_mapping
            if qb_id not in mapping:
                raise RuntimeError(
                    "Unknown qubit id {}. Please make sure "
                    "eng.flush() was called and that the qubit "
                    "was eliminated during optimization.".format(qb_id)
                )
            return mapping[qb_id]
        except AttributeError as err:
            if qb_id not in self._mapper:
                raise RuntimeError(
                    "Unknown qubit id {}. Please make sure "
                    "eng.flush() was called and that the qubit "
                    "was eliminated during optimization.".format(qb_id)
                ) from err
            return qb_id

    def get_probabilities(self, qureg):
        """
        Return the list of basis states with corresponding probabilities.
        If input qureg is a subset of the register used for the experiment,
        then returns the projected probabilities over the other states.
        The measured bits are ordered according to the supplied quantum
        register, i.e., the left-most bit in the state-string corresponds to
        the first qubit in the supplied quantum register.
        Warning:
            Only call this function after the circuit has been executed!
        Args:
            qureg (list<Qubit>): Quantum register determining the order of the
                qubits.
        Returns:
            probability_dict (dict): Dictionary mapping n-bit strings to
            probabilities.
        Raises:
            RuntimeError: If no data is available (i.e., if the circuit has
                not been executed). Or if a qubit was supplied which was not
                present in the circuit (might have gotten optimized away).
        """
        if len(self._probabilities) == 0:
            raise RuntimeError("Please, run the circuit first!")

        probability_dict = dict()
        for state in self._probabilities:
            mapped_state = ['0'] * len(qureg)
            for i, qubit in enumerate(qureg):
                mapped_state[i] = state[self._logical_to_physical(qubit.id)]
            probability = self._probabilities[state]
            mapped_state = "".join(mapped_state)

            probability_dict[mapped_state] = probability_dict.get(mapped_state, 0) + probability
        return probability_dict

    def _run(self):
        """
        Run the circuit.

        Send the circuit via the AQT API using the provided user
        token / ask for the user token.
        """
        # finally: measurements
        # NOTE AQT DOESN'T SEEM TO HAVE MEASUREMENT INSTRUCTIONS (no
        # intermediate measurements are allowed, so implicit at the end)
        # return if no operations.
        if self._circuit == []:
            return

        n_qubit = max(self._allocated_qubits) + 1
        info = {}
        # Hack: AQT instructions specifically need "GATE" string representation
        # instead of 'GATE'
        info['circuit'] = str(self._circuit).replace("'", '"')
        info['nq'] = n_qubit
        info['shots'] = self._num_runs
        info['backend'] = {'name': self.device}
        if self._num_runs > 200:
            raise Exception("Number of shots limited to 200")
        try:
            if self._retrieve_execution is None:
                res = send(
                    info,
                    device=self.device,
                    token=self._token,
                    num_retries=self._num_retries,
                    interval=self._interval,
                    verbose=self._verbose,
                )
            else:
                res = retrieve(
                    device=self.device,
                    token=self._token,
                    jobid=self._retrieve_execution,
                    num_retries=self._num_retries,
                    interval=self._interval,
                    verbose=self._verbose,
                )
            self._num_runs = len(res)
            counts = _format_counts(res, n_qubit)
            # Determine random outcome
            random_outcome = random.random()
            p_sum = 0.0
            measured = ""
            for state in counts:
                probability = counts[state] * 1.0 / self._num_runs
                p_sum += probability
                star = ""
                if p_sum >= random_outcome and measured == "":
                    measured = state
                    star = "*"
                self._probabilities[state] = probability
                if self._verbose and probability > 0:
                    print(str(state) + " with p = " + str(probability) + star)

            # register measurement result from AQT
            for qubit_id in self._measured_ids:
                location = self._logical_to_physical(qubit_id)
                result = int(measured[location])
                self.main_engine.set_measurement_result(WeakQubitRef(self, qubit_id), result)
            self._reset()
        except TypeError as err:
            raise Exception("Failed to run the circuit. Aborting.") from err

    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until completion. Upon flush, send the data to the
        AQT API.

        Args:
            command_list: List of commands to execute
        """
        for cmd in command_list:
            if not isinstance(cmd.gate, FlushGate):
                self._store(cmd)
            else:
                self._run()
                self._reset()
