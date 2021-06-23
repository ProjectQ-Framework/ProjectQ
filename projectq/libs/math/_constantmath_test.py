# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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
"""Tests for projectq.libs.math_constantmath.py."""

import pytest

from projectq import MainEngine
from projectq.cengines import InstructionFilter, AutoReplacer, DecompositionRuleSet
from projectq.backends import Simulator
from projectq.ops import All, BasicMathGate, ClassicalInstructionGate, Measure, X

import projectq.libs.math
from projectq.setups.decompositions import qft2crandhadamard, swap2cnot
from projectq.libs.math import AddConstant, AddConstantModN, MultiplyByConstantModN


def init(engine, quint, value):
    for i in range(len(quint)):
        if ((value >> i) & 1) == 1:
            X | quint[i]


def no_math_emulation(eng, cmd):
    if isinstance(cmd.gate, BasicMathGate):
        return False
    if isinstance(cmd.gate, ClassicalInstructionGate):
        return True
    try:
        return len(cmd.gate.matrix) == 2
    except AttributeError:
        return False


@pytest.fixture
def eng():
    return MainEngine(
        backend=Simulator(),
        engine_list=[AutoReplacer(rule_set), InstructionFilter(no_math_emulation)],
    )


rule_set = DecompositionRuleSet(modules=[projectq.libs.math, qft2crandhadamard, swap2cnot])


@pytest.mark.parametrize(
    'gate', (AddConstantModN(-1, 6), MultiplyByConstantModN(-1, 6), MultiplyByConstantModN(4, 4)), ids=str
)
def test_invalid(eng, gate):
    qureg = eng.allocate_qureg(4)
    init(eng, qureg, 4)

    with pytest.raises(ValueError):
        gate | qureg
        eng.flush()


def test_adder(eng):
    qureg = eng.allocate_qureg(4)
    init(eng, qureg, 4)

    AddConstant(3) | qureg

    assert 1.0 == pytest.approx(abs(eng.backend.cheat()[1][7]))

    init(eng, qureg, 7)  # reset
    init(eng, qureg, 2)

    # check for overflow -> should be 15+2 = 1 (mod 16)
    AddConstant(15) | qureg
    assert 1.0 == pytest.approx(abs(eng.backend.cheat()[1][1]))

    All(Measure) | qureg


def test_modadder(eng):
    qureg = eng.allocate_qureg(4)
    init(eng, qureg, 4)

    AddConstantModN(3, 6) | qureg

    assert 1.0 == pytest.approx(abs(eng.backend.cheat()[1][1]))

    init(eng, qureg, 1)  # reset
    init(eng, qureg, 7)

    AddConstantModN(10, 13) | qureg
    assert 1.0 == pytest.approx(abs(eng.backend.cheat()[1][4]))

    All(Measure) | qureg


def test_modmultiplier(eng):
    qureg = eng.allocate_qureg(4)
    init(eng, qureg, 4)

    MultiplyByConstantModN(3, 7) | qureg

    assert 1.0 == pytest.approx(abs(eng.backend.cheat()[1][5]))

    init(eng, qureg, 5)  # reset
    init(eng, qureg, 7)

    MultiplyByConstantModN(4, 13) | qureg
    assert 1.0 == pytest.approx(abs(eng.backend.cheat()[1][2]))

    All(Measure) | qureg
