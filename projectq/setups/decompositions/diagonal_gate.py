from projectq.cengines import DecompositionRule
from projectq.meta import Control
from projectq.ops import DiagonalGate
from projectq.libs.isometries import _apply_diagonal_gate


def _decompose_diagonal_gate(cmd):
    diag = cmd.gate
    decomposition = diag.decomposition
    ctrl = cmd.control_qubits

    qureg = []
    for reg in cmd.qubits:
        qureg.extend(reg)

    with Control(cmd.engine, ctrl):
        _apply_diagonal_gate(decomposition, qureg)


all_defined_decomposition_rules = [
    DecompositionRule(DiagonalGate, _decompose_diagonal_gate)
]
