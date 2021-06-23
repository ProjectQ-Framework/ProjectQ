# -*- coding: utf-8 -*-
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
Registers a decomposition for the Rz gate into an Rx and Ry(pi/2) or Ry(-pi/2)
gate
"""

import math

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, Control, get_control_count, Uncompute
from projectq.ops import Rx, Ry, Rz


def _decompose_rz2rx_P(cmd):  # pylint: disable=invalid-name
    """Decompose the Rz using negative angle."""
    # Labelled 'P' for 'plus' because decomposition ends with a Ry(+pi/2)
    qubit = cmd.qubits[0]
    eng = cmd.engine
    angle = cmd.gate.angle

    with Control(eng, cmd.control_qubits):
        with Compute(eng):
            Ry(-math.pi / 2.0) | qubit
        Rx(-angle) | qubit
        Uncompute(eng)


def _decompose_rz2rx_M(cmd):  # pylint: disable=invalid-name
    """Decompose the Rz using positive angle."""
    # Labelled 'M' for 'minus' because decomposition ends with a Ry(-pi/2)
    qubit = cmd.qubits[0]
    eng = cmd.engine
    angle = cmd.gate.angle

    with Control(eng, cmd.control_qubits):
        with Compute(eng):
            Ry(math.pi / 2.0) | qubit
        Rx(angle) | qubit
        Uncompute(eng)


def _recognize_RzNoCtrl(cmd):  # pylint: disable=invalid-name
    """Decompose the gate only if the command represents a single qubit gate (if it is not part of a control gate)."""
    return get_control_count(cmd) == 0


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(Rz, _decompose_rz2rx_P, _recognize_RzNoCtrl),
    DecompositionRule(Rz, _decompose_rz2rx_M, _recognize_RzNoCtrl),
]
