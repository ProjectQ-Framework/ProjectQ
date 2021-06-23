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

"""Example of a basic 'half-adder' circuit using an IonQBackend"""

import getpass
import random

import matplotlib.pyplot as plt

import projectq.setups.default
import projectq.setups.ionq
from projectq import MainEngine
from projectq.backends import IonQBackend
from projectq.libs.hist import histogram
from projectq.ops import CNOT, All, Barrier, Measure, Toffoli, X


def run_half_adder(eng):
    # allocate the quantum register to entangle
    circuit = eng.allocate_qureg(4)
    qubit1, qubit2, qubit3, qubit4 = circuit
    result_qubits = [qubit3, qubit4]

    # X gates on the first two qubits
    All(X) | [qubit1, qubit2]

    # Barrier
    Barrier | circuit

    # Cx gates
    CNOT | (qubit1, qubit3)
    CNOT | (qubit2, qubit3)

    # CCNOT
    Toffoli | (qubit1, qubit2, qubit4)

    # Barrier
    Barrier | circuit

    # Measure result qubits
    All(Measure) | result_qubits

    # Flush the circuit (this submits a job to the IonQ API)
    eng.flush()

    # Show the histogram
    histogram(eng.backend, result_qubits)
    plt.show()

    # return a random answer from our results
    probabilities = eng.backend.get_probabilities(result_qubits)
    random_answer = random.choice(list(probabilities.keys()))
    return [int(s) for s in random_answer]


if __name__ == '__main__':
    token = None
    device = None
    if token is None:
        token = getpass.getpass(prompt='IonQ apiKey > ')
    if device is None:
        device = input('IonQ device > ')

    backend = IonQBackend(
        use_hardware=True,
        token=token,
        num_runs=200,
        verbose=True,
        device=device,
    )
    engine_list = projectq.setups.ionq.get_engine_list(
        token=token,
        device=device,
    )
    engine = MainEngine(backend, engine_list)
    # run the circuit and print the result
    print(run_half_adder(engine))
