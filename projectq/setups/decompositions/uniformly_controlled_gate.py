from projectq.cengines import DecompositionRule
from projectq.ops import UniformlyControlledGate
from projectq.isometries import _apply_uniformly_controlled_gate

def _decompose_uniformly_controlled_gate(cmd):
    ucg = cmd.gate

    decomposition = ucg.decomposition
    choice_reg = cmd.qubits[0]
    target = cmd.qubits[1]
    up_to_diagonal = ucg.up_to_diagonal

    _apply_uniformly_controlled_gate(decomposition, target, choice_reg, up_to_diagonal)


all_defined_decomposition_rules = [
    DecompositionRule(UniformlyControlledGate, _decompose_uniformly_controlled_gate)
]
