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
from projectq.backends import Simulator
from projectq.ops import All, Measure, X
from projectq import MainEngine
from projectq.libs.math import AddQuantum, SubtractQuantum, Comparator, QuantumConditionalAdd, QuantumDivision, QuantumConditionalAddCarry, QuantumMultiplication


def get_all_probabilities(eng, qureg):
    i = 0
    y = len(qureg)
    while i < (2**y):
        qubit_list = [int(x) for x in list(('{0:0b}'.format(i)).zfill(y))]
        qubit_list = qubit_list[::-1]
        l = eng.backend.get_probability(qubit_list, qureg)
        if l != 0.0:
            print(l, qubit_list, i)
        i += 1


def test_addition():
    eng = MainEngine()

    qunum_a = eng.allocate_qureg(5)  # 5-qubit number
    qunum_b = eng.allocate_qureg(5)  # 5-qubit number
    carry_bit = eng.allocate_qubit()
    X | qunum_a[2]  # qunum_a is now equal to 4
    X | qunum_b[3]  # qunum_b is now equal to 8
    AddQuantum() | (qunum_a, qunum_b, carry_bit)

    eng.flush()
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 1, 1, 0], qunum_b))


def test_subtraction():

    eng = MainEngine()

    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)

    X | qunum_a[2]
    X | qunum_b[3]

    SubtractQuantum() | (qunum_a, qunum_b)

    eng.flush()

    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 1, 0, 0], qunum_b))


def test_comparator():

    eng = MainEngine()

    qunum_a = eng.allocate_qureg(5)  # 5-qubit number
    qunum_b = eng.allocate_qureg(5)  # 5-qubit number
    compare_bit = eng.allocate_qubit()
    X | qunum_a[4]  # qunum_a is now equal to 16
    X | qunum_b[3]  # qunum_b is now equal to 8

    Comparator() | (qunum_a, qunum_b, compare_bit)

    eng.flush()
    print(get_all_probabilities(eng, qunum_a))
    print(get_all_probabilities(eng, qunum_b))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 0, 0, 1], qunum_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 0, 1, 0], qunum_b))
    assert 1. == pytest.approx(eng.backend.get_probability([1], compare_bit))


def test_conditionaladd():

    eng = MainEngine()

    qunum_a = eng.allocate_qureg(5)  # 5-qubit number
    qunum_b = eng.allocate_qureg(5)  # 5-qubit number
    control_bit = eng.allocate_qubit()
    X | qunum_a[4]  # qunum_a is now equal to 16
    X | qunum_b[3]  # qunum_b is now equal to 8
    X | control_bit
    QuantumConditionalAdd() | (qunum_a, qunum_b, control_bit)
    # qunum_a remain 16 and qunum_b is now 24, control_bit remains 1.

    eng.flush()

    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 0, 0, 1], qunum_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 0, 1, 1], qunum_b))
    assert 1. == pytest.approx(eng.backend.get_probability([1], control_bit))


def test_division():

    eng = MainEngine()

    qunum_a = eng.allocate_qureg(5)
    qunum_b = eng.allocate_qureg(5)
    qunum_c = eng.allocate_qureg(5)

    All(X) | [qunum_a[0], qunum_a[3]]  # qunum_a is now equal to 9
    X | qunum_c[2]  # qunum_c is now 4

    QuantumDivision() | (qunum_c, qunum_b, qunum_a)
    eng.flush()

    print(get_all_probabilities(eng, qunum_c))
    print(get_all_probabilities(eng, qunum_b))
    print(get_all_probabilities(eng, qunum_a))
    assert 1. == pytest.approx(eng.backend.get_probability(
        [1, 0, 0, 0, 0], qunum_a))  # remainder
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 0, 0, 0], qunum_b))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 1, 0, 0], qunum_c))


def test_conditionaladdcarry():

    eng = MainEngine()

    qunum_a = eng.allocate_qureg(4)  # 4-qubit number
    qunum_b = eng.allocate_qureg(4)  # 4-qubit number
    ctrl = eng.allocate_qubit()
    qunum_c = eng.allocate_qureg(2)

    X | qunum_a[1]  # qunum is now equal to 2
    All(X) | qunum_b[0:4]  # qunum is now equal to 15
    X | ctrl
    QuantumConditionalAddCarry() | (qunum_a, qunum_b, ctrl, qunum_c)
    # qunum_a and ctrl don't change, qunum_b and qunum_c are now both equal
    # to 1 so in binary together 10001 (2 + 15 = 17)

    eng.flush()

    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 0, 0], qunum_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 0, 0], qunum_b))
    assert 1. == pytest.approx(eng.backend.get_probability([1], ctrl))
    assert 1. == pytest.approx(eng.backend.get_probability([1, 0], qunum_c))

    All(Measure) | qunum_a
    All(Measure) | qunum_b


def test_multiplication():
    eng = MainEngine()

    qunum_a = eng.allocate_qureg(4)
    qunum_b = eng.allocate_qureg(4)
    qunum_c = eng.allocate_qureg(9)
    X | qunum_a[2]  # qunum_a is now 4
    X | qunum_b[3]  # qunum_b is now 8
    QuantumMultiplication() | (qunum_a, qunum_b, qunum_c)
    # qunum_a remains 4 and qunum_b remains 8, qunum_c is now equal to 32

    eng.flush()

    print(get_all_probabilities(eng, qunum_a))
    print(get_all_probabilities(eng, qunum_b))
    print(get_all_probabilities(eng, qunum_c))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 1, 0, 0], qunum_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 0, 1, 0], qunum_b))
    assert 1. == pytest.approx(eng.backend.get_probability(
        [0, 0, 0, 0, 0, 1, 0, 0, 0], qunum_c))
