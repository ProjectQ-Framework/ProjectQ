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
from projectq.ops import UniformlyControlledGate
from projectq.meta import Control
from projectq.libs.isometries import _apply_uniformly_controlled_gate


def _decompose_uniformly_controlled_gate(cmd):
    ucg = cmd.gate

    decomposition = ucg.decomposition
    choice_reg = cmd.qubits[0]
    target = cmd.qubits[1]
    ctrl = cmd.control_qubits
    up_to_diagonal = ucg.up_to_diagonal

    with Control(cmd.engine, ctrl):
        _apply_uniformly_controlled_gate(decomposition, target,
                                         choice_reg, up_to_diagonal)


all_defined_decomposition_rules = [
    DecompositionRule(UniformlyControlledGate,
                      _decompose_uniformly_controlled_gate)
]
