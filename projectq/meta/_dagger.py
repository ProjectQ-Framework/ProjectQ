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
Tools to easily invert a sequence of gates.

.. code-block:: python

    with Dagger(eng):
        H | qubit1
        Rz(0.5) | qubit2
"""

from projectq.cengines import BasicEngine
from projectq.ops import Allocate, Deallocate
from ._util import insert_engine, drop_engine_after


class QubitManagementError(Exception):
    pass


class DaggerEngine(BasicEngine):
    """
    Stores all commands and, when done, inverts the circuit & runs it.
    """

    def __init__(self):
        BasicEngine.__init__(self)
        self._commands = []
        self._allocated_qubit_ids = set()
        self._deallocated_qubit_ids = set()

    def run(self):
        """
        Run the stored circuit in reverse and check that local qubits
        have been deallocated.
        """
        if self._deallocated_qubit_ids != self._allocated_qubit_ids:
                raise QubitManagementError(
                    "\n Error. Qubits have been allocated in 'with " +
                    "Dagger(eng)' context,\n which have not explicitely " +
                    "been deallocated.\n" +
                    "Correct usage:\n" +
                    "with Dagger(eng):\n" +
                    "    qubit = eng.allocate_qubit()\n" +
                    "    ...\n" +
                    "    del qubit[0]\n")

        for cmd in reversed(self._commands):
                self.send([cmd.get_inverse()])

    def receive(self, command_list):
        """
        Receive a list of commands and store them for later inversion.

        Args:
            command_list (list<Command>): List of commands to temporarily
                store.
        """
        for cmd in command_list:
            if cmd.gate == Allocate:
                self._allocated_qubit_ids.add(cmd.qubits[0][0].id)
            elif cmd.gate == Deallocate:
                self._deallocated_qubit_ids.add(cmd.qubits[0][0].id)
        self._commands.extend(command_list)


class Dagger(object):
    """
    Invert an entire code block.

    Use it with a with-statement, i.e.,

    .. code-block:: python

        with Dagger(eng):
            [code to invert]

    Warning:
        If the code to invert contains allocation of qubits, those qubits have
        to be deleted prior to exiting the 'with Dagger()' context.

        This code is **NOT VALID**:

        .. code-block:: python

            with Dagger(eng):
                qb = eng.allocate_qubit()
                H | qb # qb is still available!!!

        The **correct way** of handling qubit (de-)allocation is as follows:

        .. code-block:: python

            with Dagger(eng):
                qb = eng.allocate_qubit()
                ...
                del qb # sends deallocate gate (which becomes an allocate)
    """

    def __init__(self, engine):
        """
        Enter an inverted section.

        Args:
            engine: Engine which handles the commands (usually MainEngine)

        Example (executes an inverse QFT):

        .. code-block:: python

            with Dagger(eng):
                QFT | qubits
        """
        self.engine = engine
        self._dagger_eng = None

    def __enter__(self):
        self._dagger_eng = DaggerEngine()
        insert_engine(self.engine, self._dagger_eng)

    def __exit__(self, type, value, traceback):
        # run dagger engine
        self._dagger_eng.run()
        self._dagger_eng = None
        # remove dagger handler from engine list (i.e. skip it)
        drop_engine_after(self.engine)
