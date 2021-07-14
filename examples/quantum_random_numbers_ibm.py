# -*- coding: utf-8 -*-
# pylint: skip-file

"""Example of a simple quantum random number generator using IBM's API."""

import projectq.setups.ibm
from projectq import MainEngine
from projectq.backends import IBMBackend
from projectq.ops import H, Measure

# create a main compiler engine
eng = MainEngine(IBMBackend(), engine_list=projectq.setups.ibm.get_engine_list())

# allocate one qubit
q1 = eng.allocate_qubit()

# put it in superposition
H | q1

# measure
Measure | q1

eng.flush()
# print the result:
print("Measured: {}".format(int(q1)))
