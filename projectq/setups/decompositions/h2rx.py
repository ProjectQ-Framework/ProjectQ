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
Registers a decomposition for the H gate into an Ry and Rx gate.
"""

import math

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, Control, get_control_count, Uncompute
from projectq.ops import Rx, Ry, Rz, H


def _decompose_h_N(cmd):
    """ Decompose the Ry gate."""
    qubit = cmd.qubits[0]
    eng = cmd.engine
    Ry(-1*math.pi/2) | qubit
    Rx(math.pi) | qubit

def _decompose_h_M(cmd):
    """ Decompose the Ry gate."""
    qubit = cmd.qubits[0]
    eng = cmd.engine
    Rx(-1*math.pi) | qubit
    Ry(math.pi/2) | qubit

def _recognize_HNoCtrl(cmd):
    """ For efficiency reasons only if no control qubits."""
    return get_control_count(cmd) == 0


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(H.__class__, _decompose_h_N, _recognize_HNoCtrl),
    DecompositionRule(H.__class__, _decompose_h_M, _recognize_HNoCtrl)
]
