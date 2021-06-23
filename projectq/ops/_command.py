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
This file defines the apply_command function and the Command class.

When a gate is applied to qubits, e.g.,

.. code-block:: python

    CNOT | (qubit1, qubit2)

a Command object is generated which represents both the gate, qubits and control qubits. This Command object then gets
sent down the compilation pipeline.

In detail, the Gate object overloads the operator| (magic method __or__) to generate a Command object which stores the
qubits in a canonical order using interchangeable qubit indices defined by the gate to allow the optimizer to cancel
the following two gates

.. code-block:: python

    Swap | (qubit1, qubit2)
    Swap | (qubit2, qubit1)

The command then gets sent to the MainEngine via the
apply wrapper (apply_command).
"""

from copy import deepcopy
from enum import IntEnum
import itertools

import projectq
from projectq.types import WeakQubitRef, Qureg


class IncompatibleControlState(Exception):
    """
    Exception thrown when trying to set two incompatible states for a control qubit.
    """


class CtrlAll(IntEnum):
    """Enum type to initialise the control state of qubits"""

    Zero = 0
    One = 1


def apply_command(cmd):
    """
    Apply a command.

    Extracts the qubits-owning (target) engine from the Command object and sends the Command to it.

    Args:
        cmd (Command): Command to apply
    """
    engine = cmd.engine
    engine.receive([cmd])


class Command:  # pylint: disable=too-many-instance-attributes
    """
    Class used as a container to store commands. If a gate is applied to qubits, then the gate and qubits are saved in
    a command object. Qubits are copied into WeakQubitRefs in order to allow early deallocation (would be kept alive
    otherwise). WeakQubitRef qubits don't send deallocate gate when destructed.

    Attributes:
        gate: The gate to execute
        qubits: Tuple of qubit lists (e.g. Quregs). Interchangeable qubits are stored in a unique order
        control_qubits: The Qureg of control qubits in a unique order
        engine: The engine (usually: MainEngine)
        tags: The list of tag objects associated with this command (e.g., ComputeTag, UncomputeTag, LoopTag, ...). tag
          objects need to support ==, != (__eq__ and __ne__) for comparison as used in e.g.  TagRemover. New tags
          should always be added to the end of the list.  This means that if there are e.g. two LoopTags in a command,
          tag[0] is from the inner scope while tag[1] is from the other scope as the other scope receives the command
          after the inner scope LoopEngine and hence adds its LoopTag to the end.
        all_qubits: A tuple of control_qubits + qubits
    """

    def __init__(
        self, engine, gate, qubits, controls=(), tags=(), control_state=CtrlAll.One
    ):  # pylint: disable=too-many-arguments
        """
        Initialize a Command object.

        Note:
            control qubits (Command.control_qubits) are stored as a list of qubits, and command tags (Command.tags) as
            a list of tag- objects. All functions within this class also work if WeakQubitRefs are supplied instead of
            normal Qubit objects (see WeakQubitRef).

        Args:
            engine (projectq.cengines.BasicEngine): engine which created the qubit (mostly the MainEngine)
            gate (projectq.ops.Gate): Gate to be executed
            qubits (tuple[Qureg]): Tuple of quantum registers (to which the gate is applied)
            controls (Qureg|list[Qubit]): Qubits that condition the command.
            tags (list[object]): Tags associated with the command.
            control_state(int,str,projectq.meta.CtrlAll) Control state for any control qubits
        """

        qubits = tuple([WeakQubitRef(qubit.engine, qubit.id) for qubit in qreg] for qreg in qubits)

        self.gate = gate
        self.tags = list(tags)
        self.qubits = qubits  # property
        self.control_qubits = controls  # property
        self.engine = engine  # property
        self.control_state = control_state  # property

    @property
    def qubits(self):
        """Qubits stored in a Command object"""
        return self._qubits

    @qubits.setter
    def qubits(self, qubits):
        """Set the qubits stored in a Command object"""
        self._qubits = self._order_qubits(qubits)

    def __deepcopy__(self, memo):
        """Deepcopy implementation. Engine should stay a reference."""
        return Command(
            self.engine,
            deepcopy(self.gate),
            self.qubits,
            list(self.control_qubits),
            deepcopy(self.tags),
        )

    def get_inverse(self):
        """
        Get the command object corresponding to the inverse of this command.

        Inverts the gate (if possible) and creates a new command object from the result.

        Raises:
            NotInvertible: If the gate does not provide an inverse (see BasicGate.get_inverse)
        """
        return Command(
            self._engine,
            projectq.ops.get_inverse(self.gate),
            self.qubits,
            list(self.control_qubits),
            deepcopy(self.tags),
        )

    def is_identity(self):
        """
        Evaluate if the gate called in the command object is an identity gate.

        Returns:
            True if the gate is equivalent to an Identity gate, False otherwise
        """
        return projectq.ops.is_identity(self.gate)

    def get_merged(self, other):
        """
        Merge this command with another one and return the merged command
        object.

        Args:
            other: Other command to merge with this one (self)

        Raises:
            NotMergeable: if the gates don't supply a get_merged()-function
                or can't be merged for other reasons.
        """
        if self.tags == other.tags and self.all_qubits == other.all_qubits and self.engine == other.engine:
            return Command(
                self.engine,
                self.gate.get_merged(other.gate),
                self.qubits,
                self.control_qubits,
                deepcopy(self.tags),
            )
        raise projectq.ops.NotMergeable("Commands not mergeable.")

    def _order_qubits(self, qubits):
        """
        Order the given qubits according to their IDs (for unique comparison of
        commands).

        Args:
            qubits: Tuple of quantum registers (i.e., tuple of lists of qubits)

        Returns: Ordered tuple of quantum registers
        """
        ordered_qubits = list(qubits)
        # e.g. [[0,4],[1,2,3]]
        interchangeable_qubit_indices = self.interchangeable_qubit_indices
        for old_positions in interchangeable_qubit_indices:
            new_positions = sorted(old_positions, key=lambda x: ordered_qubits[x][0].id)
            qubits_new_order = [ordered_qubits[i] for i in new_positions]
            for i, pos in enumerate(old_positions):
                ordered_qubits[pos] = qubits_new_order[i]
        return tuple(ordered_qubits)

    @property
    def interchangeable_qubit_indices(self):
        """
        Return nested list of qubit indices which are interchangeable.

        Certain qubits can be interchanged (e.g., the qubit order for a Swap
        gate). To ensure that only those are sorted when determining the
        ordering (see _order_qubits), self.interchangeable_qubit_indices is
        used.
        Example:
            If we can interchange qubits 0,1 and qubits 3,4,5,
            then this function returns [[0,1],[3,4,5]]
        """
        return self.gate.interchangeable_qubit_indices

    @property
    def control_qubits(self):
        """Returns Qureg of control qubits."""
        return self._control_qubits

    @control_qubits.setter
    def control_qubits(self, qubits):
        """
        Set control_qubits to qubits

        Args:
            control_qubits (Qureg): quantum register
        """
        self._control_qubits = [WeakQubitRef(qubit.engine, qubit.id) for qubit in qubits]
        self._control_qubits = sorted(self._control_qubits, key=lambda x: x.id)

    @property
    def control_state(self):
        """Returns the state of the control qubits (ie. either positively- or negatively-controlled)"""
        return self._control_state

    @control_state.setter
    def control_state(self, state):
        """
        Set control_state to state

        Args:
            state (int,str,projectq.meta.CtrtAll): state of control qubit (ie. positive or negative)
        """
        # NB: avoid circular imports
        from projectq.meta import canonical_ctrl_state  # pylint: disable=import-outside-toplevel

        self._control_state = canonical_ctrl_state(state, len(self._control_qubits))

    def add_control_qubits(self, qubits, state=CtrlAll.One):
        """
        Add (additional) control qubits to this command object.

        They are sorted to ensure a canonical order. Also Qubit objects
        are converted to WeakQubitRef objects to allow garbage collection and
        thus early deallocation of qubits.

        Args:
            qubits (list of Qubit objects): List of qubits which control this gate
            state (int,str,CtrlAll): Control state (ie. positive or negative) for the qubits being added as
                control qubits.
        """
        # NB: avoid circular imports
        from projectq.meta import canonical_ctrl_state  # pylint: disable=import-outside-toplevel

        if not isinstance(qubits, list):
            raise ValueError('Control qubits must be a list of qubits!')
        self._control_qubits.extend([WeakQubitRef(qubit.engine, qubit.id) for qubit in qubits])
        self._control_state += canonical_ctrl_state(state, len(qubits))

        zipped = sorted(zip(self._control_qubits, self._control_state), key=lambda x: x[0].id)
        unzipped_qubit, unzipped_state = zip(*zipped)
        self._control_qubits, self._control_state = list(unzipped_qubit), ''.join(unzipped_state)

        # Make sure that we do not have contradicting control states for any control qubits
        for _, data in itertools.groupby(zipped, key=lambda x: x[0].id):
            qubits, states = list(zip(*data))
            if len(set(states)) != 1:
                raise IncompatibleControlState(
                    'Control qubits {} cannot have conflicting control states: {}'.format(list(qubits), states)
                )

    @property
    def all_qubits(self):
        """
        Get all qubits (gate and control qubits).

        Returns a tuple T where T[0] is a quantum register (a list of
        WeakQubitRef objects) containing the control qubits and T[1:] contains
        the quantum registers to which the gate is applied.
        """
        return (self.control_qubits,) + self.qubits

    @property
    def engine(self):
        """
        Return engine to which the qubits belong / on which the gates are
        executed.
        """
        return self._engine

    @engine.setter
    def engine(self, engine):
        """
        Set / Change engine of all qubits to engine.

        Args:
            engine: New owner of qubits and owner of this Command object
        """
        self._engine = engine
        for qureg in self.qubits:
            for qubit in qureg:
                qubit.engine = engine
        for qubit in self.control_qubits:
            qubit.engine = engine

    def __eq__(self, other):
        """
        Compare this command to another command.

        Args:
            other (Command): Command object to compare this to

        Returns: True if Command objects are equal (same gate, applied to same
        qubits; ordered modulo interchangeability; and same tags)
        """
        if (
            isinstance(other, self.__class__)
            and self.gate == other.gate
            and self.tags == other.tags
            and self.engine == other.engine
            and self.all_qubits == other.all_qubits
        ):
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.to_string()

    def to_string(self, symbols=False):
        """
        Get string representation of this Command object.
        """
        qubits = self.qubits
        ctrlqubits = self.control_qubits
        if len(ctrlqubits) > 0:
            qubits = (self.control_qubits,) + qubits
        qstring = ""
        if len(qubits) == 1:
            qstring = str(Qureg(qubits[0]))
        else:
            qstring = "( "
            for qreg in qubits:
                qstring += str(Qureg(qreg))
                qstring += ", "
            qstring = qstring[:-2] + " )"
        cstring = "C" * len(ctrlqubits)
        return cstring + self.gate.to_string(symbols) + " | " + qstring
