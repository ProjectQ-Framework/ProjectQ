# -*- coding: utf-8 -*-
# pylint: skip-file

"""Example if drawing of a quantum teleportation circuit."""

import teleport

from projectq import MainEngine
from projectq.backends import CircuitDrawer

if __name__ == "__main__":
    # create a main compiler engine with a simulator backend:
    drawing_engine = CircuitDrawer()
    locations = {0: 1, 1: 2, 2: 0}
    drawing_engine.set_qubit_locations(locations)
    eng = MainEngine(drawing_engine)

    # we just want to draw the teleportation circuit
    def create_state(eng, qb):
        """Create a quantum state."""

    # run the teleport and then, let Bob try to uncompute his qubit:
    teleport.run_teleport(eng, create_state, verbose=False)

    # print latex code to draw the circuit:
    print(drawing_engine.get_latex())
