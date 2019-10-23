#   Copyright 2019 ProjectQ-Framework (www.projectq.ch)
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


class QAA(BasicGate):
    """
    Quantum Aplitude Aplification gate.

    (Quick reference https://en.wikipedia.org/wiki/Amplitude_amplification.
    Complete reference G. Brassard, P. Hoyer, M. Mosca, A. Tapp (2000)
    Quantum Amplitude Amplification and Estimation
    https://arxiv.org/abs/quant-ph/0005055)

    Quantum Amplitude Amplification (QAA) executes the algorithm, but not
    the final measurement required to obtain the marked state(s) with high
    probability. The starting state on wich the QAA algorithm is executed
    is the one resulting of aplying the Algorithm on the |0> state.

    Example:
        .. code-block:: python

           def func_algorithm(eng,system_qubits):
               All(H) | system_qubits

           def func_oracle(eng,system_qubits,qaa_ancilla):
               # This oracle selects the state |010> as the one marked
               with Compute(eng):
                  All(X) | system_qubits[0::2]
               with Control(eng, system_qubits):
                  X | qaa_ancilla
               Uncompute(eng)

           system_qubits = eng.allocate_qureg(3)
           # Prepare the qaa_ancilla qubit in the |-> state
           qaa_ancilla = eng.allocate_qubit()
           X | qaa_ancilla
           H | qaa_ancilla

           # Creates the initial state form the Algorithm
           func_algorithm(eng, system_qubits)
           # Apply Quantum Amplitude Amplification the correct number of times
           num_it = int(math.pi/4.*math.sqrt(1 << 3))
           with Loop(eng, num_it):
               QAA(func_algorithm, func_oracle) | (system_qubits, qaa_ancilla)

           All(Measure) | system_qubits

    Warning:
        No qubit allocation/deallocation may take place during the call
        to the defined Algorithm :code:`func_algorithm`

    Attributes:
        func_algorithm: Algorithm that initialite the state and to be used
                        in the QAA algorithm
        func_oracle: The Oracle that marks the state(s) as "good"
        system_qubits: the system we are interested on
        qaa_ancilla: auxiliary qubit that helps to invert the amplitude of the
                     "good" states

    """
    def __init__(self, algorithm, oracle):
        BasicGate.__init__(self)
        self.algorithm = algorithm
        self.oracle = oracle

    def __str__(self):
        return 'QAA(Algorithm = {0}, Oracle = {1})'.format(
                str(self.algorithm.__name__), str(self.oracle.__name__))
