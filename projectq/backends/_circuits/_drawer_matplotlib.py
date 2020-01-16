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

from projectq.cengines import LastEngineException, BasicEngine
from projectq.ops import (SwapGate, FlushGate, Measure, Allocate, Deallocate)
from projectq.meta import get_control_count
from projectq.backends._circuits import to_draw


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
        self._gates = []

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
            # General multi-target qubit gates are not supported yet
            if (not isinstance(cmd.gate, SwapGate)
                    and len([qubit for qureg in cmd.qubits
                             for qubit in qureg]) > 1):
                return False
            return BasicEngine.is_available(self, cmd)
        except LastEngineException:
            return True

    def receive(self, command_list):
        """
        Receive a list of commands from the previous engine, print the
        commands, and then send them on to the next engine.

        Args:
            command_list (list<Command>): List of Commands to print (and
                potentially send on to the next engine).
        """

        for cmd in command_list:
            # split the gate string "Gate()" at '(' get the gate name
            gate_name = str(cmd.gate).split('(')[0]
            # case for R(1.57094543) Gate
            if hasattr(cmd.gate, 'angle'):
                gate_name = gate_name + '({0:.2f})'.format(cmd.gate.angle)

            if (cmd.gate not in [Allocate, Deallocate]
                    and not isinstance(cmd.gate, FlushGate)):
                targets = tuple(qubit.id for qureg in cmd.qubits
                                for qubit in qureg)

                if len(cmd.control_qubits) > 0:
                    self._gates.append(
                        (gate_name, targets,
                         tuple(qubit.id for qubit in cmd.control_qubits)))
                else:
                    self._gates.append((gate_name, targets))

            if cmd.gate == Allocate:
                qubit_id = cmd.qubits[0][0].id
                if qubit_id not in self._map:
                    self._map[qubit_id] = qubit_id

            elif self.is_last_engine and cmd.gate == Measure:
                assert get_control_count(cmd) == 0
                for qureg in cmd.qubits:
                    for qubit in qureg:
                        if self._accept_input:
                            m = None
                            while m not in ('0', '1', 1, 0):
                                prompt = ('Input measurement result (0 or 1) '
                                          'for qubit ' + str(qubit) + ': ')
                                m = input(prompt)
                        else:
                            m = self._default_measure
                        m = int(m)
                        self.main_engine.set_measurement_result(qubit, m)

            # (try to) send on
            if not self.is_last_engine:
                self.send([cmd])

    def draw(self):
        """
        Returns the plot of the quantum circuit
        """
        qubits = [self._map[id] for id in self._map]
        # extract all the allocated qubits from the circuit

        return to_draw(self._gates, qubits)
