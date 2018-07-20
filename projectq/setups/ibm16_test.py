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
"""Tests for projectq.setup.ibm16."""

import projectq
import projectq.setups.ibm16
from projectq import MainEngine
from projectq.cengines import GridMapper, SwapAndCNOTFlipper, DummyEngine
from projectq.libs.math import AddConstant
from projectq.ops import QFT, get_inverse


def test_mappers_in_cengines():
    found = 0
    for engine in projectq.setups.ibm16.get_engine_list():
        if isinstance(engine, GridMapper):
            found |= 1
        if isinstance(engine, SwapAndCNOTFlipper):
            found |= 2
    assert found == 3


def test_high_level_gate_set():
    mod_list = projectq.setups.ibm16.get_engine_list()
    saving_engine = DummyEngine(save_commands=True)
    mod_list = mod_list[:6] + [saving_engine] + mod_list[6:]
    eng = MainEngine(DummyEngine(),
                     engine_list=mod_list)
    qureg = eng.allocate_qureg(3)
    AddConstant(3) | qureg
    QFT | qureg
    eng.flush()
    received_gates = [cmd.gate for cmd in saving_engine.received_commands]
    assert sum([1 for g in received_gates if g == QFT]) == 1
    assert get_inverse(QFT) not in received_gates
    assert AddConstant(3) not in received_gates
