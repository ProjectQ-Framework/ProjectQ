import copy
import math
import cmath
import numpy as np

from projectq.cengines import DecompositionRule
from projectq.ops import BasicGate, CNOT, Rz, DiagonalGate, Ph

# global and relative phase
def _basic_decomposition(phi1, phi2):
    return (phi1+phi2)/2, phi2-phi1


def _decompose_diagonal_gate(cmd):
    angles = cmd.gate.angles

    qureg = []
    for reg in cmd.qubits:
        qureg.extend(reg)

    N = len(angles)
    n = len(qureg)
    assert 1 << n == N

    print(angles)
    print("--")
    for k in range(n):
        length = N >> k
        rotations = []
        for i in range(0,length,2):
            angles[i//2], rot = _basic_decomposition(angles[i], angles[i+1])
            rotations.append(rot)
            print("rot {}".format(rot))
        print(rotations)
        _apply_uniformly_controlled_rotation(rotations, qureg[k:])
        print(angles)
        print(rotations)
        print("---")
    print(angles[0])
    Ph(angles[0]) | qureg[0]


# uniformly controlled rotation (one choice qubit)
def _decompose_rotation(phi1, phi2):
    return (phi1 + phi2) / 2, (phi1 - phi2) / 2

def _decompose_rotations(angles, a, b):
    N = b-a
    if N <= 1:
        return
    for i in range(a, a+N//2):
        angles[i], angles[i+N//2] = _decompose_rotation(angles[i], angles[i+N//2])
    _decompose_rotations(angles, a, a+N//2)
    _decompose_rotations_reversed(angles, a+N//2, b)

def _decompose_rotations_reversed(angles, a, b):
    N = b-a
    if N <= 1:
        return
    for i in range(a, a+N//2):
        angles[i+N//2], angles[i] = _decompose_rotation(angles[i], angles[i+N//2])
    _decompose_rotations(angles, a, a+N//2)
    _decompose_rotations_reversed(angles, a+N//2, b)


def _count_trailing_zero_bits(v):
    assert(v > 0)
    v = (v ^ (v - 1)) >> 1;
    c = 0
    while(v):
        v >>= 1;
        c += 1
    return c


def _apply_uniformly_controlled_rotation(angles, qureg):
    N = len(angles)
    n = len(qureg) - 1
    assert 1 << n == N
    assert N > 0

    _decompose_rotations(angles, 0, N)

    target = qureg[0]
    controls = qureg[1:]

    if N == 1:
        Rz(angles[0]) | target
        return

    for i in range(N-1):
        Rz(angles[i]) | target
        control = controls[_count_trailing_zero_bits(i+1)]
        CNOT | (control, target)
    Rz(angles[N-1]) | target
    CNOT | (controls[-1], target)

#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(DiagonalGate, _decompose_diagonal_gate)
]
