import math
import cmath
import numpy as np

from projectq.cengines import DecompositionRule
from projectq.ops import UniformlyControlledGate, BasicGate, H, CNOT, Rz


def _count_trailing_zero_bits(v):
    assert(v > 0)
    v = (v ^ (v - 1)) >> 1;
    c = 0
    while(v):
        v >>= 1;
        c += 1
    return c


def _decompose_uniformly_controlled_gate(cmd):
    gates = cmd.gate.decomposed_gates
    target = cmd.qubits[1]
    choice_reg = cmd.qubits[0]

    for i in range(len(gates) - 1):
        gates[i] | target
        control_index = _count_trailing_zero_bits(i+1)
        choice = choice_reg[control_index]
        CNOT | (choice, target)
        Rz(-np.pi/2) | choice
    gates[-1] | target


all_defined_decomposition_rules = [
    DecompositionRule(UniformlyControlledGate, _decompose_uniformly_controlled_gate)
]
