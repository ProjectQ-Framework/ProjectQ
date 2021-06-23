# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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

"""Functions to plot a histogram of measured data"""

from __future__ import print_function
import matplotlib.pyplot as plt

from projectq.backends import Simulator


def histogram(backend, qureg):
    """
    Make a measurement outcome probability histogram for the given qubits.

    Args:
        backend (BasicEngine): A ProjectQ backend
        qureg (list of qubits and/or quregs): The qubits,
            for which to make the histogram

    Returns:
        A tuple (fig, axes, probabilities), where:
        fig: The histogram as figure
        axes: The axes of the histogram
        probabilities (dict): A dictionary mapping outcomes as string
            to their probabilities

    Note:
        Don't forget to call eng.flush() before using this function.
    """
    qubit_list = []
    for qb in qureg:
        if isinstance(qb, list):
            qubit_list.extend(qb)
        else:
            qubit_list.append(qb)

    if len(qubit_list) > 5:
        print('Warning: For {0} qubits there are 2^{0} different outcomes'.format(len(qubit_list)))
        print("The resulting histogram may look bad and/or take too long.")
        print("Consider calling histogram() with a sublist of the qubits.")

    if hasattr(backend, 'get_probabilities'):
        probabilities = backend.get_probabilities(qureg)
    elif isinstance(backend, Simulator):
        outcome = [0] * len(qubit_list)
        n_outcomes = 1 << len(qubit_list)
        probabilities = {}
        for i in range(n_outcomes):
            for pos in range(len(qubit_list)):
                if (1 << pos) & i:
                    outcome[pos] = 1
                else:
                    outcome[pos] = 0
            probabilities[''.join([str(bit) for bit in outcome])] = backend.get_probability(outcome, qubit_list)
    else:
        raise RuntimeError('Unable to retrieve probabilities from backend')

    # Empirical figure size for up to 5 qubits
    fig, axes = plt.subplots(figsize=(min(21.2, 2 + 0.6 * (1 << len(qubit_list))), 7))
    names = list(probabilities.keys())
    values = list(probabilities.values())
    axes.bar(names, values)
    fig.suptitle('Measurement Probabilities')
    return (fig, axes, probabilities)
