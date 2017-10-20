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
Registers a decomposition for the Ry gate into an Rz and Rx(pi/2) gate.
"""

import math

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, Control, get_control_count, Uncompute
from projectq.ops import Rx, Ry, Rz, H


def _decompose_ry(cmd):
    """ Decompose the Ry gate."""
    qubit = cmd.qubits[0]
    eng = cmd.engine
    angle = cmd.gate.angle

    with Control(eng, cmd.control_qubits):
        with Compute(eng):
            Rx(math.pi/2.) | qubit
        Rz(angle) | qubit
        Uncompute(eng)


def _recognize_RyNoCtrl(cmd):
    """ For efficiency reasons only if no control qubits."""
    return get_control_count(cmd) == 0


all_defined_decomposition_rules = [
    DecompositionRule(Ry, _decompose_ry, _recognize_RyNoCtrl)
]
