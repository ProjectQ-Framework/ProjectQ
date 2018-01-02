import projectq.setups.ibm16
from projectq.backends import IBMBackend
from projectq.ops import Measure, CNOT, H, All
from projectq import MainEngine


def run_test(eng):
    """
    Runs a test circuit on the provided compiler engine.

    Args:
        eng (MainEngine): Main compiler engine to use.

    Returns:
        measurement (list<int>): List of measurement outcomes.
    """
    # allocate the quantum register to entangle
    qureg = eng.allocate_qureg(16)

    interactions = [(1, 0), (1, 2), (2, 3), (3, 4), (5, 4), (6, 5), (6, 7),
                    (8, 7), (9, 8), (9, 10), (11, 10), (12, 11), (12, 13),
                    (13, 14), (15, 14)]
    H | qureg[0]
    for e in interactions:
        flip = e[0] > e[1]
        if flip:
            All(H) | [qureg[e[0]], qureg[e[1]]]
            CNOT | (qureg[e[0]], qureg[e[1]])
            All(H) | [qureg[e[0]], qureg[e[1]]]
        else:
            CNOT | (qureg[e[0]], qureg[e[1]])

    # measure; should be all-0 or all-1
    Measure | qureg

    # run the circuit
    eng.flush()

    # access the probabilities via the back-end:
    results = eng.backend.get_probabilities(qureg)
    for state, probability in sorted(list(results.items())):
        print("Measured {} with p = {}.".format(state, probability))

    # return one (random) measurement outcome.
    return [int(q) for q in qureg]


if __name__ == "__main__":
    # create main compiler engine for the 16-qubit IBM back-end
    eng = MainEngine(IBMBackend(use_hardware=True, num_runs=1024,
                                verbose=False, device='ibmqx5'))
    # run the circuit and print the result
    print(run_test(eng))
