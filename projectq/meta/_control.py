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
from projectq.ops import ClassicalInstructionGate, CtrlAll
from projectq.types import BasicQubit

from ._compute import ComputeTag, UncomputeTag
from ._util import insert_engine, drop_engine_after


def canonical_ctrl_state(ctrl_state, num_qubits):
    """
    Return canonical form for control state

    Args:
        ctrl_state (int,str,CtrlAll): Initial control state representation
        num_qubits (int): number of control qubits

    Returns:
        Canonical form of control state (currently a string composed of '0' and '1')

    Note:
        In case of integer values for `ctrl_state`, the least significant bit applies to the first qubit in the qubit
        register, e.g. if ctrl_state == 2, its binary representation if '10' with the least significan bit being 0.

        This means in particular that the followings are equivalent:

        .. code-block:: python

            canonical_ctrl_state(6, 3) == canonical_ctrl_state(6, '110')
    """
    if not num_qubits:
        return ''

    if isinstance(ctrl_state, CtrlAll):
        if ctrl_state == CtrlAll.One:
            return '1' * num_qubits
        return '0' * num_qubits

    if isinstance(ctrl_state, int):
        # If the user inputs an integer, convert it to binary bit string
        converted_str = '{0:b}'.format(ctrl_state).zfill(num_qubits)[::-1]
        if len(converted_str) != num_qubits:
            raise ValueError(
                'Control state specified as {} ({}) is higher than maximum for {} qubits: {}'.format(
                    ctrl_state, converted_str, num_qubits, 2 ** num_qubits - 1
                )
            )
        return converted_str

    if isinstance(ctrl_state, str):
        # If the user inputs bit string, directly use it
        if len(ctrl_state) != num_qubits:
            raise ValueError(
                'Control state {} has different length than the number of control qubits {}'.format(
                    ctrl_state, num_qubits
                )
            )
        if not set(ctrl_state).issubset({'0', '1'}):
            raise ValueError('Control state {} has string other than 1 and 0'.format(ctrl_state))
        return ctrl_state

    raise TypeError('Input must be a string, an integer or an enum value of class State')


def _has_compute_uncompute_tag(cmd):
    """
    Return True if command cmd has a compute/uncompute tag.

    Args:
        cmd (Command object): a command object.
    """
    for tag in cmd.tags:
        if tag in [UncomputeTag(), ComputeTag()]:
            return True
    return False


class ControlEngine(BasicEngine):
    """
    Adds control qubits to all commands that have no compute / uncompute tags.
    """

    def __init__(self, qubits, ctrl_state=CtrlAll.One):
        """
        Initialize the control engine.

        Args:
            qubits (list of Qubit objects): qubits conditional on which the
                following operations are executed.
        """
        BasicEngine.__init__(self)
        self._qubits = qubits
        self._state = ctrl_state

    def _handle_command(self, cmd):
        if not _has_compute_uncompute_tag(cmd) and not isinstance(cmd.gate, ClassicalInstructionGate):
            cmd.add_control_qubits(self._qubits, self._state)
        self.send([cmd])

    def receive(self, command_list):
        """Forward all commands to the next engine."""
        for cmd in command_list:
            self._handle_command(cmd)


class Control:
    """
    Condition an entire code block on the value of qubits being 1.

    Example:
        .. code-block:: python

            with Control(eng, ctrlqubits):
                do_something(otherqubits)
    """

    def __init__(self, engine, qubits, ctrl_state=CtrlAll.One):
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
        if isinstance(qubits, tuple):
            raise TypeError('Control qubits must be a list, not a tuple!')
        if isinstance(qubits, BasicQubit):
            qubits = [qubits]
        self._qubits = qubits
        self._state = canonical_ctrl_state(ctrl_state, len(self._qubits))

    def __enter__(self):
        if len(self._qubits) > 0:
            engine = ControlEngine(self._qubits, self._state)
            insert_engine(self.engine, engine)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # remove control handler from engine list (i.e. skip it)
        if len(self._qubits) > 0:
            drop_engine_after(self.engine)


def get_control_count(cmd):
    """
    Return the number of control qubits of the command object cmd
    """
    return len(cmd.control_qubits)


def has_negative_control(cmd):
    """
    Returns whether a command has negatively controlled qubits
    """
    return get_control_count(cmd) > 0 and '0' in cmd.control_state
