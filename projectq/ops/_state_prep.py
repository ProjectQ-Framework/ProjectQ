#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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

from ._basics import BasicGate


class StatePreparation(BasicGate):
    """
    Gate for transforming qubits in state |0> to any desired quantum state.
    """
    def __init__(self, final_state):
        """
        Initialize StatePreparation gate.

        Example:
            .. code-block:: python

                qureg = eng.allocate_qureg(2)
                StatePreparation([0.5, -0.5j, -0.5, 0.5]) | qureg

        Note:
            final_state[k] is taken to be the amplitude of the computational
            basis state whose string is equal to the binary representation
            of k.

        Args:
            final_state(list[complex]): wavefunction of the desired
                                        quantum state. len(final_state) must
                                        be 2**len(qureg). Must be normalized!
        """
        BasicGate.__init__(self)
        self.final_state = list(final_state)

    def __str__(self):
        return "StatePreparation"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.final_state == other.final_state
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash("StatePreparation(" + str(self.final_state) + ")")
