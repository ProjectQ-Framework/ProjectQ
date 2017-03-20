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
Registers a decomposition to achieve a Swap gate.

Decomposes a Swap gate using 3 CNOT gates, where the one in the middle
features as many control qubits as the Swap gate has control qubits.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, Uncompute, Control, get_control_count
from projectq.ops import Swap, CNOT


def _decompose_swap(cmd):
    """ Decompose (controlled) swap gates. """
    ctrl = cmd.control_qubits
    eng = cmd.engine
    with Compute(eng):
        CNOT | (cmd.qubits[0], cmd.qubits[1])
    with Control(eng, ctrl):
        CNOT | (cmd.qubits[1], cmd.qubits[0])
    Uncompute(eng)


all_defined_decomposition_rules = [
    DecompositionRule(Swap.__class__, _decompose_swap)
]
