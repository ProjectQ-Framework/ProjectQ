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
Compute, Uncompute, CustomUncompute.

Contains Compute, Uncompute, and CustomUncompute classes which can be used to
annotate Compute / Action / Uncompute sections, facilitating the conditioning
of the entire operation on the value of a qubit / register (only Action needs
controls). This file also defines the corresponding meta tags.
"""
from copy import deepcopy

import projectq
from projectq.cengines import BasicEngine
from projectq.ops import Allocate, Deallocate


class QubitManagementError(Exception):
    pass


class NoComputeSectionError(Exception):
    """
    Exception raised if uncompute is called but no compute section found.
    """
    pass


class ComputeTag(object):
    """
    Compute meta tag.
    """

    def __eq__(self, other):
        return isinstance(other, ComputeTag)

    def __ne__(self, other):
        return not self.__eq__(other)


class UncomputeTag(object):
    """
    Uncompute meta tag.
    """

    def __eq__(self, other):
        return isinstance(other, UncomputeTag)

    def __ne__(self, other):
        return not self.__eq__(other)


class ComputeEngine(BasicEngine):
    """
    Adds Compute-tags to all commands and stores them (to later uncompute them
    automatically)
    """

    def __init__(self):
        """
        Initialize a ComputeEngine.
        """
        BasicEngine.__init__(self)
        self._l = []
        self._compute = True
        # Save all qubit ids from qubits which are created or destroyed.
        self._allocated_qubit_ids = set()
        self._deallocated_qubit_ids = set()

    def _add_uncompute_tag(self, cmd):
        """
        Modify the command tags, inserting an UncomputeTag.

        Args:
            cmd (Command): Command to modify.
        """
        cmd.tags.append(UncomputeTag())
        return cmd

    def run_uncompute(self):
        """
        Send uncomputing gates.

        Sends the inverse of the stored commands in reverse order down to the
        next engine. And also deals with allocated qubits in Compute section.
        If a qubit has been allocated during compute, it will be deallocated
        during uncompute. If a qubit has been allocated and deallocated during
        compute, then a new qubit is allocated and deallocated during
        uncompute.
        """

        # No qubits allocated during Compute section -> do standard uncompute
        if len(self._allocated_qubit_ids) == 0:
            self.send([self._add_uncompute_tag(cmd.get_inverse())
                       for cmd in reversed(self._l)])
            return

        # qubits ids which were allocated and deallocated in Compute section
        ids_local_to_compute = self._allocated_qubit_ids.intersection(
            self._deallocated_qubit_ids)
        # qubit ids which were allocated but not yet deallocated in
        # Compute section
        ids_still_alive = self._allocated_qubit_ids.difference(
            self._deallocated_qubit_ids)

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
                        raise QubitManagementError(
                            "\nQubit was not found in " +
                            "MainEngine.active_qubits.\n")
                    self.send([self._add_uncompute_tag(cmd.get_inverse())])
                else:
                    self.send([self._add_uncompute_tag(cmd.get_inverse())])
            return
        # There was at least one qubit allocated and deallocated within
        # compute section. Handle uncompute in most general case
        new_local_id = dict()
        for cmd in reversed(self._l):
            if cmd.gate == Deallocate:
                assert (cmd.qubits[0][0].id) in ids_local_to_compute
                # Create new local qubit which lives within uncompute section
                # Allocate needs to have old tags + uncompute tag
                oldnext = self.next_engine

                def add_uncompute(command, old_tags=deepcopy(cmd.tags)):
                    command.tags = old_tags + [UncomputeTag()]
                    return command
                self.next_engine = projectq.cengines.CommandModifier(
                    add_uncompute)
                self.next_engine.next_engine = oldnext
                new_local_qb = self.allocate_qubit()
                self.next_engine = oldnext
                new_local_id[cmd.qubits[0][0].id] = deepcopy(
                    new_local_qb[0].id)
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
                    self.send([self._add_uncompute_tag(cmd.get_inverse())])

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
                        raise QubitManagementError(
                            "\nQubit was not found in " +
                            "MainEngine.active_qubits.\n")
                    self.send([self._add_uncompute_tag(cmd.get_inverse())])

            else:
                if len(new_local_id) == 0:
                    # No local qubits are active currently -> do standard
                    # uncompute
                    self.send([self._add_uncompute_tag(cmd.get_inverse())])
                else:
                    # Process commands by replacing each local qubit from
                    # compute section with new local qubit from the uncompute
                    # section
                    tmp_control_qubits = cmd.control_qubits
                    changed = False
                    for control_qubit in tmp_control_qubits:
                        if control_qubit.id in new_local_id:
                            control_qubit.id = new_local_id[control_qubit.id]
                            changed = True
                    if changed:
                        cmd.control_qubits = tmp_control_qubits
                    tmp_qubits = cmd.qubits
                    changed = False
                    for qureg in tmp_qubits:
                        for qubit in qureg:
                            if qubit.id in new_local_id:
                                qubit.id = new_local_id[qubit.id]
                                changed = True
                    if changed:
                        cmd.qubits = tmp_qubits
                    self.send([self._add_uncompute_tag(cmd.get_inverse())])

    def end_compute(self):
        """
        End the compute step (exit the with Compute() - statement).

        Will tell the Compute-engine to stop caching. It then waits for the
        uncompute instruction, which is when it sends all cached commands
        inverted and in reverse order down to the next compiler engine.

        Raises:
            QubitManagementError: If qubit has been deallocated in Compute
                section which has not been allocated in Compute section
        """
        self._compute = False
        if not self._allocated_qubit_ids.issuperset(
           self._deallocated_qubit_ids):
            raise QubitManagementError(
                "\nQubit has been deallocated in with Compute(eng) context \n"
                "which has not been allocated within this Compute section")

    def receive(self, command_list):
        """
        If in compute-mode: Receive commands and store deepcopy of each cmd.
                            Add ComputeTag to received cmd and send it on.
        Otherwise: send all received commands directly to next_engine.

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
    """
    Adds Uncompute-tags to all commands.
    """
    def __init__(self):
        """
        Initialize a UncomputeEngine.
        """
        BasicEngine.__init__(self)
        # Save all qubit ids from qubits which are created or destroyed.
        self._allocated_qubit_ids = set()
        self._deallocated_qubit_ids = set()

    def receive(self, command_list):
        """
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


class Compute(object):
    """
    Start a compute-section.

    Example:
        .. code-block:: python

            with Compute(eng):
                do_something(qubits)
            action(qubits)
            Uncompute(eng) # runs inverse of the compute section

    Warning:
        If qubits are allocated within the compute section, they must either be
        uncomputed and deallocated within that section or, alternatively,
        uncomputed and deallocated in the following uncompute section.

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

        After the uncompute section, ancilla qubits allocated within the
        compute section will be invalid (and deallocated). The same holds when
        using CustomUncompute.

        Failure to comply with these rules results in an exception being
        thrown.
    """

    def __init__(self, engine):
        """
        Initialize a Compute context.

        Args:
            engine (BasicEngine): Engine which is the first to receive all
                commands (normally: MainEngine).
        """
        self.engine = engine

    def __enter__(self):
        compute_eng = ComputeEngine()
        compute_eng.main_engine = self.engine.main_engine
        oldnext = self.engine.next_engine
        self.engine.next_engine = compute_eng
        compute_eng.next_engine = oldnext
        self._compute_eng = compute_eng

    def __exit__(self, type, value, traceback):
        # notify ComputeEngine that the compute section is done
        self._compute_eng.end_compute()


class CustomUncompute(object):
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
        QubitManagementError: If qubits are allocated within Compute or within
                              CustomUncompute context but are not deallocated.
    """

    def __init__(self, engine):
        """
        Initialize a CustomUncompute context.

        Args:
            engine (BasicEngine): Engine which is the first to receive all
                commands (normally: MainEngine).
        """
        self.engine = engine
        # Save all qubit ids from qubits which are created or destroyed.
        self._allocated_qubit_ids = set()
        self._deallocated_qubit_ids = set()

    def __enter__(self):
        # first, remove the compute engine
        compute_eng = self.engine.next_engine
        if not isinstance(compute_eng, ComputeEngine):
            raise NoComputeSectionError(
                "Invalid call to CustomUncompute: No corresponding"
                "'with Compute' statement found.")
        # Make copy so there is not reference to compute_eng anymore
        # after __enter__
        self._allocated_qubit_ids = compute_eng._allocated_qubit_ids.copy()
        self._deallocated_qubit_ids = compute_eng._deallocated_qubit_ids.copy()
        oldnext = compute_eng.next_engine
        self.engine.next_engine = oldnext

        # Now add uncompute engine
        uncompute_eng = UncomputeEngine()
        uncompute_eng.main_engine = self.engine.main_engine
        oldnext = self.engine.next_engine
        self.engine.next_engine = uncompute_eng
        uncompute_eng.next_engine = oldnext
        self._uncompute_eng = uncompute_eng

    def __exit__(self, type, value, traceback):
        # Check that all qubits allocated within Compute or within
        # CustomUncompute have been deallocated.
        all_allocated_qubits = self._allocated_qubit_ids.union(
            self._uncompute_eng._allocated_qubit_ids)
        all_deallocated_qubits = self._deallocated_qubit_ids.union(
            self._uncompute_eng._deallocated_qubit_ids)
        if len(all_allocated_qubits.difference(all_deallocated_qubits)) != 0:
            raise QubitManagementError(
                "\nError. Not all qubits have been deallocated which have \n" +
                "been allocated in the with Compute(eng) or with " +
                "CustomUncompute(eng) context.")
        # remove uncompute engine
        oldnext = self._uncompute_eng.next_engine
        self.engine.next_engine = oldnext


def Uncompute(engine):
    """
    Uncompute automatically.

    Example:
        .. code-block:: python

            with Compute(eng):
                do_something(qubits)
            action(qubits)
            Uncompute(eng) # runs inverse of the compute section
    """
    compute_eng = engine.next_engine
    if not isinstance(compute_eng, ComputeEngine):
        raise NoComputeSectionError("Invalid call to Uncompute: No "
                                    "corresponding 'with Compute' statement "
                                    "found.")
    compute_eng.run_uncompute()
    oldnext = compute_eng.next_engine
    engine.next_engine = oldnext
