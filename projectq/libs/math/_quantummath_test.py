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

import pytest

from projectq import MainEngine
from projectq.cengines import (InstructionFilter, AutoReplacer,
                               DecompositionRuleSet)
from projectq.backends import Simulator
from projectq.ops import (All, BasicMathGate, ClassicalInstructionGate,
                          Measure, X)

from projectq.setups.decompositions import swap2cnot

import projectq.libs.math
from projectq.libs.math import (
    AddQuantum,
    SubtractQuantum,
    ComparatorQuantum,
    DivideQuantum,
    MultiplyQuantum,
)

from projectq.meta import Control, Compute, Uncompute


def print_all_probabilities(eng, qureg):
    i = 0
    y = len(qureg)
    while i < (2**y):
        qubit_list = [int(x) for x in list(('{0:0b}'.format(i)).zfill(y))]
        qubit_list = qubit_list[::-1]
        l = eng.backend.get_probability(qubit_list, qureg)
        if l != 0.0:
            print(l, qubit_list, i)
        i += 1


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


rule_set = DecompositionRuleSet(modules=[projectq.libs.math, swap2cnot])


def test_quantum_adder():
    sim = Simulator()
    eng = MainEngine(
        sim, [AutoReplacer(rule_set),
              InstructionFilter(no_math_emulation)])

    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    control_qubit = eng.allocate_qubit()

    init(eng, qureg_a, 2)
    init(eng, qureg_b, 1)
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 0, 0], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 0, 0], qureg_b))

    with Control(eng, control_qubit):
        AddQuantum | (qureg_a, qureg_b)

    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 0, 0], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 0, 0], qureg_b))

    X | control_qubit

    with Control(eng, control_qubit):
        AddQuantum | (qureg_a, qureg_b)

    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 0, 0], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 0, 0], qureg_b))

    init(eng, qureg_a, 2)  # reset
    init(eng, qureg_b, 3)  # reset

    c = eng.allocate_qubit()
    init(eng, qureg_a, 15)
    init(eng, qureg_b, 15)

    AddQuantum | (qureg_a, qureg_b, c)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 1, 1], qureg_b))
    assert 1. == pytest.approx(eng.backend.get_probability([1], c))

    with Compute(eng):
        with Control(eng, control_qubit):
            AddQuantum | (qureg_a, qureg_b)
    Uncompute(eng)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 1, 1], qureg_b))
    assert 1. == pytest.approx(eng.backend.get_probability([1], c))

    AddQuantum | (qureg_a, qureg_b)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 1, 1], qureg_b))

    with Compute(eng):
        AddQuantum | (qureg_a, qureg_b)
    Uncompute(eng)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 1, 1], qureg_b))

    d = eng.allocate_qureg(2)

    with Compute(eng):
        with Control(eng, control_qubit):
            AddQuantum | (qureg_a, qureg_b, d)
    Uncompute(eng)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 1, 1], qureg_b))
    assert 1. == pytest.approx(eng.backend.get_probability([0, 0], d))

    All(Measure) | qureg_b
    Measure | c


def test_quantumsubtraction():

    sim = Simulator()
    eng = MainEngine(
        sim, [AutoReplacer(rule_set),
              InstructionFilter(no_math_emulation)])

    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    control_qubit = eng.allocate_qubit()

    init(eng, qureg_a, 5)
    init(eng, qureg_b, 7)

    X | control_qubit
    with Control(eng, control_qubit):
        SubtractQuantum | (qureg_a, qureg_b)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 1, 0, 0], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 0, 0, 0], qureg_b))

    init(eng, qureg_a, 5)  # reset
    init(eng, qureg_b, 2)  # reset

    init(eng, qureg_a, 5)
    init(eng, qureg_b, 3)

    SubtractQuantum | (qureg_a, qureg_b)

    print_all_probabilities(eng, qureg_b)
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 1, 0, 0], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 1, 1, 1, 0], qureg_b))

    init(eng, qureg_a, 5)  # reset
    init(eng, qureg_b, 14)  # reset
    init(eng, qureg_a, 5)
    init(eng, qureg_b, 3)

    with Compute(eng):
        SubtractQuantum | (qureg_a, qureg_b)
    Uncompute(eng)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 1, 0, 0], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 0, 0, 0], qureg_b))
    All(Measure) | qureg_a
    All(Measure) | qureg_b


def test_comparator():

    sim = Simulator()
    eng = MainEngine(
        sim, [AutoReplacer(rule_set),
              InstructionFilter(no_math_emulation)])
    qureg_a = eng.allocate_qureg(3)
    qureg_b = eng.allocate_qureg(3)
    compare_qubit = eng.allocate_qubit()

    init(eng, qureg_a, 5)
    init(eng, qureg_b, 3)

    ComparatorQuantum | (qureg_a, qureg_b, compare_qubit)

    assert 1. == pytest.approx(eng.backend.get_probability([1], compare_qubit))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    Measure | compare_qubit


def test_quantumdivision():
    sim = Simulator()
    eng = MainEngine(
        sim, [AutoReplacer(rule_set),
              InstructionFilter(no_math_emulation)])

    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    qureg_c = eng.allocate_qureg(4)

    init(eng, qureg_a, 10)
    init(eng, qureg_c, 3)

    DivideQuantum | (qureg_a, qureg_b, qureg_c)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 0, 0], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 0, 0], qureg_b))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 0, 0], qureg_c))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c

    init(eng, qureg_a, 1)  # reset
    init(eng, qureg_b, 3)  # reset

    init(eng, qureg_a, 11)

    with Compute(eng):
        DivideQuantum | (qureg_a, qureg_b, qureg_c)
    Uncompute(eng)

    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 0, 1], qureg_a))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 0, 0], qureg_b))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 1, 0, 0], qureg_c))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c


def test_quantummultiplication():

    sim = Simulator()
    eng = MainEngine(
        sim, [AutoReplacer(rule_set),
              InstructionFilter(no_math_emulation)])

    qureg_a = eng.allocate_qureg(3)
    qureg_b = eng.allocate_qureg(3)
    qureg_c = eng.allocate_qureg(7)

    init(eng, qureg_a, 7)
    init(eng, qureg_b, 3)

    MultiplyQuantum | (qureg_a, qureg_b, qureg_c)

    assert 1. == pytest.approx(eng.backend.get_probability([1, 1, 1], qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([1, 1, 0], qureg_b))
    assert 1. == pytest.approx(
        eng.backend.get_probability([1, 0, 1, 0, 1, 0, 0], qureg_c))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c

    init(eng, qureg_a, 7)
    init(eng, qureg_b, 3)
    init(eng, qureg_c, 21)

    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 0, 0, 0, 0, 0], qureg_c))
    init(eng, qureg_a, 2)
    init(eng, qureg_b, 3)

    with Compute(eng):
        MultiplyQuantum | (qureg_a, qureg_b, qureg_c)
    Uncompute(eng)

    assert 1. == pytest.approx(eng.backend.get_probability([0, 1, 0], qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([1, 1, 0], qureg_b))
    assert 1. == pytest.approx(
        eng.backend.get_probability([0, 0, 0, 0, 0, 0, 0], qureg_c))
