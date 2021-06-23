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

"""Example of a basic Bernstein-Vazirani circuit using an IonQBackend."""

import getpass
import random

import matplotlib.pyplot as plt

import projectq.setups.ionq
from projectq import MainEngine
from projectq.backends import IonQBackend
from projectq.libs.hist import histogram
from projectq.ops import CX, All, Barrier, H, Measure, Z


def oracle(qureg, input_size, s):
    """Apply the 'oracle'."""

    for bit in range(input_size):
        if s[input_size - 1 - bit] == '1':
            CX | (qureg[bit], qureg[input_size])


def run_bv_circuit(eng, input_size, s_int):
    s = ('{0:0' + str(input_size) + 'b}').format(s_int)
    print("Secret string: ", s)
    print("Number of qubits: ", str(input_size + 1))
    circuit = eng.allocate_qureg(input_size + 1)
    All(H) | circuit
    Z | circuit[input_size]

    Barrier | circuit

    oracle(circuit, input_size, s)

    Barrier | circuit

    qubits = circuit[:input_size]
    All(H) | qubits
    All(Measure) | qubits
    eng.flush()

    # return a random answer from our results
    histogram(eng.backend, qubits)
    plt.show()

    # return a random answer from our results
    probabilities = eng.backend.get_probabilities(qubits)
    random_answer = random.choice(list(probabilities.keys()))
    print("Probability of getting correct string: ", probabilities[s[::-1]])
    return [int(s) for s in random_answer]


if __name__ == '__main__':
    token = None
    device = None
    if token is None:
        token = getpass.getpass(prompt='IonQ apiKey > ')
    if device is None:
        device = input('IonQ device > ')

    # create main compiler engine for the IonQ back-end
    backend = IonQBackend(
        use_hardware=True,
        token=token,
        num_runs=1,
        verbose=False,
        device=device,
    )
    engine_list = projectq.setups.ionq.get_engine_list(
        token=token,
        device=device,
    )
    engine = MainEngine(backend, engine_list)

    # run the circuit and print the result
    print(run_bv_circuit(engine, 3, 3))
