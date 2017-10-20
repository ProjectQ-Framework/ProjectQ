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
Registers a decomposition for the controlled global phase gate.

Turns the controlled global phase gate into a (controlled) phase-shift gate.
Each time this rule is applied, one control can be shaved off.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import Control, get_control_count
from projectq.ops import Ph, R


def _decompose_Ph(cmd):
    """ Decompose the controlled phase gate (C^nPh(phase)). """
    ctrl = cmd.control_qubits
    gate = cmd.gate
    eng = cmd.engine

    with Control(eng, ctrl[1:]):
        R(gate.angle) | ctrl[0]


def _recognize_Ph(cmd):
    """ Recognize the controlled phase gate. """
    return get_control_count(cmd) >= 1


all_defined_decomposition_rules = [
    DecompositionRule(Ph, _decompose_Ph, _recognize_Ph)
]
