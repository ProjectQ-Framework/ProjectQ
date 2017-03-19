import projectq.setups.default
from projectq.ops import H, X, Z, Rz, CNOT, Measure
from projectq import MainEngine
from projectq.meta import Dagger, Control


def create_bell_pair(eng):
    """
    Returns a Bell-pair (two qubits in state :math:`|A\rangle \otimes |B
    \rangle = \frac 1{\sqrt 2} \left( |0\rangle\otimes|0\rangle + |1\rangle
    \otimes|1\rangle \right)`).

    Args:
        eng (MainEngine): MainEngine from which to allocate the qubits.

    Returns:
        bell_pair (tuple<Qubits>): The Bell-pair.
    """
    b1 = eng.allocate_qubit()
    b2 = eng.allocate_qubit()

    H | b1
    CNOT | (b1, b2)

    return b1, b2


def run_teleport(eng, state_creation_function, verbose=False):
    """
    Runs quantum teleportation on the provided main compiler engine.

    Creates a state from |0> using the state_creation_function, teleports this
    state to Bob who then tries to uncompute his qubit using the inverse of
    the state_creation_function. If successful, deleting the qubit won't raise
    an error in the underlying Simulator back-end (else it will).

    Args:
        eng (MainEngine): Main compiler engine to run the circuit on.
        state_creation_function (function): Function which accepts the main
            engine and a qubit in state |0>, which it then transforms to the
            state that Alice would like to send to Bob.
        verbose (bool): If True, info messages will be printed.

    """
    # make a Bell-pair
    b1, b2 = create_bell_pair(eng)

    # Alice creates a nice state to send
    psi = eng.allocate_qubit()
    if verbose:
        print("Alice is creating her state from scratch, i.e., |0>.")
    state_creation_function(eng, psi)

    # entangle it with Alice's b1
    CNOT | (psi, b1)
    if verbose:
        print("Alice entangled her qubit with her share of the Bell-pair.")

    # measure two values (once in Hadamard basis) and send the bits to Bob
    H | psi
    Measure | (psi, b1)
    msg_to_bob = [int(psi), int(b1)]
    if verbose:
        print("Alice is sending the message {} to Bob.".format(msg_to_bob))

    # Bob may have to apply up to two operation depending on the message sent
    # by Alice:
    with Control(eng, b1):
        X | b2
    with Control(eng, psi):
        Z | b2

    # try to uncompute the psi state
    if verbose:
        print("Bob is trying to uncompute the state.")
    with Dagger(eng):
        state_creation_function(eng, b2)

    # check whether the uncompute was successful. The simulator only allows to
    # delete qubits which are in a computational basis state.
    del b2
    eng.flush()

    if verbose:
        print("Bob successfully arrived at |0>")


if __name__ == "__main__":
    # create a main compiler engine with a simulator backend:
    eng = MainEngine()

    # define our state-creation routine, which transforms a |0> to the state
    # we would like to send. Bob can then try to uncompute it and, if he
    # arrives back at |0>, we know that the teleportation worked.
    def create_state(eng, qb):
        H | qb
        Rz(1.21) | qb

    # run the teleport and then, let Bob try to uncompute his qubit:
    run_teleport(eng, create_state, verbose=True)
