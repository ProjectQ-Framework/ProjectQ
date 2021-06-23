# -*- coding: utf-8 -*-
# pylint: skip-file

from projectq.cengines import MainEngine
from projectq.ops import All, H, X, Measure
from projectq.meta import Compute, Uncompute
from projectq.libs.revkit import PhaseOracle


# phase function
def f(a, b, c, d):
    return (a and b) ^ (c and d)


eng = MainEngine()
x1, x2, x3, x4 = qubits = eng.allocate_qureg(4)

with Compute(eng):
    All(H) | qubits
    X | x1
PhaseOracle(f) | qubits
Uncompute(eng)

PhaseOracle(f) | qubits
All(H) | qubits
All(Measure) | qubits

eng.flush()

print("Shift is {}".format(8 * int(x4) + 4 * int(x3) + 2 * int(x2) + int(x1)))
