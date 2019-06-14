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

"""
Registers a decomposition for quantum amplitude amplification.

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

       def func_algorithm(system_qubits):
           All(H) | system_qubits

       def func_algorithm_inverse(system_qubits):
           All(H) | system_qubits

       def func_oracle(eng,system_qubits,control):
           # This oracle selects the state |010> as the one marked
           # Method taken form the Grover example
           with Compute(eng):
              All(X) | system_qubits[0::2]
           with Control(eng, system_qubits):
              X | control
           Uncompute(eng)

       system_qubits = eng.allocate_qureg(3)
       # Prepare the control qubit in the |-> state
       control = eng.allocate_qubit()
       X | control
       H | control

       # Creates the initial state form the Algorithm
       func_algorithm(system_qubits)
       # Apply Quantum Amplitude Amplification the correct number of times
       num_it = int(math.pi/4.*math.sqrt(1 << 3))
       with Loop(eng, num_it):
           QAA(func_algorithm, func_algorithm_inverse, func_oracle) | (system_qubits, control)

       All(Measure) | system_qubits

Attributes:
    func_algorithm: Algorithm that initialite the state and to be used in the QAA algorithm
    func_algorithm_inverse: inverse of the func_algorithm
    func_oracle: The Oracle that marks the state(s) as "good"
    system_qubits: the system we are interested on
    control: auxiliary qubit that helps to invert the amplitude of the "good" states

"""

import math
import numpy as np

from projectq.cengines import DecompositionRule
from projectq.meta import Control, Compute, Uncompute, CustomUncompute
from projectq.ops import X, Z, Ph, All

from projectq.ops import QAA


def _decompose_QAA(cmd):
    """ Decompose the Quantum Amplitude Apmplification algorithm as a gate. """
    eng = cmd.engine

    # System-qubit is the first qubit/qureg. Control qubit is the second qubit
    system_qubits = cmd.qubits[0]
    control = cmd.qubits[1]

    # The Oracle and the Algorithm
    Orcl = cmd.gate.oracle
    A = cmd.gate.algorithm
    A_inv = cmd.gate.algorithm_inverse

    # Apply the oracle to invert the amplitude of the good states, S_Chi
    Orcl(eng, system_qubits, control)

    # Apply the inversion of the Algorithm, the inversion of the aplitude of |0> and the Algorithm

    with Compute(eng):
        A_inv(eng, system_qubits)
        All(X) | system_qubits
    with Control(eng, system_qubits[0:-1]):
        Z | system_qubits[-1]
    with CustomUncompute(eng):
        All(X) | system_qubits
        A(eng, system_qubits)
    Ph(math.pi) | system_qubits[0]


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(QAA, _decompose_QAA)
]