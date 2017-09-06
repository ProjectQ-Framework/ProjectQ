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

"""TestEngine and DummyEngine."""


from copy import deepcopy
from projectq.cengines import BasicEngine
from projectq.ops import FlushGate, Allocate, Deallocate


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
