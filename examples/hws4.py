# -*- coding: utf-8 -*-
# pylint: skip-file

"""Example of a 4-qubit phase function."""

from projectq.cengines import MainEngine
from projectq.libs.revkit import PhaseOracle
from projectq.meta import Compute, Uncompute
from projectq.ops import All, H, Measure, X


# phase function
def f(a, b, c, d):
    """Phase function."""
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
