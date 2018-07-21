import projectq.setups.ibm16
from projectq.backends import IBMBackend
from projectq.ops import All, Entangle, Measure
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
    qureg = eng.allocate_qureg(8)

    Entangle | qureg

    # measure; should be all-0 or all-1
    All(Measure) | qureg

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
                                verbose=False, device='ibmqx5'),
                     engine_list=projectq.setups.ibm16.get_engine_list())
    # run the circuit and print the result
    print(run_test(eng))
