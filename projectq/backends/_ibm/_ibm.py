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
""" Back-end to run quantum program on IBM's Quantum Experience."""
import math
import random

from projectq.cengines import BasicEngine
from projectq.meta import get_control_count, LogicalQubitIDTag, has_negative_control
from projectq.ops import NOT, H, Rx, Ry, Rz, Measure, Allocate, Deallocate, Barrier, FlushGate
from projectq.types import WeakQubitRef

from ._ibm_http_client import send, retrieve


class IBMBackend(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """
    The IBM Backend class, which stores the circuit, transforms it to JSON,
    and sends the circuit through the IBM API.
    """

    def __init__(
        self,
        use_hardware=False,
        num_runs=1024,
        verbose=False,
        token='',
        device='ibmq_essex',
        num_retries=3000,
        interval=1,
        retrieve_execution=None,
    ):  # pylint: disable=too-many-arguments
        """
        Initialize the Backend object.

        Args:
            use_hardware (bool): If True, the code is run on the IBM quantum
                chip (instead of using the IBM simulator)
            num_runs (int): Number of runs to collect statistics.
                (default is 1024)
            verbose (bool): If True, statistics are printed, in addition to
                the measurement result being registered (at the end of the
                circuit).
            token (str): IBM quantum experience user password.
            device (str): name of the IBM device to use. ibmq_essex By default
            num_retries (int): Number of times to retry to obtain
                results from the IBM API. (default is 3000)
            interval (float, int): Number of seconds between successive
                attempts to obtain results from the IBM API.
                (default is 1)
            retrieve_execution (int): Job ID to retrieve instead of re-
                running the circuit (e.g., if previous run timed out).
        """
        super().__init__()
        self._clear = False
        self._reset()
        if use_hardware:
            self.device = device
        else:
            self.device = 'ibmq_qasm_simulator'
        self._num_runs = num_runs
        self._verbose = verbose
        self._token = token
        self._num_retries = num_retries
        self._interval = interval
        self._probabilities = dict()
        self.qasm = ""
        self._json = []
        self._measured_ids = []
        self._allocated_qubits = set()
        self._retrieve_execution = retrieve_execution

    def is_available(self, cmd):
        """
        Return true if the command can be executed.

        The IBM quantum chip can only do U1,U2,U3,barriers, and CX / CNOT.
        Conversion implemented for Rotation gates and H gates.

        Args:
            cmd (Command): Command for which to check availability
        """
        if has_negative_control(cmd):
            return False

        gate = cmd.gate

        if get_control_count(cmd) == 1:
            return gate == NOT
        if get_control_count(cmd) == 0:
            return gate == H or isinstance(gate, (Rx, Ry, Rz)) or gate in (Measure, Allocate, Deallocate, Barrier)
        return False

    def get_qasm(self):
        """Return the QASM representation of the circuit sent to the backend.
        Should be called AFTER calling the ibm device"""
        return self.qasm

    def _reset(self):
        """Reset all temporary variables (after flush gate)."""
        self._clear = True
        self._measured_ids = []

    def _store(self, cmd):  # pylint: disable=too-many-branches,too-many-statements
        """
        Temporarily store the command cmd.

        Translates the command and stores it in a local variable (self._cmds).

        Args:
            cmd: Command to store
        """
        if self.main_engine.mapper is None:
            raise RuntimeError('No mapper is present in the compiler engine list!')

        if self._clear:
            self._probabilities = dict()
            self._clear = False
            self.qasm = ""
            self._json = []
            self._allocated_qubits = set()

        gate = cmd.gate
        if gate == Allocate:
            self._allocated_qubits.add(cmd.qubits[0][0].id)
            return

        if gate == Deallocate:
            return

        if gate == Measure:
            logical_id = None
            for tag in cmd.tags:
                if isinstance(tag, LogicalQubitIDTag):
                    logical_id = tag.logical_qubit_id
                    break
            if logical_id is None:
                raise RuntimeError('No LogicalQubitIDTag found in command!')
            self._measured_ids += [logical_id]
        elif gate == NOT and get_control_count(cmd) == 1:
            ctrl_pos = cmd.control_qubits[0].id
            qb_pos = cmd.qubits[0][0].id
            self.qasm += "\ncx q[{}], q[{}];".format(ctrl_pos, qb_pos)
            self._json.append({'qubits': [ctrl_pos, qb_pos], 'name': 'cx'})
        elif gate == Barrier:
            qb_pos = [qb.id for qr in cmd.qubits for qb in qr]
            self.qasm += "\nbarrier "
            qb_str = ""
            for pos in qb_pos:
                qb_str += "q[{}], ".format(pos)
            self.qasm += qb_str[:-2] + ";"
            self._json.append({'qubits': qb_pos, 'name': 'barrier'})
        elif isinstance(gate, (Rx, Ry, Rz)):
            qb_pos = cmd.qubits[0][0].id
            u_strs = {'Rx': 'u3({}, -pi/2, pi/2)', 'Ry': 'u3({}, 0, 0)', 'Rz': 'u1({})'}
            u_name = {'Rx': 'u3', 'Ry': 'u3', 'Rz': 'u1'}
            u_angle = {
                'Rx': [gate.angle, -math.pi / 2, math.pi / 2],
                'Ry': [gate.angle, 0, 0],
                'Rz': [gate.angle],
            }
            gate_qasm = u_strs[str(gate)[0:2]].format(gate.angle)
            gate_name = u_name[str(gate)[0:2]]
            params = u_angle[str(gate)[0:2]]
            self.qasm += "\n{} q[{}];".format(gate_qasm, qb_pos)
            self._json.append({'qubits': [qb_pos], 'name': gate_name, 'params': params})
        elif gate == H:
            qb_pos = cmd.qubits[0][0].id
            self.qasm += "\nu2(0,pi/2) q[{}];".format(qb_pos)
            self._json.append({'qubits': [qb_pos], 'name': 'u2', 'params': [0, 3.141592653589793]})
        else:
            raise Exception('Command not authorized. You should run the circuit with the appropriate ibm setup.')

    def _logical_to_physical(self, qb_id):
        """
        Return the physical location of the qubit with the given logical id.

        Args:
            qb_id (int): ID of the logical qubit whose position should be
                returned.
        """
        mapping = self.main_engine.mapper.current_mapping
        if qb_id not in mapping:
            raise RuntimeError(
                "Unknown qubit id {}. Please make sure "
                "eng.flush() was called and that the qubit "
                "was eliminated during optimization.".format(qb_id)
            )
        return mapping[qb_id]

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
            for i, val in enumerate(qureg):
                mapped_state[i] = state[self._logical_to_physical(val.id)]
            probability = self._probabilities[state]
            mapped_state = "".join(mapped_state)
            if mapped_state not in probability_dict:
                probability_dict[mapped_state] = probability
            else:
                probability_dict[mapped_state] += probability
        return probability_dict

    def _run(self):  # pylint: disable=too-many-locals
        """
        Run the circuit.

        Send the circuit via a non documented IBM API (using JSON written
        circuits) using the provided user data / ask for the user token.
        """
        # finally: add measurements (no intermediate measurements are allowed)
        for measured_id in self._measured_ids:
            qb_loc = self.main_engine.mapper.current_mapping[measured_id]
            self.qasm += "\nmeasure q[{0}] -> c[{0}];".format(qb_loc)
            self._json.append({'qubits': [qb_loc], 'name': 'measure', 'memory': [qb_loc]})
        # return if no operations / measurements have been performed.
        if self.qasm == "":
            return
        max_qubit_id = max(self._allocated_qubits) + 1
        info = {}
        info['json'] = self._json
        info['nq'] = max_qubit_id

        info['shots'] = self._num_runs
        info['maxCredits'] = 10
        info['backend'] = {'name': self.device}
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
            counts = res['data']['counts']
            # Determine random outcome
            random_outcome = random.random()
            p_sum = 0.0
            measured = ""
            for state in counts:
                probability = counts[state] * 1.0 / self._num_runs
                state = "{0:b}".format(int(state, 0))
                state = state.zfill(max_qubit_id)
                # states in ibmq are right-ordered, so need to reverse state string
                state = state[::-1]
                p_sum += probability
                star = ""
                if p_sum >= random_outcome and measured == "":
                    measured = state
                    star = "*"
                self._probabilities[state] = probability
                if self._verbose and probability > 0:
                    print(str(state) + " with p = " + str(probability) + star)

            # register measurement result from IBM
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
        IBM QE API.

        Args:
            command_list: List of commands to execute
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._store(cmd)
            else:
                self._run()
                self._reset()
