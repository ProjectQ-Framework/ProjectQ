# -*- coding: utf-8 -*-
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
#
#   Module uses ideas from "Basic circuit compilation techniques
#   for an ion-trap quantum machine" by Dmitri Maslov (2017) at
#   https://iopscience.iop.org/article/10.1088/1367-2630/aa5e47
"""
Registers a decomposition to for a CNOT gate in terms of Rxx, Rx and Ry gates.
"""

import math

from projectq.cengines import DecompositionRule
from projectq.meta import get_control_count
from projectq.ops import Ph, Rxx, Ry, Rx, X


def _decompose_cnot2rxx_M(cmd):  # pylint: disable=invalid-name
    """Decompose CNOT gate into Rxx gate."""
    # Labelled 'M' for 'minus' because decomposition ends with a Ry(-pi/2)
    ctrl = cmd.control_qubits
    Ry(math.pi / 2) | ctrl[0]
    Ph(7 * math.pi / 4) | ctrl[0]
    Rx(-math.pi / 2) | ctrl[0]
    Rx(-math.pi / 2) | cmd.qubits[0][0]
    Rxx(math.pi / 2) | (ctrl[0], cmd.qubits[0][0])
    Ry(-1 * math.pi / 2) | ctrl[0]


def _decompose_cnot2rxx_P(cmd):  # pylint: disable=invalid-name
    """Decompose CNOT gate into Rxx gate."""
    # Labelled 'P' for 'plus' because decomposition ends with a Ry(+pi/2)
    ctrl = cmd.control_qubits
    Ry(-math.pi / 2) | ctrl[0]
    Ph(math.pi / 4) | ctrl[0]
    Rx(-math.pi / 2) | ctrl[0]
    Rx(math.pi / 2) | cmd.qubits[0][0]
    Rxx(math.pi / 2) | (ctrl[0], cmd.qubits[0][0])
    Ry(math.pi / 2) | ctrl[0]


def _recognize_cnot2(cmd):
    """Identify that the command is a CNOT gate (control - X gate)"""
    return get_control_count(cmd) == 1


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(X.__class__, _decompose_cnot2rxx_M, _recognize_cnot2),
    DecompositionRule(X.__class__, _decompose_cnot2rxx_P, _recognize_cnot2),
]
