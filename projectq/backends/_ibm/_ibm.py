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

import random
import json

from projectq.cengines import BasicEngine
from projectq.meta import get_control_count, QubitPlacementTag
from projectq.ops import (NOT,
                          Y,
                          Z,
                          T,
                          Tdag,
                          S,
                          Sdag,
                          H,
                          Rx,
                          Ry,
                          Rz,
                          Measure,
                          Allocate,
                          Deallocate,
                          Barrier,
                          FlushGate)

from ._ibm_http_client import send


class IBMBackend(BasicEngine):
    """
    The IBM Backend class, which stores the circuit, transforms it to JSON
    QASM, and sends the circuit through the IBM API.
    """
    def __init__(self, use_hardware=False, num_runs=1024, verbose=False,
                 user=None, password=None, device='ibmqx2'):
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
            user (string): IBM Quantum Experience user name
            password (string): IBM Quantum Experience password
            device (string): Device to use ('ibmqx2', 'ibmqx4', or 'ibmqx5')
                if use_hardware is set to True. Default is ibmqx2.
        """
        BasicEngine.__init__(self)
        self._reset()
        if use_hardware:
            self.device = device
        else:
            self.device = 'simulator'
        self._num_runs = num_runs
        self._verbose = verbose
        self._user = user
        self._password = password
        self._mapping = dict()
        self._inverse_mapping = dict()
        self._probabilities = dict()
        self.qasm = ""

    def is_available(self, cmd):
        """
        Return true if the command can be executed.

        The IBM quantum chip can do X, Y, Z, T, Tdag, S, Sdag,
        rotation gates, barriers, and CX / CNOT.

        Args:
            cmd (Command): Command for which to check availability
        """
        g = cmd.gate
        if g == NOT and get_control_count(cmd) <= 1:
            return True
        if get_control_count(cmd) == 0:
            if g in (T, Tdag, S, Sdag, H, Y, Z):
                return True
            if isinstance(g, (Rx, Ry, Rz)):
                return True
        if g in (Measure, Allocate, Deallocate, Barrier):
            return True
        return False

    def _reset(self):
        """ Reset all temporary variables (after flush gate). """
        self._clear = True

    def _store(self, cmd):
        """
        Temporarily store the command cmd.

        Translates the command and stores it in a local variable (self._cmds).

        Args:
            cmd: Command to store
        """
        if self._clear:
            self._mapping = dict()
            self._inverse_mapping = dict()
            self._probabilities = dict()
            self._clear = False
            self.qasm = ""

        gate = cmd.gate
        if gate == Allocate:
            qb_id = cmd.qubits[0][0].id
            for tag in cmd.tags:
                if isinstance(tag, QubitPlacementTag):
                    self._mapping[qb_id] = tag.position
                    self._inverse_mapping[tag.position] = qb_id
                    break
            if qb_id not in self._mapping:
                raise Exception("No qubit placement info found in Allocate.\n"
                                "Please make sure you are using the IBM CNOT "
                                "Mapper.")
            return

        if gate == Deallocate:
            return

        if gate == Measure:
            for qr in cmd.qubits:
                for qb in qr:
                    qb_pos = self._mapping[qb.id]
                    self.qasm += "\nmeasure q[{}] -> c[{}];".format(qb_pos,
                                                                    qb_pos)

        elif gate == NOT and get_control_count(cmd) == 1:
            ctrl_pos = self._mapping[cmd.control_qubits[0].id]
            qb_pos = self._mapping[cmd.qubits[0][0].id]
            self.qasm += "\ncx q[{}], q[{}];".format(ctrl_pos, qb_pos)
        elif gate == Barrier:
            qb_pos = [self._mapping[qb.id] for qr in cmd.qubits for qb in qr]
            self.qasm += "\nbarrier "
            qb_str = ""
            for pos in qb_pos:
                qb_str += "q[{}], ".format(pos)
            self.qasm += qb_str[:-2] + ";"
        elif isinstance(gate, (Rx, Ry, Rz)):
            assert get_control_count(cmd) == 0
            qb_pos = self._mapping[cmd.qubits[0][0].id]
            u_strs = {'Rx': 'u3({}, -pi/2, pi/2)', 'Ry': 'u3({}, 0, 0)',
                      'Rz': 'u1({})'}
            gate = u_strs[str(gate)[0:2]].format(gate.angle)
            self.qasm += "\n{} q[{}];".format(gate, qb_pos)
        else:
            assert get_control_count(cmd) == 0
            if str(gate) in self._gate_names:
                gate_str = self._gate_names[str(gate)]
            else:
                gate_str = str(gate).lower()

            qb_pos = self._mapping[cmd.qubits[0][0].id]
            self.qasm += "\n{} q[{}];".format(gate_str, qb_pos)

    def get_probabilities(self, qureg):
        """
        Return the list of basis states with corresponding probabilities.

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
        if any(qb.id not in self._mapping for qb in qureg):
            raise RuntimeError("Unknown qubit. Please, make sure that all "
                               "provided qubits are present in the circuit.")

        probability_dict = dict()

        for state in self._probabilities:
            mapped_state = ['0'] * len(qureg)
            for i in range(len(qureg)):
                mapped_state[i] = state[self._mapping[qureg[i].id]]
            probability = self._probabilities[state]
            probability_dict["".join(mapped_state)] = probability

        return probability_dict

    def _run(self):
        """
        Run the circuit.

        Send the circuit via the IBM API (JSON QASM) using the provided user
        data / ask for username & password.
        """
        if self.qasm == "":
            return
        num_qubits = max(self._mapping.values()) + 1
        qasm = ("\ninclude \"qelib1.inc\";\nqreg q[{nq}];\ncreg c[{nq}];" +
                self.qasm).format(nq=num_qubits)
        info = {}
        info['qasms'] = [{'qasm': qasm}]
        info['shots'] = self._num_runs
        info['maxCredits'] = 5
        info['backend'] = {'name': self.device}
        info = json.dumps(info)

        try:
            res = send(info, device=self.device,
                       user=self._user, password=self._password,
                       shots=self._num_runs, verbose=self._verbose)

            counts = res['data']['counts']
            # Determine random outcome
            P = random.random()
            p_sum = 0.
            measured = ""
            for state in counts:
                probability = counts[state] * 1. / self._num_runs
                state = list(reversed(state))
                state = "".join(state)
                p_sum += probability
                star = ""
                if p_sum >= P and measured == "":
                    measured = state
                    star = "*"
                self._probabilities[state] = probability
                if self._verbose and probability > 0:
                    print(str(state) + " with p = " + str(probability) +
                          star)

            class QB():
                def __init__(self, ID):
                    self.id = ID

            # register measurement result
            for ID in self._mapping:
                location = self._mapping[ID]
                result = int(measured[location])
                self.main_engine.set_measurement_result(QB(ID), result)
            self._reset()
        except TypeError:
            raise Exception("Failed to run the circuit. Aborting.")

    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until
        completion.

        Args:
            command_list: List of commands to execute
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._store(cmd)
            else:
                self._run()
                self._reset()

    """
    Mapping of gate names from our gate objects to the IBM QASM representation.
    """
    _gate_names = {str(Tdag): "tdg",
                   str(Sdag): "sdg"}
