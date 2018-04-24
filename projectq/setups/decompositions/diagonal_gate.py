import copy
import math
import cmath
import numpy as np

from projectq.cengines import DecompositionRule
from projectq.ops import BasicGate, CNOT, Rz, DiagonalGate, Ph
from projectq.isometries import _apply_diagonal_gate

def _decompose_diagonal_gate(cmd):
    diag = cmd.gate
    if not diag.decomposed:
        diag.decompose()
    decomposition = diag.decomposition

    qureg = []
    for reg in cmd.qubits:
        qureg.extend(reg)

    _apply_diagonal_gate(decomposition, qureg)


all_defined_decomposition_rules = [
    DecompositionRule(DiagonalGate, _decompose_diagonal_gate)
]
