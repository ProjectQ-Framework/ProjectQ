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
