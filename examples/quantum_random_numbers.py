# -*- coding: utf-8 -*-
# pylint: skip-file

"""Example of a simple quantum random number generator."""

from projectq import MainEngine
from projectq.ops import H, Measure

# create a main compiler engine
eng = MainEngine()

# allocate one qubit
q1 = eng.allocate_qubit()

# put it in superposition
H | q1

# measure
Measure | q1

eng.flush()
# print the result:
print("Measured: {}".format(int(q1)))
