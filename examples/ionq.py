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

"""Example of a basic entangling operation using an IonQBackend."""

import getpass

import matplotlib.pyplot as plt

import projectq.setups.ionq
from projectq import MainEngine
from projectq.backends import IonQBackend
from projectq.libs.hist import histogram
from projectq.ops import All, Entangle, Measure


def run_entangle(eng, num_qubits=3):
    """
    Runs an entangling operation on the provided compiler engine.

    Args:
        eng (MainEngine): Main compiler engine to use.
        num_qubits (int): Number of qubits to entangle.

    Returns:
        measurement (list<int>): List of measurement outcomes.
    """
    # allocate the quantum register to entangle
    qureg = eng.allocate_qureg(num_qubits)

    # entangle the qureg
    Entangle | qureg

    # measure; should be all-0 or all-1
    All(Measure) | qureg

    # run the circuit
    eng.flush()

    # access the probabilities via the back-end:
    # results = eng.backend.get_probabilities(qureg)
    # for state in results:
    #     print("Measured {} with p = {}.".format(state, results[state]))
    # or plot them directly:
    histogram(eng.backend, qureg)
    plt.show()

    # return one (random) measurement outcome.
    return [int(q) for q in qureg]


if __name__ == '__main__':
    token = None
    device = None
    if token is None:
        token = getpass.getpass(prompt='IonQ apiKey > ')
    if device is None:
        device = input('IonQ device > ')

    # create an IonQBackend
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
    print(run_entangle(engine))
