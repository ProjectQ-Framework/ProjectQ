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
"""Tests for projectq.libs.math._gates.py."""

import pytest

from projectq.cengines import (
    MainEngine,
    TagRemover,
    AutoReplacer,
    InstructionFilter,
    DecompositionRuleSet,
)
from projectq.meta import Control, Compute, Uncompute
from projectq.ops import All, Measure, X, BasicMathGate, ClassicalInstructionGate
import projectq.setups.decompositions

import projectq.libs.math
from . import (
    AddConstant,
    AddQuantum,
    SubtractQuantum,
    ComparatorQuantum,
    DivideQuantum,
    MultiplyQuantum,
)

from projectq.backends import CommandPrinter


def print_all_probabilities(eng, qureg):
    i = 0
    y = len(qureg)
    while i < (2 ** y):
        qubit_list = [int(x) for x in list(('{0:0b}'.format(i)).zfill(y))]
        qubit_list = qubit_list[::-1]
        prob = eng.backend.get_probability(qubit_list, qureg)
        if prob != 0.0:
            print(prob, qubit_list, i)

        i += 1


def _eng_emulation():
    # Only decomposing native ProjectQ gates
    # -> using emulation for gates in projectq.libs.math
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    eng = MainEngine(
        engine_list=[
            TagRemover(),
            AutoReplacer(rule_set),
            TagRemover(),
            CommandPrinter(),
        ],
        verbose=True,
    )
    return eng


def _eng_decomp():
    def no_math_emulation(eng, cmd):
        if isinstance(cmd.gate, BasicMathGate):
            return False
        if isinstance(cmd.gate, ClassicalInstructionGate):
            return True
        try:
            return len(cmd.gate.matrix) > 0
        except AttributeError:
            return False

    rule_set = DecompositionRuleSet(modules=[projectq.libs.math, projectq.setups.decompositions.qft2crandhadamard])
    eng = MainEngine(
        engine_list=[
            TagRemover(),
            AutoReplacer(rule_set),
            InstructionFilter(no_math_emulation),
            TagRemover(),
            CommandPrinter(),
        ]
    )
    return eng


@pytest.fixture(params=['no_decomp', 'full_decomp'])
def eng(request):
    if request.param == 'no_decomp':
        return _eng_emulation()
    elif request.param == 'full_decomp':
        return _eng_decomp()


def test_constant_addition(eng):
    qunum_a = eng.allocate_qureg(5)
    X | qunum_a[2]
    with Compute(eng):
        AddConstant(5) | (qunum_a)

    Uncompute(eng)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))


def test_addition(eng):
    qunum_a = eng.allocate_qureg(5)  # 5-qubit number
    qunum_b = eng.allocate_qureg(5)  # 5-qubit number
    carry_bit = eng.allocate_qubit()
    X | qunum_a[2]  # qunum_a is now equal to 4
    X | qunum_b[3]  # qunum_b is now equal to 8
    AddQuantum | (qunum_a, qunum_b, carry_bit)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 1, 0], qunum_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0], carry_bit))


def test_inverse_addition(eng):
    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)
    X | qunum_a[2]
    X | qunum_b[3]
    with Compute(eng):
        AddQuantum | (qunum_a, qunum_b)
    Uncompute(eng)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 1, 0], qunum_b))


def test_inverse_addition_with_control(eng):
    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)
    qunum_c = eng.allocate_qubit()
    All(X) | qunum_a
    All(X) | qunum_b
    X | qunum_c
    with Compute(eng):
        with Control(eng, qunum_c):
            AddQuantum | (qunum_a, qunum_b)

    Uncompute(eng)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1, 1, 1], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1, 1, 1], qunum_b))


def test_addition_with_control(eng):
    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)
    control_bit = eng.allocate_qubit()
    X | qunum_a[1]  # qunum_a is now equal to 2
    X | qunum_b[4]  # qunum_b is now equal to 16
    X | control_bit
    with Control(eng, control_bit):
        AddQuantum | (qunum_a, qunum_b)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0, 1], qunum_b))


def test_addition_with_control_carry(eng):
    qunum_a = eng.allocate_qureg(4)  # 4-qubit number
    qunum_b = eng.allocate_qureg(4)  # 4-qubit number
    control_bit = eng.allocate_qubit()
    qunum_c = eng.allocate_qureg(2)

    X | qunum_a[1]  # qunum is now equal to 2
    All(X) | qunum_b[0:4]  # qunum is now equal to 15
    X | control_bit

    with Control(eng, control_bit):
        AddQuantum | (qunum_a, qunum_b, qunum_c)
    # qunum_a and ctrl don't change, qunum_b and qunum_c are now both equal
    # to 1 so in binary together 10001 (2 + 15 = 17)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 0, 0], qunum_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1], control_bit))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0], qunum_c))

    All(Measure) | qunum_a
    All(Measure) | qunum_b


def test_inverse_addition_with_control_carry(eng):
    qunum_a = eng.allocate_qureg(4)
    qunum_b = eng.allocate_qureg(4)

    control_bit = eng.allocate_qubit()
    qunum_c = eng.allocate_qureg(2)

    X | qunum_a[1]
    All(X) | qunum_b[0:4]
    X | control_bit
    with Compute(eng):
        with Control(eng, control_bit):
            AddQuantum | (qunum_a, qunum_b, qunum_c)
    Uncompute(eng)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1, 1], qunum_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1], control_bit))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0], qunum_c))

    All(Measure) | qunum_a
    All(Measure) | qunum_b
    Measure | control_bit
    All(Measure) | qunum_c


def test_subtraction(eng):
    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)

    X | qunum_a[2]
    X | qunum_b[3]

    SubtractQuantum | (qunum_a, qunum_b)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_b))


def test_inverse_subtraction(eng):
    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)

    X | qunum_a[2]
    X | qunum_b[3]

    with Compute(eng):
        SubtractQuantum | (qunum_a, qunum_b)
    Uncompute(eng)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 1, 0], qunum_b))


def test_comparator(eng):
    qunum_a = eng.allocate_qureg(5)  # 5-qubit number
    qunum_b = eng.allocate_qureg(5)  # 5-qubit number
    compare_bit = eng.allocate_qubit()
    X | qunum_a[4]  # qunum_a is now equal to 16
    X | qunum_b[3]  # qunum_b is now equal to 8

    ComparatorQuantum | (qunum_a, qunum_b, compare_bit)

    eng.flush()
    print_all_probabilities(eng, qunum_a)
    print_all_probabilities(eng, qunum_b)
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 0, 1], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 1, 0], qunum_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1], compare_bit))


def test_division(eng):
    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)
    qunum_c = eng.allocate_qureg(5)

    All(X) | [qunum_a[0], qunum_a[3]]  # qunum_a is now equal to 9
    X | qunum_c[2]  # qunum_c is now 4

    DivideQuantum | (qunum_a, qunum_b, qunum_c)
    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 0, 0, 0], qunum_a))  # remainder
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0, 0], qunum_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_c))


def test_inverse_division(eng):
    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)
    qunum_c = eng.allocate_qureg(5)

    All(X) | [qunum_a[0], qunum_a[3]]
    X | qunum_c[2]

    with Compute(eng):
        DivideQuantum | (qunum_a, qunum_b, qunum_c)
    Uncompute(eng)
    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 0, 1, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 0, 0], qunum_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_c))


def test_multiplication(eng):
    qunum_a = eng.allocate_qureg(4)
    qunum_b = eng.allocate_qureg(4)
    qunum_c = eng.allocate_qureg(9)
    X | qunum_a[2]  # qunum_a is now 4
    X | qunum_b[3]  # qunum_b is now 8
    MultiplyQuantum | (qunum_a, qunum_b, qunum_c)
    # qunum_a remains 4 and qunum_b remains 8, qunum_c is now equal to 32

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 1, 0], qunum_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 0, 0, 1, 0, 0, 0], qunum_c))


def test_inverse_multiplication(eng):
    qunum_a = eng.allocate_qureg(4)
    qunum_b = eng.allocate_qureg(4)
    qunum_c = eng.allocate_qureg(9)
    X | qunum_a[2]  # qunum_a is now 4
    X | qunum_b[3]  # qunum_b is now 8
    with Compute(eng):
        MultiplyQuantum | (qunum_a, qunum_b, qunum_c)
    Uncompute(eng)

    eng.flush()

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 1, 0], qunum_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 0, 0, 0, 0, 0, 0], qunum_c))
