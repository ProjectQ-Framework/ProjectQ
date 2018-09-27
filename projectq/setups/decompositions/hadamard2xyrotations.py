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
Registers a decomposition for the Hadamard gate.
"""

import numpy as np
from projectq.cengines import DecompositionRule
from projectq.meta import Control, get_control_count
from projectq.ops import X, Ry, Ph, H 

def _recognize_hadamard(cmd):
    """ For efficiency only use this if at most 1 control qubit."""
    return get_control_count(cmd) <= 1

def _decompose_hadamard(cmd):
    """ Decompose the H gate. """
    qr = cmd.qubits[0]
    eng = cmd.engine

    with Control(eng, cmd.control_qubits):
        X | qr[0]
        Ry(-np.pi/2) | qr[0]
        Ph(np.pi/2) | qr[0]


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(H.__class__, _decompose_hadamard, _recognize_hadamard)
]
