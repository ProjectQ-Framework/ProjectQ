import math
import cmath
import numpy as np

from projectq.cengines import DecompositionRule
from projectq.ops import UniformlyControlledGate, BasicGate, H, CNOT, Rz, DiagonalGate
from projectq.isometries import _apply_uniformly_controlled_gate

def _decompose_uniformly_controlled_gate(cmd):
    ucg = cmd.gate
    if not ucg.decomposed:
        ucg.decompose()
    decomposition = ucg.decomposition

    choice_reg = cmd.qubits[0]
    target = cmd.qubits[1]

    reduced = ucg.up_to_diagonal
    _apply_uniformly_controlled_gate(decomposition, target, choice_reg, reduced)


all_defined_decomposition_rules = [
    DecompositionRule(UniformlyControlledGate, _decompose_uniformly_controlled_gate)
]
