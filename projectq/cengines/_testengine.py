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

"""TestEngine and DummyEngine."""

from copy import deepcopy

from projectq.cengines import BasicEngine
from projectq.ops import (
    FlushGate,
    BasicMathGate,
    ClassicalInstructionGate,
    XGate
)


class CompareEngine(BasicEngine):
    """
    CompareEngine is an engine which saves all commands. It is only intended
    for testing purposes. Two CompareEngine backends can be compared and
    return True if they contain the same commmands.
    """
    def __init__(self):
        BasicEngine.__init__(self)
        self._l = [[]]

    def is_available(self, cmd):
        return True

    def cache_cmd(self, cmd):
        # are there qubit ids that haven't been added to the list?
        all_qubit_id_list = [qubit.id for qureg in cmd.all_qubits
                             for qubit in qureg]
        maxidx = int(0)
        for qubit_id in all_qubit_id_list:
            maxidx = max(maxidx, qubit_id)

        # if so, increase size of list to account for these qubits
        add = maxidx+1-len(self._l)
        if add > 0:
            for i in range(add):
                self._l += [[]]

        # add gate command to each of the qubits involved
        for qubit_id in all_qubit_id_list:
            self._l[qubit_id] += [cmd]

    def receive(self, command_list):
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self.cache_cmd(cmd)
        if not self.is_last_engine:
            self.send(command_list)

    def compare_cmds(self, c1, c2):
        c2 = deepcopy(c2)
        c2.engine = c1.engine
        return c1 == c2

    def __eq__(self, other):
        if (not isinstance(other, CompareEngine) or
           len(self._l) != len(other._l)):
            return False
        for i in range(len(self._l)):
            if len(self._l[i]) != len(other._l[i]):
                return False
            for j in range(len(self._l[i])):
                if not self.compare_cmds(self._l[i][j], other._l[i][j]):
                    return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        string = ""
        for qubit_id in range(len(self._l)):
            string += "Qubit {0} : ".format(qubit_id)
            for command in self._l[qubit_id]:
                string += str(command) + ", "
            string = string[:-2] + "\n"
        return string


class DummyEngine(BasicEngine):
    """
    DummyEngine used for testing.

    The DummyEngine forwards all commands directly to next engine.
    If self.is_last_engine == True it just discards all gates.
    By setting save_commands == True all commands get saved as a
    list in self.received_commands. Elements are appended to this
    list so they are ordered according to when they are received.
    """
    def __init__(self, save_commands=False):
        """
        Initialize DummyEngine

        Args:
            save_commands (default = False): If True, commands are saved in
                                             self.received_commands.
        """
        BasicEngine.__init__(self)
        self.save_commands = save_commands
        self.received_commands = []

    def is_available(self, cmd):
        return True

    def receive(self, command_list):
        if self.save_commands:
            self.received_commands.extend(command_list)
        if not self.is_last_engine:
            self.send(command_list)
        else:
            pass


class LimitedCapabilityEngine(BasicEngine):
    """
    An engine that restricts the available operations, on top of any
    restrictions for later engines.

    Only commands that meet as least one of the 'allow' criteria and NONE of
    the 'ban' criteria given to the constructor are considered available. Also
    gates are not considered available if the underlying engine can't receive
    them.
    """
    def __init__(self,
                 allow_classical_instructions=True,
                 allow_all=False,
                 allow_arithmetic=False,
                 allow_toffoli=False,
                 allow_nots_with_many_controls=False,
                 allow_single_qubit_gates=False,
                 allow_classes=(),
                 allow_custom_predicate=lambda cmd: False,
                 ban_classes=(),
                 ban_custom_predicate=lambda cmd: False):
        """
        Constructs a LimitedCapabilityEngine that accepts commands based on
        the given criteria arguments.

        Note that a command is accepted if it meets *none* of the ban criteria
        and *any* of the allow criteria.

        Args:
            allow_classical_instructions (bool):
                Enabled by default. Marks classical instruction commands like
                'Allocate', 'Flush', etc as available.

            allow_all (bool):
                Defaults to allowing all commands.
                Any ban criteria will override this default.

            allow_arithmetic (bool):
                Allows gates with the BasicMathGate type.

            allow_toffoli (bool):
                Allows NOT gates with at most 2 controls.

            allow_nots_with_many_controls (bool):
                Allows NOT gates with arbitrarily many controls.

            allow_single_qubit_gates (bool):
                Allows gates that affect only a single qubit
                (counting controls).

            allow_classes (list[type]):
                Allows any gates matching the given class.

            allow_custom_predicate (function(Command) : bool):
                Allows any gates that cause the given function to return True.

            ban_classes (list[type]):
                Bans any gates matching the given class.

            ban_custom_predicate (function(Command) : bool):
                Bans gates that cause the given function to return True.
        """
        BasicEngine.__init__(self)
        self.allow_arithmetic = allow_arithmetic
        self.allow_all = allow_all
        self.allow_nots_with_many_controls = allow_nots_with_many_controls
        self.allow_single_qubit_gates = allow_single_qubit_gates
        self.allow_toffoli = allow_toffoli
        self.allow_classical_instructions = allow_classical_instructions
        self.allowed_classes = tuple(allow_classes)
        self.allow_custom_predicate = allow_custom_predicate
        self.ban_classes = tuple(ban_classes)
        self.ban_custom_predicate = ban_custom_predicate

    def is_available(self, cmd):
        return (self._allow_command(cmd) and
                not self._ban_command(cmd) and
                (self.is_last_engine or self.next_engine.is_available(cmd)))

    def receive(self, command_list):
        if not self.is_last_engine:
            self.send(command_list)

    def _ban_command(self, cmd):
        if any(isinstance(cmd.gate, c) for c in self.ban_classes):
            return True

        return self.ban_custom_predicate(cmd)

    def _allow_command(self, cmd):
        if self.allow_arithmetic and isinstance(cmd.gate, BasicMathGate):
            return True

        if (self.allow_classical_instructions and
                isinstance(cmd.gate, ClassicalInstructionGate)):
            return True

        if (self.allow_toffoli and isinstance(cmd.gate, XGate) and
                len(cmd.control_qubits) <= 2):
            return True

        if self.allow_single_qubit_gates and len(cmd.all_qubits) == 1:
            return True

        if self.allow_nots_with_many_controls and isinstance(cmd.gate, XGate):
            return True

        if any(isinstance(cmd.gate, c) for c in self.allowed_classes):
            return True

        if self.allow_custom_predicate(cmd):
            return True

        return self.allow_all
