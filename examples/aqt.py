# -*- coding: utf-8 -*-
# pylint: skip-file

import matplotlib.pyplot as plt
import getpass

from projectq import MainEngine
from projectq.backends import AQTBackend
from projectq.libs.hist import histogram
from projectq.ops import Measure, Entangle, All
import projectq.setups.aqt


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


if __name__ == "__main__":
    # devices available to subscription:
    # aqt_simulator (11 qubits)
    # aqt_simulator_noise (11 qubits)
    # aqt_device (4 qubits)
    #
    # To get a subscription, create a profile at :
    # https://gateway-portal.aqt.eu/
    #
    device = None  # replace by the AQT device name you want to use
    token = None  # replace by the token given by AQT
    if token is None:
        token = getpass.getpass(prompt='AQT token > ')
    if device is None:
        device = getpass.getpass(prompt='AQT device > ')
    # create main compiler engine for the AQT back-end
    eng = MainEngine(
        AQTBackend(use_hardware=True, token=token, num_runs=200, verbose=False, device=device),
        engine_list=projectq.setups.aqt.get_engine_list(token=token, device=device),
    )
    # run the circuit and print the result
    print(run_entangle(eng))
