import math

from projectq import MainEngine
from projectq.ops import H, Z, X, Measure, All
from projectq.meta import Loop, Compute, Uncompute, Control


def run_grover(eng, n, oracle):
    """
    Runs Grover's algorithm on n qubit using the provided quantum oracle.

    Args:
        eng (MainEngine): Main compiler engine to run Grover on.
        n (int): Number of bits in the solution.
        oracle (function): Function accepting the engine, an n-qubit register,
            and an output qubit which is flipped by the oracle for the correct
            bit string.

    Returns:
        solution (list<int>): Solution bit-string.
    """
    x = eng.allocate_qureg(n)

    # start in uniform superposition
    All(H) | x

    # number of iterations we have to run:
    num_it = int(math.pi/4.*math.sqrt(1 << n))

    # prepare the oracle output qubit (the one that is flipped to indicate the
    # solution. start in state 1/sqrt(2) * (|0> - |1>) s.t. a bit-flip turns
    # into a (-1)-phase.
    oracle_out = eng.allocate_qubit()
    X | oracle_out
    H | oracle_out

    # run num_it iterations
    with Loop(eng, num_it):
        # oracle adds a (-1)-phase to the solution
        oracle(eng, x, oracle_out)

        # reflection across uniform superposition
        with Compute(eng):
            All(H) | x
            All(X) | x

        with Control(eng, x[0:-1]):
            Z | x[-1]

        Uncompute(eng)

    Measure | x
    Measure | oracle_out

    eng.flush()
    # return result
    return [int(qubit) for qubit in x]


def alternating_bits_oracle(eng, qubits, output):
    """
    Marks the solution string 1,0,1,0,...,0,1 by flipping the output qubit,
    conditioned on qubits being equal to the alternating bit-string.

    Args:
        eng (MainEngine): Main compiler engine the algorithm is being run on.
        qubits (Qureg): n-qubit quantum register Grover search is run on.
        output (Qubit): Output qubit to flip in order to mark the solution.
    """
    with Compute(eng):
        All(X) | qubits[1::2]
    with Control(eng, qubits):
        X | output
    Uncompute(eng)


if __name__ == "__main__":
    eng = MainEngine()  # use default compiler engine
    # run Grover search to find a 7-bit solution
    print(run_grover(eng, 7, alternating_bits_oracle))
