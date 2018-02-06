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
Tools to implement loops.

Example:
    .. code-block:: python

        with Loop(eng, 4):
            H | qb
        Rz(M_PI/3.) | qb
"""

from copy import deepcopy

from projectq.cengines import BasicEngine
from projectq.ops import Allocate, Deallocate
from ._util import insert_engine, drop_engine_after


class QubitManagementError(Exception):
    pass


class LoopTag(object):
    """
    Loop meta tag
    """
    def __init__(self, num):
        self.num = num
        self.id = LoopTag.loop_tag_id
        LoopTag.loop_tag_id += 1

    def __eq__(self, other):
        return (isinstance(other, LoopTag) and self.id == other.id and
                self.num == other.num)

    def __ne__(self, other):
        return not self.__eq__(other)

    loop_tag_id = 0


class LoopEngine(BasicEngine):
    """
    Stores all commands and, when done, executes them num times if no loop tag
    handler engine is available.
    If there is one, it adds a loop_tag to the commands and sends them on.
    """

    def __init__(self, num):
        """
        Initialize a LoopEngine.

        Args:
            num (int): Number of loop iterations.
        """
        BasicEngine.__init__(self)
        self._tag = LoopTag(num)
        self._cmd_list = []
        self._allocated_qubit_ids = set()
        self._deallocated_qubit_ids = set()
        # key: qubit id of a local qubit, i.e. a qubit which has been allocated
        #      and deallocated within the loop body.
        # value: list contain reference to each weakref qubit with this qubit
        #        id either within control_qubits or qubits.
        self._refs_to_local_qb = dict()
        self._next_engines_support_loop_tag = False

    def run(self):
        """
        Apply the loop statements to all stored commands.

        Unrolls the loop if LoopTag is not supported by any of the following
        engines, i.e., if

        .. code-block:: python
            is_meta_tag_supported(next_engine, LoopTag) == False
        """
        error_message = ("\n Error. Qubits have been allocated in with "
                         "Loop(eng, num) context,\n which have not "
                         "explicitely been deallocated in the Loop context.\n"
                         "Correct usage:\nwith Loop(eng, 5):\n"
                         "    qubit = eng.allocate_qubit()\n"
                         "    ...\n"
                         "    del qubit[0]\n")
        if not self._next_engines_support_loop_tag:
            # Unroll the loop
            # Check that local qubits have been deallocated:
            if self._deallocated_qubit_ids != self._allocated_qubit_ids:
                raise QubitManagementError(error_message)

            if len(self._allocated_qubit_ids) == 0:
                # No local qubits, just send the circuit num times
                for i in range(self._tag.num):
                    self.send(deepcopy(self._cmd_list))
            else:
                # Ancilla qubits have been allocated in loop body
                # For each iteration, allocate and deallocate a new qubit and
                # replace the qubit id in all commands using it.
                for i in range(self._tag.num):
                    if i == 0:  # Don't change local qubit ids
                        self.send(deepcopy(self._cmd_list))
                    else:
                        # Change local qubit ids before sending them
                        for refs_loc_qubit in self._refs_to_local_qb.values():
                            new_qb_id = self.main_engine.get_new_qubit_id()
                            for qubit_ref in refs_loc_qubit:
                                qubit_ref.id = new_qb_id
                        self.send(deepcopy(self._cmd_list))
        else:
            # Next engines support loop tag so no unrolling needed only
            # check that all qubits have been deallocated which have been
            # allocated in the loop body
            if self._deallocated_qubit_ids != self._allocated_qubit_ids:
                raise QubitManagementError(error_message)

    def receive(self, command_list):
        """
        Receive (and potentially temporarily store) all commands.

        Add LoopTag to all receiving commands and send to the next engine if
        a further engine is a LoopTag-handling engine. Otherwise store all
        commands (to later unroll them). Check that within the loop body,
        all allocated qubits have also been deallocated. If loop needs to be
        unrolled and ancilla qubits have been allocated within the loop body,
        then store a reference all these qubit ids (to change them when
        unrolling the loop)

        Args:
            command_list (list<Command>): List of commands to store and later
                unroll or, if there is a LoopTag-handling engine, add the
                LoopTag.
        """
        if (self._next_engines_support_loop_tag or
           self.next_engine.is_meta_tag_supported(LoopTag)):
            # Loop tag is supported, send everything with a LoopTag
            # Don't check is_meta_tag_supported anymore
            self._next_engines_support_loop_tag = True
            if self._tag.num == 0:
                return
            for cmd in command_list:
                if cmd.gate == Allocate:
                    self._allocated_qubit_ids.add(cmd.qubits[0][0].id)
                elif cmd.gate == Deallocate:
                    self._deallocated_qubit_ids.add(cmd.qubits[0][0].id)
                cmd.tags.append(self._tag)
                self.send([cmd])
        else:
            # LoopTag is not supported, save the full loop body
            self._cmd_list += command_list
            # Check for all local qubits allocated and deallocated in loop body
            for cmd in command_list:
                if cmd.gate == Allocate:
                    self._allocated_qubit_ids.add(cmd.qubits[0][0].id)
                    # Save reference to this local qubit
                    self._refs_to_local_qb[cmd.qubits[0][0].id] = (
                        [cmd.qubits[0][0]])
                elif cmd.gate == Deallocate:
                    self._deallocated_qubit_ids.add(cmd.qubits[0][0].id)
                    # Save reference to this local qubit
                    self._refs_to_local_qb[cmd.qubits[0][0].id].append(
                        cmd.qubits[0][0])
                else:
                    # Add a reference to each place a local qubit id is
                    # used as within either control_qubit or qubits
                    for control_qubit in cmd.control_qubits:
                        if control_qubit.id in self._allocated_qubit_ids:
                            self._refs_to_local_qb[control_qubit.id].append(
                                control_qubit)
                    for qureg in cmd.qubits:
                        for qubit in qureg:
                            if qubit.id in self._allocated_qubit_ids:
                                self._refs_to_local_qb[qubit.id].append(
                                    qubit)


class Loop(object):
    """
    Loop n times over an entire code block.

    Example:
        .. code-block:: python

            with Loop(eng, 4):
                # [quantum gates to be executed 4 times]

    Warning:
        If the code in the loop contains allocation of qubits, those qubits
        have to be deleted prior to exiting the 'with Loop()' context.

        This code is **NOT VALID**:

        .. code-block:: python

            with Loop(eng, 4):
                qb = eng.allocate_qubit()
                H | qb # qb is still available!!!

        The **correct way** of handling qubit (de-)allocation is as follows:

        .. code-block:: python

            with Loop(eng, 4):
                qb = eng.allocate_qubit()
                ...
                del qb # sends deallocate gate
    """

    def __init__(self, engine, num):
        """
        Enter a looped section.

        Args:
            engine: Engine handling the commands (usually MainEngine)
            num (int): Number of loop iterations

        Example:
            .. code-block:: python

                with Loop(eng, 4):
                    H | qb
                    Rz(M_PI/3.) | qb
        Raises:
            TypeError: If number of iterations (num) is not an integer
            ValueError: If number of iterations (num) is not >= 0
        """
        self.engine = engine
        if not isinstance(num, int):
            raise TypeError("Number of loop iterations must be an int.")
        if num < 0:
            raise ValueError("Number of loop iterations must be >=0.")
        self.num = num
        self._loop_eng = None

    def __enter__(self):
        if self.num != 1:
            self._loop_eng = LoopEngine(self.num)
            insert_engine(self.engine, self._loop_eng)

    def __exit__(self, type, value, traceback):
        if self.num != 1:
            # remove loop handler from engine list (i.e. skip it)
            self._loop_eng.run()
            self._loop_eng = None
            drop_engine_after(self.engine)
