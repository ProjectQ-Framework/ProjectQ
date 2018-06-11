from projectq.ops import Isometry
from projectq.meta import Control
from projectq.cengines import DecompositionRule
from projectq.libs.isometries import _apply_isometry

import cmath


def _print_qureg(qureg):
    eng = qureg.engine
    eng.flush()
    bla, vec = eng.backend.cheat()
    for i in range(len(vec)):
        print("{}: {:.3f}, {}".format(i,abs(vec[i]), cmath.phase(vec[i])))
    print("-")

def _print_vec(vec):
    for i in range(len(vec)):
        print("{}: {:.3f}, {}".format(i,abs(vec[i]), cmath.phase(vec[i])))
    print("-")

def _decompose_isometry(cmd):
    iso = cmd.gate
    decomposition = iso.decomposition
    threshold = iso._threshold
    ctrl = cmd.control_qubits

    qureg = []
    for reg in cmd.qubits:
        qureg.extend(reg)

    with Control(cmd.engine, ctrl):
        _apply_isometry(decomposition, threshold, qureg)


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(Isometry, _decompose_isometry)
]
