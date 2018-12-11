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
            On hardware backends this operation needs to automatically
            construct a circuit that prepares the given state. This typically
            can be expected to work only for relatively simple states or such
            of few qubits.

        Args:
            final_state(list[complex]): wavefunction of the desired
                                        quantum state. len(final_state) must
                                        be 2**len(qureg). Must be normalized!

        Note:
            final_state[k] is taken to be the amplitude of the computational
            basis state whose string is equal to the binary representation
            of k.
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
    def __init__(self, basis_state):
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
            basis_state(list[int]): array of bits of binary string identifying
                                    the desired computational basis state of
                                    length len(qureg). Must conatin only 0s
                                    and 1s!
        """
        self.basis_state = list(basis_state)

    def __str__(self):
        return "FlipBits"

    def __or__(self, qubits):
        for qureg in self.make_tuple_of_qureg(qubits):
            for i, qubit in enumerate(qureg):
                if self.basis_state[i] == 1:
                    XGate() | qubit

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.basis_state == other.basis_state
        else:
            return False

    def __hash__(self):
        return hash("FlipBits(" + str(self.basis_state) + ")")
