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
Definition of Compute, Uncompute and CustomUncompute.

Contains Compute, Uncompute, and CustomUncompute classes which can be used to annotate Compute / Action / Uncompute
sections, facilitating the conditioning of the entire operation on the value of a qubit / register (only Action needs
controls). This file also defines the corresponding meta tags.
"""

from copy import deepcopy

from projectq.cengines import BasicEngine, CommandModifier
from projectq.ops import Allocate, Deallocate

from ._exceptions import QubitManagementError
from ._util import drop_engine_after, insert_engine


class NoComputeSectionError(Exception):
    """Exception raised if uncompute is called but no compute section found."""


class ComputeTag:  # pylint: disable=too-few-public-methods
    """Compute meta tag."""

    def __eq__(self, other):
        """Equal operator."""
        return isinstance(other, ComputeTag)


class UncomputeTag:  # pylint: disable=too-few-public-methods
    """Uncompute meta tag."""

    def __eq__(self, other):
        """Equal operator."""
        return isinstance(other, UncomputeTag)


def _add_uncompute_tag(cmd):
    """
    Modify the command tags, inserting an UncomputeTag.

    Args:
        cmd (Command): Command to modify.
    """
    cmd.tags.append(UncomputeTag())
    return cmd


class ComputeEngine(BasicEngine):
    """Add Compute-tags to all commands and stores them (to later uncompute them automatically)."""

    def __init__(self):
        """Initialize a ComputeEngine."""
        super().__init__()
        self._l = []
        self._compute = True
        # Save all qubit ids from qubits which are created or destroyed.
        self._allocated_qubit_ids = set()
        self._deallocated_qubit_ids = set()

    def run_uncompute(self):  # pylint: disable=too-many-branches,too-many-statements
        """
        Send uncomputing gates.

        Sends the inverse of the stored commands in reverse order down to the next engine. And also deals with
        allocated qubits in Compute section.  If a qubit has been allocated during compute, it will be deallocated
        during uncompute. If a qubit has been allocated and deallocated during compute, then a new qubit is allocated
        and deallocated during uncompute.
        """
        # No qubits allocated during Compute section -> do standard uncompute
        if len(self._allocated_qubit_ids) == 0:
            self.send([_add_uncompute_tag(cmd.get_inverse()) for cmd in reversed(self._l)])
            return

        # qubits ids which were allocated and deallocated in Compute section
        ids_local_to_compute = self._allocated_qubit_ids.intersection(self._deallocated_qubit_ids)

        # No qubits allocated and already deallocated during compute.
        # Don't inspect each command as below -> faster uncompute
        # Just find qubits which have been allocated and deallocate them
        if len(ids_local_to_compute) == 0:
            for cmd in reversed(self._l):
                if cmd.gate == Allocate:
                    qubit_id = cmd.qubits[0][0].id
                    # Remove this qubit from MainEngine.active_qubits and
                    # set qubit.id to = -1 in Qubit object such that it won't
                    # send another deallocate when it goes out of scope
                    qubit_found = False
                    for active_qubit in self.main_engine.active_qubits:
                        if active_qubit.id == qubit_id:
                            active_qubit.id = -1
                            active_qubit.__del__()
                            qubit_found = True
                            break
                    if not qubit_found:
                        raise QubitManagementError("\nQubit was not found in " + "MainEngine.active_qubits.\n")
                    self.send([_add_uncompute_tag(cmd.get_inverse())])
                else:
                    self.send([_add_uncompute_tag(cmd.get_inverse())])
            return
        # There was at least one qubit allocated and deallocated within
        # compute section. Handle uncompute in most general case
        new_local_id = {}
        for cmd in reversed(self._l):
            if cmd.gate == Deallocate:
                if not cmd.qubits[0][0].id in ids_local_to_compute:  # pragma: no cover
                    raise RuntimeError(
                        'Internal compiler error: qubit being deallocated is not found in the list of qubits local to '
                        'the Compute section'
                    )

                # Create new local qubit which lives within uncompute section

                # Allocate needs to have old tags + uncompute tag
                def add_uncompute(command, old_tags=deepcopy(cmd.tags)):
                    command.tags = old_tags + [UncomputeTag()]
                    return command

                tagger_eng = CommandModifier(add_uncompute)
                insert_engine(self, tagger_eng)
                new_local_qb = self.allocate_qubit()
                drop_engine_after(self)

                new_local_id[cmd.qubits[0][0].id] = deepcopy(new_local_qb[0].id)
                # Set id of new_local_qb to -1 such that it doesn't send a
                # deallocate gate
                new_local_qb[0].id = -1

            elif cmd.gate == Allocate:
                # Deallocate qubit
                if cmd.qubits[0][0].id in ids_local_to_compute:
                    # Deallocate local qubit and remove id from new_local_id
                    old_id = deepcopy(cmd.qubits[0][0].id)
                    cmd.qubits[0][0].id = new_local_id[cmd.qubits[0][0].id]
                    del new_local_id[old_id]
                    self.send([_add_uncompute_tag(cmd.get_inverse())])

                else:
                    # Deallocate qubit which was allocated in compute section:
                    qubit_id = cmd.qubits[0][0].id
                    # Remove this qubit from MainEngine.active_qubits and
                    # set qubit.id to = -1 in Qubit object such that it won't
                    # send another deallocate when it goes out of scope
                    qubit_found = False
                    for active_qubit in self.main_engine.active_qubits:
                        if active_qubit.id == qubit_id:
                            active_qubit.id = -1
                            active_qubit.__del__()
                            qubit_found = True
                            break
                    if not qubit_found:
                        raise QubitManagementError("\nQubit was not found in " + "MainEngine.active_qubits.\n")
                    self.send([_add_uncompute_tag(cmd.get_inverse())])

            else:
                # Process commands by replacing each local qubit from
                # compute section with new local qubit from the uncompute
                # section
                if new_local_id:  # Only if we still have local qubits
                    for qureg in cmd.all_qubits:
                        for qubit in qureg:
                            if qubit.id in new_local_id:
                                qubit.id = new_local_id[qubit.id]

                self.send([_add_uncompute_tag(cmd.get_inverse())])

    def end_compute(self):
        """
        End the compute step (exit the with Compute() - statement).

        Will tell the Compute-engine to stop caching. It then waits for the uncompute instruction, which is when it
        sends all cached commands inverted and in reverse order down to the next compiler engine.

        Raises:
            QubitManagementError: If qubit has been deallocated in Compute section which has not been allocated in
                Compute section
        """
        self._compute = False
        if not self._allocated_qubit_ids.issuperset(self._deallocated_qubit_ids):
            raise QubitManagementError(
                "\nQubit has been deallocated in with Compute(eng) context \n"
                "which has not been allocated within this Compute section"
            )

    def receive(self, command_list):
        """
        Receive a list of commands.

        If in compute-mode, receive commands and store deepcopy of each cmd.  Add ComputeTag to received cmd and send
        it on. Otherwise, send all received commands directly to next_engine.

        Args:
            command_list (list<Command>): List of commands to receive.
        """
        if self._compute:
            for cmd in command_list:
                if cmd.gate == Allocate:
                    self._allocated_qubit_ids.add(cmd.qubits[0][0].id)
                elif cmd.gate == Deallocate:
                    self._deallocated_qubit_ids.add(cmd.qubits[0][0].id)
                self._l.append(deepcopy(cmd))
                tags = cmd.tags
                tags.append(ComputeTag())
            self.send(command_list)
        else:
            self.send(command_list)


class UncomputeEngine(BasicEngine):
    """Adds Uncompute-tags to all commands."""

    def __init__(self):
        """Initialize a UncomputeEngine."""
        super().__init__()
        # Save all qubit ids from qubits which are created or destroyed.
        self._allocated_qubit_ids = set()
        self._deallocated_qubit_ids = set()

    def receive(self, command_list):
        """
        Receive a list of commands.

        Receive commands and add an UncomputeTag to their tags.

        Args:
            command_list (list<Command>): List of commands to handle.
        """
        for cmd in command_list:
            if cmd.gate == Allocate:
                self._allocated_qubit_ids.add(cmd.qubits[0][0].id)
            elif cmd.gate == Deallocate:
                self._deallocated_qubit_ids.add(cmd.qubits[0][0].id)
            tags = cmd.tags
            tags.append(UncomputeTag())
            self.send([cmd])


class Compute:
    """
    Start a compute-section.

    Example:
        .. code-block:: python

            with Compute(eng):
                do_something(qubits)
            action(qubits)
            Uncompute(eng)  # runs inverse of the compute section

    Warning:
        If qubits are allocated within the compute section, they must either be uncomputed and deallocated within that
        section or, alternatively, uncomputed and deallocated in the following uncompute section.

        This means that the following examples are valid:

        .. code-block:: python

            with Compute(eng):
                anc = eng.allocate_qubit()
                do_something_with_ancilla(anc)
                ...
                uncompute_ancilla(anc)
                del anc

            do_something_else(qubits)

            Uncompute(eng)  # will allocate a new ancilla (with a different id)
            # and then deallocate it again

        .. code-block:: python

            with Compute(eng):
                anc = eng.allocate_qubit()
                do_something_with_ancilla(anc)
                ...

            do_something_else(qubits)

            Uncompute(eng)  # will deallocate the ancilla!

        After the uncompute section, ancilla qubits allocated within the compute section will be invalid (and
        deallocated). The same holds when using CustomUncompute.

        Failure to comply with these rules results in an exception being thrown.
    """

    def __init__(self, engine):
        """
        Initialize a Compute context.

        Args:
            engine (BasicEngine): Engine which is the first to receive all commands (normally: MainEngine).
        """
        self.engine = engine
        self._compute_eng = None

    def __enter__(self):
        """Context manager enter function."""
        self._compute_eng = ComputeEngine()
        insert_engine(self.engine, self._compute_eng)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Context manager exit function."""
        # notify ComputeEngine that the compute section is done
        self._compute_eng.end_compute()
        self._compute_eng = None


class CustomUncompute:
    """
    Start a custom uncompute-section.

    Example:
        .. code-block:: python

            with Compute(eng):
                do_something(qubits)
            action(qubits)
            with CustomUncompute(eng):
                do_something_inverse(qubits)

    Raises:
        QubitManagementError: If qubits are allocated within Compute or within CustomUncompute context but are not
                              deallocated.
    """

    def __init__(self, engine):
        """
        Initialize a CustomUncompute context.

        Args:
            engine (BasicEngine): Engine which is the first to receive all commands (normally: MainEngine).
        """
        self.engine = engine
        # Save all qubit ids from qubits which are created or destroyed.
        self._allocated_qubit_ids = set()
        self._deallocated_qubit_ids = set()
        self._uncompute_eng = None

    def __enter__(self):
        """Context manager enter function."""
        # first, remove the compute engine
        compute_eng = self.engine.next_engine
        if not isinstance(compute_eng, ComputeEngine):
            raise NoComputeSectionError(
                "Invalid call to CustomUncompute: No corresponding 'with Compute' statement found."
            )
        # Make copy so there is not reference to compute_eng anymore
        # after __enter__
        self._allocated_qubit_ids = compute_eng._allocated_qubit_ids.copy()
        self._deallocated_qubit_ids = compute_eng._deallocated_qubit_ids.copy()
        drop_engine_after(self.engine)

        # Now add uncompute engine
        self._uncompute_eng = UncomputeEngine()
        insert_engine(self.engine, self._uncompute_eng)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Context manager exit function."""
        # If an error happens in this context, qubits might not have been
        # deallocated because that code section was not yet executed,
        # so don't check and raise an additional error.
        if exc_type is not None:
            return
        # Check that all qubits allocated within Compute or within
        # CustomUncompute have been deallocated.
        all_allocated_qubits = self._allocated_qubit_ids.union(self._uncompute_eng._allocated_qubit_ids)
        all_deallocated_qubits = self._deallocated_qubit_ids.union(self._uncompute_eng._deallocated_qubit_ids)
        if len(all_allocated_qubits.difference(all_deallocated_qubits)) != 0:
            raise QubitManagementError(
                "\nError. Not all qubits have been deallocated which have \n"
                + "been allocated in the with Compute(eng) or with "
                + "CustomUncompute(eng) context."
            )
        # remove uncompute engine
        drop_engine_after(self.engine)


def Uncompute(engine):  # pylint: disable=invalid-name
    """
    Uncompute automatically.

    Example:
        .. code-block:: python

            with Compute(eng):
                do_something(qubits)
            action(qubits)
            Uncompute(eng)  # runs inverse of the compute section
    """
    compute_eng = engine.next_engine
    if not isinstance(compute_eng, ComputeEngine):
        raise NoComputeSectionError("Invalid call to Uncompute: No corresponding 'with Compute' statement found.")
    compute_eng.run_uncompute()
    drop_engine_after(engine)
