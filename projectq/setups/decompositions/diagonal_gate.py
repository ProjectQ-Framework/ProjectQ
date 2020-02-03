# Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
