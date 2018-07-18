#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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
Registers a decomposition to for a CNOT gate in terms of CZ and Hadamard.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, get_control_count, Uncompute
from projectq.ops import CZ, H, X


def _decompose_cnot(cmd):
    """ Decompose CNOT gates. """
    ctrl = cmd.control_qubits
    eng = cmd.engine
    with Compute(eng):
        H | cmd.qubits[0]
    CZ | (ctrl[0], cmd.qubits[0][0])
    Uncompute(eng)


def _recognize_cnot(cmd):
    return get_control_count(cmd) == 1


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(X.__class__, _decompose_cnot, _recognize_cnot)
]
