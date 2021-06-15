# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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
Register a decomposition to replace turn negatively controlled qubits into positively controlled qubits by applying X
gates.
"""

from copy import deepcopy
from projectq.cengines import DecompositionRule
from projectq.meta import Compute, Uncompute, has_negative_control
from projectq.ops import BasicGate, X


def _decompose_controlstate(cmd):
    """
    Decompose commands with control qubits in negative state (ie. control
    qubits with state '0' instead of '1')
    """
    with Compute(cmd.engine):
        for state, ctrl in zip(cmd.control_state, cmd.control_qubits):
            if state == '0':
                X | ctrl

    # Resend the command with the `control_state` cleared
    cmd.ctrl_state = '1' * len(cmd.control_state)
    orig_engine = cmd.engine
    cmd.engine.receive([deepcopy(cmd)])  # NB: deepcopy required here to workaround infinite recursion detection
    Uncompute(orig_engine)


#: Decomposition rules
all_defined_decomposition_rules = [DecompositionRule(BasicGate, _decompose_controlstate, has_negative_control)]
