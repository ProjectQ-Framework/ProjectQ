# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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
# pylint: skip-file

"""Example of using the UnitarySimulator."""


import numpy as np

from projectq.backends import UnitarySimulator
from projectq.cengines import MainEngine
from projectq.meta import Control
from projectq.ops import All, X, QFT, Measure, CtrlAll


def run_circuit(eng, n_qubits, circuit_num, gate_after_measure=False):
    """Run a quantum circuit demonstrating the capabilities of the UnitarySimulator."""
    qureg = eng.allocate_qureg(n_qubits)

    if circuit_num == 1:
        All(X) | qureg
    elif circuit_num == 2:
        X | qureg[0]
        with Control(eng, qureg[:2]):
            All(X) | qureg[2:]
    elif circuit_num == 3:
        with Control(eng, qureg[:2], ctrl_state=CtrlAll.Zero):
            All(X) | qureg[2:]
    elif circuit_num == 4:
        QFT | qureg

    eng.flush()
    All(Measure) | qureg

    if gate_after_measure:
        QFT | qureg
    eng.flush()
    All(Measure) | qureg


def main():
    """Definition of the main function of this example."""
    # Create a MainEngine with a unitary simulator backend
    eng = MainEngine(backend=UnitarySimulator())

    n_qubits = 3

    # Run out quantum circuit
    #   1 - circuit applying X on all qubits
    #   2 - circuit applying an X gate followed by a controlled-X gate
    #   3 - circuit applying a off-controlled-X gate
    #   4 - circuit applying a QFT on all qubits (QFT will get decomposed)
    run_circuit(eng, n_qubits, 3, gate_after_measure=True)

    # Output the unitary transformation of the circuit
    print('The unitary of the circuit is:')
    print(eng.backend.unitary)

    # Output the final state of the qubits (assuming they all start in state |0>)
    print('The final state of the qubits is:')
    print(eng.backend.unitary @ np.array([1] + ([0] * (2 ** n_qubits - 1))))
    print('\n')

    # Show the unitaries separated by measurement:
    for history in eng.backend.history:
        print('Previous unitary is: \n', history, '\n')


if __name__ == '__main__':
    main()
