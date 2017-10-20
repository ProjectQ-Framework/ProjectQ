#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Registers a decomposition rule for multi-controlled gates.

Implements the decomposition of Nielsen and Chuang (Fig. 4.10) which
decomposes a C^n(U) gate into a sequence of 2 * (n-1) Toffoli gates and one
C(U) gate by using (n-1) ancilla qubits and circuit depth of 2n-1.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import get_control_count, Compute, Control, Uncompute
from projectq.ops import BasicGate, Toffoli, XGate


def _recognize_CnU(cmd):
    """
    Recognize an arbitrary gate which has n>=2 control qubits, except a
    Toffoli gate.
    """
    if get_control_count(cmd) == 2:
        if not isinstance(cmd.gate, XGate):
            return True
    elif get_control_count(cmd) > 2:
        return True
    return False


def _decompose_CnU(cmd):
    """
    Decompose a multi-controlled gate U into a single-controlled U.

    It uses (n-1) work qubits and 2 * (n-1) Toffoli gates.
    """
    eng = cmd.engine
    qubits = cmd.qubits
    ctrl_qureg = cmd.control_qubits
    gate = cmd.gate
    n = get_control_count(cmd)
    ancilla_qureg = eng.allocate_qureg(n-1)

    with Compute(eng):
        Toffoli | (ctrl_qureg[0], ctrl_qureg[1], ancilla_qureg[0])
        for ctrl_index in range(2, n):
            Toffoli | (ctrl_qureg[ctrl_index], ancilla_qureg[ctrl_index-2],
                       ancilla_qureg[ctrl_index-1])

    with Control(eng, ancilla_qureg[-1]):
        gate | qubits

    Uncompute(eng)


all_defined_decomposition_rules = [
    DecompositionRule(BasicGate, _decompose_CnU, _recognize_CnU)
]
