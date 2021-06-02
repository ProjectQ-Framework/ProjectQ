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
    qubits = circuit[:-1]
    output = circuit[input_size]

    H | output
    Z | output
    All(H) | qubits

    Barrier | (*qubits, output)

    oracle(circuit, input_size, s)

    Barrier | (*qubits, output)

    All(H) | qubits
    All(Measure) | qubits
    eng.flush()

    # return a random answer from our results
    histogram(eng.backend, circuit)
    plt.show()

    # return a random answer from our results
    probabilities = eng.backend.get_probabilities(circuit)
    random_answer = random.choice(list(probabilities.keys()))
    print("Probability of getting correct string: ", probabilities[s[::-1] + '0'])
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
