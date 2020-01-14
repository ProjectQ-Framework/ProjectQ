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
#
#   Module uses ideas from "Basic circuit compilation techniques for an
#   ion-trap quantum machine" by Dmitri Maslov (2017) at
#   https://iopscience.iop.org/article/10.1088/1367-2630/aa5e47
"""
Registers a decomposition for the H gate into an Ry and Rx gate.
"""

import math

from projectq.cengines import DecompositionRule
from projectq.meta import get_control_count
from projectq.ops import Ph, Rx, Ry, H


def _decompose_h2rx_M(cmd):
    """ Decompose the Ry gate."""
    # Labelled 'M' for 'minus' because decomposition ends with a Ry(-pi/2)
    qubit = cmd.qubits[0]
    Rx(math.pi) | qubit
    Ph(math.pi/2) | qubit
    Ry(-1 * math.pi / 2) | qubit


def _decompose_h2rx_N(cmd):
    """ Decompose the Ry gate."""
    # Labelled 'N' for 'neutral' because decomposition doesn't end with
    # Ry(pi/2) or Ry(-pi/2)
    qubit = cmd.qubits[0]
    Ry(math.pi / 2) | qubit
    Ph(3*math.pi/2) | qubit
    Rx(-1 * math.pi) | qubit


def _recognize_HNoCtrl(cmd):
    """ For efficiency reasons only if no control qubits."""
    return get_control_count(cmd) == 0


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(H.__class__, _decompose_h2rx_N, _recognize_HNoCtrl),
    DecompositionRule(H.__class__, _decompose_h2rx_M, _recognize_HNoCtrl)
]
