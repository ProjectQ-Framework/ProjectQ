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
Registers a decomposition for the S gate.

The S gate is perfomed by doing a T gate twice.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import Control
from projectq.ops import S, T


def _decompose_S(cmd):
    """ Decompose the S gate. """
    qr = cmd.qubits[0]
    eng = cmd.engine

    with Control(eng, cmd.control_qubits):
        T | qr[0]
        T | qr[0]
        

#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(S.__class__, _decompose_S)
]
