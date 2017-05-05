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
from projectq.ops import ClassicalInstructionGate
from projectq.meta import ComputeTag, UncomputeTag
from projectq.types import BasicQubit


class ControlEngine(BasicEngine):
    """
    Adds control qubits to all commands that have no compute / uncompute tags.
    """

    def __init__(self, qubits):
        """
        Initialize the control engine.

        Args:
            qubits (list of Qubit objects): qubits conditional on which the
                following operations are executed.
        """
        BasicEngine.__init__(self)
        self._qubits = qubits

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
        if (not self._has_compute_uncompute_tag(cmd) and not
                isinstance(cmd.gate, ClassicalInstructionGate)):
            cmd.add_control_qubits(self._qubits)
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

    def __init__(self, engine, qubits):
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
        assert(not isinstance(qubits, tuple))
        if isinstance(qubits, BasicQubit):
            qubits = [qubits]
        self._qubits = qubits

    def __enter__(self):
        if len(self._qubits) > 0:
            ce = ControlEngine(self._qubits)
            ce.main_engine = self.engine.main_engine
            oldnext = self.engine.next_engine
            self.engine.next_engine = ce
            ce.next_engine = oldnext
            self._ce = ce

    def __exit__(self, type, value, traceback):
        # remove control handler from engine list (i.e. skip it)
        if len(self._qubits) > 0:
            oldnext = self._ce.next_engine
            self.engine.next_engine = oldnext


def get_control_count(cmd):
    """
    Return the number of control qubits of the command object cmd
    """
    return len(cmd.control_qubits)
