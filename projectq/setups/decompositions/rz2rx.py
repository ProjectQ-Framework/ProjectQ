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
Registers a decomposition for the Rz gate into an Rx and Ry(pi/2) or Ry(-pi/2) gate
"""

import math

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, Control, get_control_count, Uncompute
from projectq.ops import Rx, Ry, Rz, H


def _decompose_rz2rx_P(cmd):
    """ Decompose the Rz using negative angle. """
    qubit = cmd.qubits[0]
    eng = cmd.engine
    angle = cmd.gate.angle

    with Control(eng, cmd.control_qubits):
        with Compute(eng):
            Ry(-math.pi/2.) | qubit
        Rx(-angle) | qubit
        Uncompute(eng)

def _decompose_rz2rx_M(cmd):
    """ Decompose the Rz using positive angle. """
    qubit = cmd.qubits[0]
    eng = cmd.engine
    angle = cmd.gate.angle

    with Control(eng, cmd.control_qubits):
        with Compute(eng):
            Ry(math.pi/2.) | qubit
        Rx(angle) | qubit
        Uncompute(eng)

def _recognize_RzNoCtrl(cmd):
    """ For efficiency reasons only if no control qubits."""
    return get_control_count(cmd) == 0


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(Rz, _decompose_rz2rx_P, _recognize_RzNoCtrl),
    DecompositionRule(Rz, _decompose_rz2rx_M, _recognize_RzNoCtrl)
]
