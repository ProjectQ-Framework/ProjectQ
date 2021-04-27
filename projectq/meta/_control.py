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
"""
Contains the tools to make an entire section of operations controlled.

Example:
    .. code-block:: python

        with Control(eng, qubit1):
            H | qubit2
            X | qubit3
"""

from projectq.cengines import BasicEngine
from projectq.meta import ComputeTag, UncomputeTag, Compute, Uncompute
from projectq.ops import ClassicalInstructionGate
from projectq.types import BasicQubit
from projectq.ops import _command, X
from ._util import insert_engine, drop_engine_after
from enum import Enum

class State(Enum):
    AllZero = 0
    AllOne = -1


class ControlEngine(BasicEngine):
    """
    Adds control qubits to all commands that have no compute / uncompute tags.
    """

    def __init__(self, qubits, ctrl_state):
        """
        Initialize the control engine.

        Args:
            qubits (list of Qubit objects): qubits conditional on which the
                following operations are executed.
        """
        BasicEngine.__init__(self)
        self._qubits = qubits
        self._state = ctrl_state

    def _has_compute_uncompute_tag(self, cmd):
        """
        Return True if command cmd has a compute/uncompute tag.

        Args:
            cmd (Command object): a command object.
        """
        for t in cmd.tags:
            if t in [UncomputeTag(), ComputeTag()]:
                return True
        return False

    def _handle_command(self, cmd):
        if not self._has_compute_uncompute_tag(cmd) and not isinstance(cmd.gate, ClassicalInstructionGate):
            cmd.add_control_qubits(self._qubits, self._state)
        self.send([cmd])

    def receive(self, command_list):



        for cmd in command_list:
            self._handle_command(cmd)


class Control(object):
    """
    Condition an entire code block on the value of qubits being 1.

    Example:
        .. code-block:: python

            with Control(eng, ctrlqubits):
                do_something(otherqubits)
    """

    def __init__(self, engine, qubits, ctrl_state=State.AllOne):
        """
        Enter a controlled section.

        Args:
            engine: Engine which handles the commands (usually MainEngine)
            qubits (list of Qubit objects): Qubits to condition on

        Enter the section using a with-statement:

        .. code-block:: python

            with Control(eng, ctrlqubits):
                ...
        """
        self.engine = engine
        assert not isinstance(qubits, tuple)
        if isinstance(qubits, BasicQubit):
            qubits = [qubits]
        self._qubits = qubits

        # If the user inputs a single digit 0 or 1, extend the digit to all ctrl qubits
        if ctrl_state == 0  or ctrl_state == '0':
            self._state = str(ctrl_state)*len(qubits)
        elif type(ctrl_state) is State:
            if ctrl_state.value == -1:

                self._state = '1'*len(qubits)
            else:
                self._state = '0' * len(qubits)
        # If the user inputs an integer, convert it to binary bit string
        elif type(ctrl_state) is int:
            bit_length = len(self._qubits)
            self._state = '{0:b}'.format(ctrl_state).zfill(bit_length)

        # If the user inputs bit string, directly use it
        elif type(ctrl_state) is str:
            self._state = ctrl_state

        else:
            raise TypeError('Input must be a string, an integer or class State')
        # Raise exceptions for wrong cases: invalid string length and number
        assert len(self._state) == len(self._qubits), 'Control state has different length than control qubits'
        assert set(self._state).issubset({'0','1'}), 'Control state has string other than 1 and 0'


    def __enter__(self):
        if len(self._qubits) > 0:

            with Compute(self.engine):
                for i in range(len(self._state)):
                    if self._state[i]=='0':
                        X | self._qubits[i]

            ce = ControlEngine(self._qubits, self._state)
            insert_engine(self.engine, ce)


    def __exit__(self, type, value, traceback):
        # remove control handler from engine list (i.e. skip it)

        if len(self._qubits) > 0:
            drop_engine_after(self.engine)
            Uncompute(self.engine)


def get_control_count(cmd):
    """
    Return the number of control qubits of the command object cmd
    """
    return len(cmd.control_qubits)
