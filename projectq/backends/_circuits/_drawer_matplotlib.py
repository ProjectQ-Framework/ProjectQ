#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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
Contains a compiler engine which generates matplotlib figures describing the
circuit.
"""

from builtins import input
import re
import itertools

from projectq.cengines import LastEngineException, BasicEngine
from projectq.ops import (FlushGate, Measure, Allocate, Deallocate)
from projectq.meta import get_control_count
from projectq.backends._circuits import to_draw

# ==============================================================================


def _format_gate_str(cmd):
    param_str = ''
    gate_name = str(cmd.gate)
    if '(' in gate_name:
        (gate_name, param_str) = re.search(r'(.+)\((.*)\)', gate_name).groups()
        params = re.findall(r'([^,]+)', param_str)
        params_str_list = []
        for param in params:
            try:
                params_str_list.append('{0:.2f}'.format(float(param)))
            except ValueError:
                if len(param) < 8:
                    params_str_list.append(param)
                else:
                    params_str_list.append(param[:5] + '...')

        gate_name += '(' + ','.join(params_str_list) + ')'
    return gate_name


# ==============================================================================


class CircuitDrawerMatplotlib(BasicEngine):
    """
    CircuitDrawerMatplotlib is a compiler engine which using Matplotlib library
    for drawing quantum circuits
    """
    def __init__(self, accept_input=False, default_measure=0):
        """
        Initialize a circuit drawing engine(mpl)
        Args:
            accept_input (bool): If accept_input is true, the printer queries
                the user to input measurement results if the CircuitDrawerMPL
                is the last engine. Otherwise, all measurements yield the
                result default_measure (0 or 1).
            default_measure (bool): Default value to use as measurement
                results if accept_input is False and there is no underlying
                backend to register real measurement results.
        """
        BasicEngine.__init__(self)
        self._accept_input = accept_input
        self._default_measure = default_measure
        self._map = dict()
        self._qubit_lines = {}

    def is_available(self, cmd):
        """
        Specialized implementation of is_available: Returns True if the
        CircuitDrawerMatplotlib is the last engine
        (since it can print any command).

        Args:
            cmd (Command): Command for which to check availability (all
                Commands can be printed).

        Returns:
            availability (bool): True, unless the next engine cannot handle
            the Command (if there is a next engine).
        """
        try:
            # Multi-qubit gates may fail at drawing time if the target qubits
            # are not right next to each other on the output graphic.
            return BasicEngine.is_available(self, cmd)
        except LastEngineException:
            return True

    def _process(self, cmd):
        """
        Process the command cmd and stores it in the internal storage

        Queries the user for measurement input if a measurement command
        arrives if accept_input was set to True. Otherwise, it uses the
        default_measure parameter to register the measurement outcome.

        Args:
            cmd (Command): Command to add to the circuit diagram.
        """
        if cmd.gate == Allocate:
            qubit_id = cmd.qubits[0][0].id
            if qubit_id not in self._map:
                self._map[qubit_id] = qubit_id
            self._qubit_lines[qubit_id] = []
            return

        if cmd.gate == Deallocate:
            return

        if self.is_last_engine and cmd.gate == Measure:
            assert get_control_count(cmd) == 0
            for qureg in cmd.qubits:
                for qubit in qureg:
                    if self._accept_input:
                        measurement = None
                        while measurement not in ('0', '1', 1, 0):
                            prompt = ("Input measurement result (0 or 1) for "
                                      "qubit " + str(qubit) + ": ")
                            measurement = input(prompt)
                    else:
                        measurement = self._default_measure
                    self.main_engine.set_measurement_result(
                        qubit, int(measurement))

        targets = [qubit.id for qureg in cmd.qubits for qubit in qureg]
        controls = [qubit.id for qubit in cmd.control_qubits]

        ref_qubit_id = targets[0]
        gate_str = _format_gate_str(cmd)

        # First find out what is the maximum index that this command might
        # have
        max_depth = max(
            len(self._qubit_lines[qubit_id])
            for qubit_id in itertools.chain(targets, controls))

        # If we have a multi-qubit gate, make sure that all the qubit axes
        # have the same depth. We do that by recalculating the maximum index
        # over all the known qubit axes.
        # This is to avoid the possibility of a multi-qubit gate overlapping
        # with some other gates. This could potentially be improved by only
        # considering the qubit axes that are between the topmost and
        # bottommost qubit axes of the current command.
        if len(targets) + len(controls) > 1:
            max_depth = max(
                len(self._qubit_lines[qubit_id])
                for qubit_id in self._qubit_lines)

        for qubit_id in itertools.chain(targets, controls):
            depth = len(self._qubit_lines[qubit_id])
            self._qubit_lines[qubit_id] += [None] * (max_depth - depth)

            if qubit_id == ref_qubit_id:
                self._qubit_lines[qubit_id].append(
                    (gate_str, targets, controls))
            else:
                self._qubit_lines[qubit_id].append(None)

    def receive(self, command_list):
        """
        Receive a list of commands from the previous engine, print the
        commands, and then send them on to the next engine.

        Args:
            command_list (list<Command>): List of Commands to print (and
                potentially send on to the next engine).
        """
        for cmd in command_list:
            if not isinstance(cmd.gate, FlushGate):
                self._process(cmd)

            if not self.is_last_engine:
                self.send([cmd])

    def draw(self, qubit_labels=None, drawing_order=None):
        """
        Generates and returns the plot of the quantum circuit stored so far

        Args:
            qubit_labels (dict): label for each wire in the output figure.
                Keys: qubit IDs, Values: string to print out as label for
                that particular qubit wire.
            drawing_order (dict): position of each qubit in the output
                graphic. Keys: qubit IDs, Values: position of qubit on the
                qubit line in the graphic.

        Returns:
            A tuple containing the matplotlib figure and axes objects
        """
        max_depth = max(
            len(self._qubit_lines[qubit_id]) for qubit_id in self._qubit_lines)
        for qubit_id in self._qubit_lines:
            depth = len(self._qubit_lines[qubit_id])
            if depth < max_depth:
                self._qubit_lines[qubit_id] += [None] * (max_depth - depth)

        return to_draw(self._qubit_lines,
                       qubit_labels=qubit_labels,
                       drawing_order=drawing_order)
