# -*- coding: utf-8 -*-
# pylint: skip-file

from projectq.cengines import MainEngine
from projectq.ops import All, H, X, Measure
from projectq.meta import Compute, Uncompute, Dagger
from projectq.libs.revkit import PhaseOracle, PermutationOracle

import revkit


# phase function
def f(a, b, c, d, e, f):
    return (a and b) ^ (c and d) ^ (e and f)


# permutation
pi = [0, 2, 3, 5, 7, 1, 4, 6]

eng = MainEngine()
qubits = eng.allocate_qureg(6)
x = qubits[::2]  # qubits on odd lines
y = qubits[1::2]  # qubits on even lines

# circuit
with Compute(eng):
    All(H) | qubits
    All(X) | [x[0], x[1]]
    PermutationOracle(pi) | y
PhaseOracle(f) | qubits
Uncompute(eng)

with Compute(eng):
    with Dagger(eng):
        PermutationOracle(pi, synth=revkit.dbs) | x
PhaseOracle(f) | qubits
Uncompute(eng)

All(H) | qubits

All(Measure) | qubits

# measurement result
print("Shift is {}".format(sum(int(q) << i for i, q in enumerate(qubits))))
