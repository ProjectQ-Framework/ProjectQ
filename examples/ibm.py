import projectq.setups.ibm
from projectq.backends import IBMBackend
from projectq.ops import Measure, Entangle, All
from projectq import MainEngine
import getpass


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
    results = eng.backend.get_probabilities(qureg)
    for state in results:
        print("Measured {} with p = {}.".format(state, results[state]))

    # return one (random) measurement outcome.
    return [int(q) for q in qureg]


if __name__ == "__main__":
    #devices commonly available :
    #ibmq_16_melbourne (15 qubit)
    #ibmq_essex (5 qubit)
    #ibmq_qasm_simulator (32 qubits)
    device = None #replace by the IBM device name you want to use
    token = None  #replace by the token given by IBMQ
    if token is None:
        token = getpass.getpass(prompt='IBM Q token > ')
    if device is None:
        token = getpass.getpass(prompt='IBM device > ')
    # create main compiler engine for the IBM back-end
    eng = MainEngine(IBMBackend(use_hardware=True, token=token num_runs=1024,
                                verbose=False, device=device),
                     engine_list=projectq.setups.ibm.get_engine_list(token=token, device=device))
    # run the circuit and print the result
    print(run_entangle(eng))
