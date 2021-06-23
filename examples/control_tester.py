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


from projectq.cengines import MainEngine
from projectq.meta import Control
from projectq.ops import All, X, Measure, CtrlAll


def run_circuit(eng, circuit_num):
    qubit = eng.allocate_qureg(2)
    ctrl_fail = eng.allocate_qureg(3)
    ctrl_success = eng.allocate_qureg(3)

    if circuit_num == 1:
        with Control(eng, ctrl_fail):
            X | qubit[0]
        All(X) | ctrl_success
        with Control(eng, ctrl_success):
            X | qubit[1]

    elif circuit_num == 2:
        All(X) | ctrl_fail
        with Control(eng, ctrl_fail, ctrl_state=CtrlAll.Zero):
            X | qubit[0]
        with Control(eng, ctrl_success, ctrl_state=CtrlAll.Zero):
            X | qubit[1]

    elif circuit_num == 3:
        All(X) | ctrl_fail
        with Control(eng, ctrl_fail, ctrl_state='101'):
            X | qubit[0]

        X | ctrl_success[0]
        X | ctrl_success[2]
        with Control(eng, ctrl_success, ctrl_state='101'):
            X | qubit[1]

    elif circuit_num == 4:
        All(X) | ctrl_fail
        with Control(eng, ctrl_fail, ctrl_state=5):
            X | qubit[0]

        X | ctrl_success[0]
        X | ctrl_success[2]
        with Control(eng, ctrl_success, ctrl_state=5):
            X | qubit[1]

    All(Measure) | qubit
    All(Measure) | ctrl_fail
    All(Measure) | ctrl_success
    eng.flush()
    return qubit, ctrl_fail, ctrl_success


if __name__ == '__main__':
    # Create a MainEngine with a unitary simulator backend
    eng = MainEngine()

    # Run out quantum circuit
    #   1 - Default behaviour of the control: all control qubits should be 1
    #   2 - Off-control: all control qubits should remain 0
    #   3 - Specific state given by a string
    #   4 - Specific state given by an integer

    qubit, ctrl_fail, ctrl_success = run_circuit(eng, 4)

    # Measured value of the failed qubit should be 0 in all cases
    print('The final value of the qubit with failed control is:')
    print(int(qubit[0]))
    print('with the state of control qubits are:')
    print([int(qubit) for qubit in ctrl_fail], '\n')

    # Measured value of the success qubit should be 1 in all cases
    print('The final value of the qubit with successful control is:')
    print(int(qubit[1]))
    print('with the state of control qubits are:')
    print([int(qubit) for qubit in ctrl_success], '\n')
