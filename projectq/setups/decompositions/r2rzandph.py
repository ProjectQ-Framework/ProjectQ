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
Registers a decomposition rule for the phase-shift gate.

Decomposes the (controlled) phase-shift gate using z-rotation and a global
phase gate.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import Control
from projectq.ops import Ph, Rz, R


def _decompose_R(cmd):
    """ Decompose the (controlled) phase-shift gate, denoted by R(phase). """
    ctrl = cmd.control_qubits
    eng = cmd.engine
    gate = cmd.gate

    with Control(eng, ctrl):
        Ph(.5 * gate._angle) | cmd.qubits
        Rz(gate._angle) | cmd.qubits


all_defined_decomposition_rules = [
    DecompositionRule(R, _decompose_R)
]
