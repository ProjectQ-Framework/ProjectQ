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
Registers a decomposition for controlled z-rotation gates.

It uses 2 z-rotations and 2 C^n NOT gates to achieve this gate.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import get_control_count
from projectq.ops import NOT, Rz, C


def _decompose_CRz(cmd):
    """ Decompose the controlled Rz gate (into CNOT and Rz). """
    qubit = cmd.qubits[0]
    ctrl = cmd.control_qubits
    gate = cmd.gate
    n = get_control_count(cmd)

    Rz(0.5 * gate._angle) | qubit
    C(NOT, n) | (ctrl, qubit)
    Rz(-0.5 * gate._angle) | qubit
    C(NOT, n) | (ctrl, qubit)


def _recognize_CRz(cmd):
    """ Recognize the controlled Rz gate. """
    return get_control_count(cmd) >= 1


all_defined_decomposition_rules = [
    DecompositionRule(Rz, _decompose_CRz, _recognize_CRz)
]
