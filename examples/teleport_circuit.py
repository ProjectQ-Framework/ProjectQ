import projectq.setups.default
from projectq import MainEngine
from projectq.backends import CircuitDrawer

import teleport

if __name__ == "__main__":
    # create a main compiler engine with a simulator backend:
    drawing_engine = CircuitDrawer()
    locations = {0: 1, 1: 2, 2: 0}
    drawing_engine.set_qubit_locations(locations)
    eng = MainEngine(drawing_engine)

    # we just want to draw the teleportation circuit
    def create_state(eng, qb):
        pass

    # run the teleport and then, let Bob try to uncompute his qubit:
    teleport.run_teleport(eng, create_state, verbose=False)

    # print latex code to draw the circuit:
    print(drawing_engine.get_latex())
