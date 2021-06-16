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
Tests for the controlstate decomposition rule.
"""

from projectq import MainEngine
from projectq.cengines import DummyEngine, AutoReplacer, InstructionFilter, DecompositionRuleSet
from projectq.meta import Control, has_negative_control
from projectq.ops import X
from projectq.setups.decompositions import controlstate, cnot2cz


def filter_func(eng, cmd):
    if has_negative_control(cmd):
        return False
    return True


def test_controlstate_priority():
    saving_backend = DummyEngine(save_commands=True)
    rule_set = DecompositionRuleSet(modules=[cnot2cz, controlstate])
    eng = MainEngine(backend=saving_backend, engine_list=[AutoReplacer(rule_set), InstructionFilter(filter_func)])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()
    with Control(eng, qubit2, ctrl_state='0'):
        X | qubit1
    with Control(eng, qubit3, ctrl_state='1'):
        X | qubit1
    eng.flush()

    assert len(saving_backend.received_commands) == 8
    for cmd in saving_backend.received_commands:
        assert not has_negative_control(cmd)
