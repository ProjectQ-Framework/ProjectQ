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
"""
Registers a decomposition rule for the Toffoli gate.

Decomposes the Toffoli gate using Hadamard, T, Tdag, and CNOT gates.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import get_control_count
from projectq.ops import CNOT, NOT, H, T, Tdag


def _decompose_toffoli(cmd):
    """Decompose the Toffoli gate into CNOT, H, T, and Tdagger gates."""
    ctrl = cmd.control_qubits

    target = cmd.qubits[0]

    H | target
    CNOT | (ctrl[0], target)
    T | ctrl[0]
    Tdag | target
    CNOT | (ctrl[1], target)
    CNOT | (ctrl[1], ctrl[0])
    Tdag | ctrl[0]
    T | target
    CNOT | (ctrl[1], ctrl[0])
    CNOT | (ctrl[0], target)
    Tdag | target
    CNOT | (ctrl[1], target)
    T | target
    T | ctrl[1]
    H | target


def _recognize_toffoli(cmd):
    """Recognize the Toffoli gate."""
    return get_control_count(cmd) == 2


#: Decomposition rules
all_defined_decomposition_rules = [DecompositionRule(NOT.__class__, _decompose_toffoli, _recognize_toffoli)]
