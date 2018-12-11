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

from ._basics import BasicGate, SelfInverseGate
from ._gates import XGate

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

class FlipBits(SelfInverseGate):
    """
    Gate for transforming qubits in state |0> to any computational basis state
    """
    def __init__(self, bits_to_flip):
        """
        Initialize FlipBits gate.

        Example:
            .. code-block:: python

                qureg = eng.allocate_qureg(2)
                FlipBits([0, 1]) | qureg

        Note:
            The amplitude of state k is final_state[k]. When the state k is
            written in binary notation, then qureg[0] denotes the qubit
            whose state corresponds to the least significant bit of k.

        Args:
            bits_to_flip(list[int]|list[bool]|str): array of 0/1, True/False or
                                    string of 0/1 identifying the qubits to flip
                                    of length len(qureg).
        """
        if isinstance(bits_to_flip, str):
            self.bits_to_flip = list([ c != "0" for c in bits_to_flip])
        else:
            self.bits_to_flip = list(bits_to_flip)

    def __str__(self):
        return "FlipBits"

    def __or__(self, qubits):
        for qureg in self.make_tuple_of_qureg(qubits):
            for i, qubit in enumerate(qureg):
                if self.bits_to_flip[i]:
                    XGate() | qubit

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.bits_to_flip == other.bits_to_flip
        else:
            return False

    def __hash__(self):
        return hash("FlipBits(" + str(self.bits_to_flip) + ")")
