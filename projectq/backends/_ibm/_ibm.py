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

from projectq.cengines import BasicEngine
from projectq.meta import get_control_count
from projectq.ops import (NOT,
                          Y,
                          Z,
                          T,
                          Tdag,
                          S,
                          Sdag,
                          H,
                          Measure,
                          Allocate,
                          Deallocate,
                          FlushGate)

from ._ibm_http_client import send


class _IBMGateCommand:
    """
    IBM gate command wrapper: Stores gate, qubit, and control qubit (for cx
    gates only).
    """
    def __init__(self, gate_str, qubit_id, ctrl_id=None):
        self.gate = gate_str
        self.qubit = qubit_id
        self.ctrl = ctrl_id


class IBMBackend(BasicEngine):
    """
    The IBM Backend class, which stores the circuit, transforms it to JSON
    QASM, and sends the circuit through the IBM API.
    """
    def __init__(self, use_hardware=False, num_runs=1024, verbose=False,
                 user=None, password=None):
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
        """
        BasicEngine.__init__(self)
        self._reset()
        if use_hardware:
            self._device = 'real'
        else:
            self._device = 'sim_trivial_2'
        self._num_runs = num_runs
        self._verbose = verbose
        self._user = user
        self._password = password
        self._mapping = dict()
        self._inverse_mapping = dict()
        self._mapped_qubits = 0
        self._probabilities = dict()

    def is_available(self, cmd):
        """
        Return true if the command can be executed.

        The IBM quantum chip can do X, Y, Z, T, Tdag, S, Sdag, and CX / CNOT.

        Args:
            cmd (Command): Command for which to check availability
        """
        g = cmd.gate
        if g == NOT and get_control_count(cmd) <= 1:
            return True
        if get_control_count(cmd) == 0:
            if (g == T or g == Tdag or g == S or g == Sdag or g == H or g == Y
               or g == Z):
                return True
        if g == Measure or g == Allocate or g == Deallocate:
            return True
        return False

    def _reset(self):
        """ Reset all temporary variables (after flush gate). """
        self._num_cols = 40  # number of gates / columns in the circuit
        self._num_qubits = 5  # number of lines
        self._cmds = []
        for _ in range(self._num_qubits):
            self._cmds.append([""] * self._num_cols)
        self._positions = [0] * self._num_qubits
        self._mapped_qubits = 0

    def _store(self, cmd):
        """
        Temporarily store the command cmd.

        Translates the command and stores it in a local variable (self._cmds).

        Args:
            cmd: Command to store
        """
        gate = cmd.gate
        if gate == Allocate or gate == Deallocate:
            return

        if self._mapped_qubits == 0:
            self._mapping = dict()
            self._inverse_mapping = dict()
            self._probabilities = dict()

        for qr in cmd.qubits:
            for qb in qr:
                if not qb.id in self._mapping:
                    self._mapping[qb.id] = self._mapped_qubits
                    self._inverse_mapping[self._mapped_qubits] = qb.id
                    self._mapped_qubits += 1
        for qb in cmd.control_qubits:
            if not qb.id in self._mapping:
                self._mapping[qb.id] = self._mapped_qubits
                self._inverse_mapping[self._mapped_qubits] = qb.id
                self._mapped_qubits += 1

        if gate == Measure:
            for qr in cmd.qubits:
                for qb in qr:
                    qb_pos = self._mapping[qb.id]
                    meas = _IBMGateCommand("measure", qb_pos)
                    self._cmds[qb_pos][self._positions[qb_pos]] = meas
                    self._positions[qb_pos] += 1

        elif not (gate == NOT and get_control_count(cmd) == 1):
            cls = gate.__class__.__name__
            if cls in self._gate_names:
                gate_str = self._gate_names[cls]
            else:
                gate_str = str(gate).lower()

            qb_pos = self._mapping[cmd.qubits[0][0].id]
            ibm_cmd = _IBMGateCommand(gate_str, qb_pos)
            self._cmds[qb_pos][self._positions[qb_pos]] = ibm_cmd
            self._positions[qb_pos] += 1
        else:
            ctrl_pos = self._mapping[cmd.control_qubits[0].id]
            qb_pos = self._mapping[cmd.qubits[0][0].id]
            pos = max(self._positions[qb_pos], self._positions[ctrl_pos])
            self._positions[qb_pos] = pos
            self._positions[ctrl_pos] = pos
            ibm_cmd = _IBMGateCommand("cx", qb_pos, ctrl_pos)
            self._cmds[qb_pos][self._positions[qb_pos]] = ibm_cmd
            self._positions[qb_pos] += 1
            self._positions[ctrl_pos] += 1

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
            Exception: If no data is available (i.e., if the circuit has not
                been executed).
        """
        if len(self._probabilities) == 0:
            raise RuntimeError("Please, run the circuit first!")

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
        lines = []
        num_gates = 0
        num_cols = min(max(self._positions), self._num_cols)

        cnot_qubit_id = 2

        if num_cols > 0:
            for i in range(self._num_qubits):
                gates = []
                for j in range(num_cols):
                    cmd = self._cmds[i][j]
                    gate = dict()
                    gate['position'] = j
                    try:
                        gate['name'] = cmd.gate
                        gate['qasm'] = cmd.gate
                        if not cmd.ctrl is None:
                            gate['to'] = cmd.ctrl
                            cnot_qubit_id = i
                    except AttributeError:
                        pass
                    gates.append(gate)
                    num_gates += 1

                lines.append(dict())
                lines[i]['line'] = i
                lines[i]['name'] = 'q'
                lines[i]['gates'] = gates

                self._cmds[i] = []
                self._positions[i] = 0

            for gate in lines[cnot_qubit_id]['gates']:
                try:
                    if gate['to'] == 2:
                        gate['to'] = cnot_qubit_id
                except KeyError:
                    pass

            lines[2], lines[cnot_qubit_id] = lines[cnot_qubit_id], lines[2]
            # save this id, so we can later register the measurement result
            # correctly
            self._cnot_qubit_id = cnot_qubit_id

            info = dict()
            info['playground'] = lines
            info['numberColumns'] = num_cols
            info['numberLines'] = self._num_qubits
            info['numberGates'] = num_gates
            info['hasMeasures'] = True
            info['topology'] = '250e969c6b9e68aa2a045ffbceb3ac33'

            info = '{"playground":['
            for i in range(len(lines)):
                info += '{"line":' + str(i) + ',"name":"q","gates":['
                gates = ""
                for j in range(len(lines[i]['gates'])):
                    try:
                        name = lines[i]['gates'][j]['name']
                        qasm = lines[i]['gates'][j]['qasm']
                        gates += '{"position":' + str(j)
                        gates += ',"name":"' + name + '"'
                        gates += ',"qasm":"' + qasm + '"'
                        if name == "cx":
                            gates += ',"to":' + str(lines[i]['gates'][j]['to'])
                        gates += '},'
                    except:
                        pass
                info = info + gates[:-1] + ']},'

            info = (info[:-1]
                    + '],"numberColumns":' + str(40) + ',"numberLines":'
                    + str(self._num_qubits) + ',"numberGates":' + str(200)
                    + ',"hasMeasures":true,"topology":'
                    + '"250e969c6b9e68aa2a045ffbceb3ac33"}')

            try:
                res = send(info, 'projectq_experiment', device=self._device,
                           user=self._user, password=self._password,
                           shots=self._num_runs, verbose=self._verbose)

                data = res['data']['p']

                # Determine random outcome
                P = random.random()
                p_sum = 0.
                measured = ""
                for state, probability in zip(data['labels'], data['values']):
                    state = list(reversed(state))
                    ids_to_swap = state[self._cnot_qubit_id], state[2]
                    state[2], state[self._cnot_qubit_id] = ids_to_swap
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
    _gate_names = {Tdag.__class__.__name__: "tdg",
                   Sdag.__class__.__name__: "sdg"}
