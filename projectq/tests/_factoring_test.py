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

import pytest

import projectq.libs.math
import projectq.setups.decompositions
from projectq.backends._sim._simulator_test import sim
from projectq.cengines import (MainEngine,
                               AutoReplacer,
                               DecompositionRuleSet,
                               InstructionFilter,
                               LocalOptimizer,
                               TagRemover)
from projectq.libs.math import MultiplyByConstantModN
from projectq.meta import Control
from projectq.ops import X, H, QFT, BasicMathGate, Swap, get_inverse, Measure

rule_set = DecompositionRuleSet(modules=(projectq.libs.math,
                                         projectq.setups.decompositions))

assert sim  # Asserts to tools that the fixture import is used.


def high_level_gates(eng, cmd):
    g = cmd.gate
    if g == QFT or get_inverse(g) == QFT or g == Swap:
        return True
    if isinstance(g, BasicMathGate):
        return False
    return eng.next_engine.is_available(cmd)


def get_main_engine(sim):
    engine_list = [AutoReplacer(rule_set),
                   InstructionFilter(high_level_gates),
                   TagRemover(),
                   LocalOptimizer(3),
                   AutoReplacer(rule_set),
                   TagRemover(),
                   LocalOptimizer(3)]
    return MainEngine(sim, engine_list)


def test_factoring(sim):
    eng = get_main_engine(sim)

    ctrl_qubit = eng.allocate_qubit()

    N = 15
    a = 2

    x = eng.allocate_qureg(4)
    X | x[0]

    H | ctrl_qubit
    with Control(eng, ctrl_qubit):
        MultiplyByConstantModN(pow(a, 2**7, N), N) | x

    H | ctrl_qubit
    eng.flush()
    cheat_tpl = sim.cheat()
    idx = cheat_tpl[0][ctrl_qubit[0].id]
    vec = cheat_tpl[1]

    for i in range(len(vec)):
        if abs(vec[i]) > 1.e-8:
            assert ((i >> idx) & 1) == 0

    Measure | ctrl_qubit
    assert int(ctrl_qubit) == 0
    del vec, cheat_tpl

    H | ctrl_qubit
    with Control(eng, ctrl_qubit):
        MultiplyByConstantModN(pow(a, 2, N), N) | x

    H | ctrl_qubit
    eng.flush()
    cheat_tpl = sim.cheat()
    idx = cheat_tpl[0][ctrl_qubit[0].id]
    vec = cheat_tpl[1]

    probability = 0.
    for i in range(len(vec)):
        if abs(vec[i]) > 1.e-8:
            if ((i >> idx) & 1) == 0:
                probability += abs(vec[i])**2

    assert probability == pytest.approx(.5)

    Measure | ctrl_qubit
    Measure | x
