# try:
#     from ._cppsim import Simulator as SimulatorBackend
# except ImportError:
#     from ._pysim import Simulator as SimulatorBackend
#
import numpy as np

from projectq.ops import Rz, X, CNOT, UniformlyControlledGate, DiagonalGate, Ph
from projectq.meta import Dagger, Control, Compute, Uncompute

def _count_trailing_zero_bits(v):
    assert v > 0
    v = (v ^ (v - 1)) >> 1;
    c = 0
    while(v):
        v >>= 1;
        c += 1
    return c

def _apply_diagonal_gate(decomposition, qureg):
    n = len(qureg)
    assert n == len(decomposition) - 1

    for i in range(n):
        _apply_uniformly_controlled_rotation(decomposition[i], qureg[i:])

    p = decomposition[-1][0]
    Ph(p) | qureg[0]

def _apply_uniformly_controlled_rotation(angles, qureg):
    N = len(angles)
    n = len(qureg) - 1
    assert 1 << n == N
    assert N > 0

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


def _apply_uniformly_controlled_gate(decomposition, target, choice_reg, up_to_diagonal):
    gates, phases = decomposition

    for i in range(len(gates) - 1):
        gates[i] | target
        control_index = _count_trailing_zero_bits(i+1)
        choice = choice_reg[control_index]
        CNOT | (choice, target)
        Rz(-np.pi/2) | choice
    gates[-1] | target

    if up_to_diagonal:
        return

    diagonal = DiagonalGate(phases=phases)
    diagonal | (target, choice_reg)

def _apply_mask(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 0:
            X | qureg[pos]

def _apply_isometry(decomposition, qureg):
    reductions, phases = decomposition
    n = len(qureg)
    with Dagger(qureg[0].engine):
        for k in range(len(reductions)):
            for s in range(n):
                mcg, ucg = reductions[k][s]
                # apply MCG
                mask = b(k,s) + (a(k,s+1) << s)
                qubits = qureg[:s]+qureg[s+1:]
                e = qureg[0].engine
                with Compute(e):
                    _apply_mask(mask,qubits)
                with Control(e, qubits):
                    mcg | qureg[s]
                Uncompute(e)
                #apply UCG
                if len(ucg) > 0:
                    UCG = UniformlyControlledGate(ucg, up_to_diagonal=True)
                    UCG | (qureg[s+1:], qureg[s])
        diagonal = DiagonalGate(phases=phases)
        diagonal | qureg

def a(k,s):
    return k >> s

def b(k,s):
    return k - (a(k,s) << s)
