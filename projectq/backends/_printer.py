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

"""
Contains a compiler engine which prints commands to stdout prior to sending
them on to the next engines (see CommandPrinter).
"""
import sys

from builtins import input

from projectq.cengines import LastEngineException, BasicEngine
from projectq.ops import FlushGate, Measure
from projectq.meta import get_control_count


class CommandPrinter(BasicEngine):
    """
    CommandPrinter is a compiler engine which prints commands to stdout prior
    to sending them on to the next compiler engine.
    """
    def __init__(self, accept_input=True, default_measure=False,
                 in_place=False):
        """
        Initialize a CommandPrinter.

        Args:
            accept_input (bool): If accept_input is true, the printer queries
                the user to input measurement results if the CommandPrinter is
                the last engine. Otherwise, all measurements yield
                default_measure.
            default_measure (bool): Default measurement result (if
                accept_input is False).
            in_place (bool): If in_place is true, all output is written on the
                same line of the terminal.
        """
        BasicEngine.__init__(self)
        self._accept_input = accept_input
        self._default_measure = default_measure
        self._in_place = in_place

    def is_available(self, cmd):
        """
        Specialized implementation of is_available: Returns True if the
        CommandPrinter is the last engine (since it can print any command).

        Args:
            cmd (Command): Command of which to check availability (all
                Commands can be printed).
        Returns:
            availability (bool): True, unless the next engine cannot handle
                the Command (if there is a next engine).
        """
        try:
            return BasicEngine.is_available(self, cmd)
        except LastEngineException:
            return True

    def _print_cmd(self, cmd):
        """
        Print a command or, if the command is a measurement instruction and
        the CommandPrinter is the last engine in the engine pipeline: Query
        the user for the measurement result (if accept_input = True) / Set
        the result to 0 (if it's False).

        Args:
            cmd (Command): Command to print.
        """
        if self.is_last_engine and cmd.gate == Measure:
            assert(get_control_count(cmd) == 0)
            print(cmd)
            for qureg in cmd.qubits:
                for qubit in qureg:
                    if self._accept_input:
                        m = None
                        while m != '0' and m != '1' and m != 1 and m != 0:
                            prompt = ("Input measurement result (0 or 1) for"
                                      " qubit " + str(qubit) + ": ")
                            m = input(prompt)
                    else:
                        m = self._default_measure
                    m = int(m)
                    self.main_engine.set_measurement_result(qubit, m)
        else:
            if self._in_place:
                sys.stdout.write("\0\r\t\x1b[K" + str(cmd) + "\r")
            else:
                print(cmd)

    def receive(self, command_list):
        """
        Receive a list of commands from the previous engine, print the
        commands, and then send them on to the next engine.

        Args:
            command_list (list<Command>): List of Commands to print (and
                potentially send on to the next engine).
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._print_cmd(cmd)
            # (try to) send on
            if not self.is_last_engine:
                self.send([cmd])


class CommandLister(CommandPrinter):
    """
    CommandLister is a minor modification of CommandPrinter which stores the
    commands in a list rather than outputting to stdout, which can be more
    convenient in interactive/notebook environments. By creating this object
    and passing it as the backend, we can later access the list of commands
    by using CommandLister.cmd_list.
    """
    def __init__(self, accept_input=True, default_measure=False,
                 in_place=False):
        """
        Initialize a CommandLister.
        Args:
            accept_input (bool): If accept_input is true, the printer queries
                the user to input measurement results if the CommandPrinter is
                the last engine. Otherwise, all measurements yield
                default_measure.
            default_measure (bool): Default measurement result (if
                accept_input is False).
            in_place (bool): If in_place is true, all output is written on the
                same line of the terminal.
        """
        CommandPrinter.__init__(self, accept_input,default_measure, in_place)

        #Initialize an empty list which we will fill with commands
        self.cmd_list = [] 
    
    def _print_cmd(self, cmd):
        """
        Store a command or, if the command is a measurement instruction and
        the CommandStorer is the last engine in the engine pipeline: Query
        the user for the measurement result (if accept_input = True) / Set
        the result to 0 (if it's False).
        Args:
            cmd (Command): Command to print.
        """
        if self.is_last_engine and cmd.gate == Measure:
            assert(get_control_count(cmd) == 0)
            self.cmd_list.append(str(cmd))
            for qureg in cmd.qubits:
                for qubit in qureg:
                    if self._accept_input:
                        m = None
                        while m != '0' and m != '1' and m != 1 and m != 0:
                            prompt = ("Input measurement result (0 or 1) for"
                                      " qubit " + str(qubit) + ": ")
                            m = input(prompt)
                    else:
                        m = self._default_measure
                    m = int(m)
                    self.main_engine.set_measurement_result(qubit, m)
        else:
            if self._in_place:
                self.cmd_list.append("\0\r\t\x1b[K" + str(cmd) + "\r")
            else:
                self.cmd_list.append(str(cmd))
