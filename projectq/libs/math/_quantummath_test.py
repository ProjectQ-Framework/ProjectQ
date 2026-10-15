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

import projectq.libs.math
from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import AutoReplacer, BasicEngine, DecompositionRuleSet, InstructionFilter
from projectq.libs.math import (
    AddQuantum,
    ComparatorQuantum,
    DivideQuantum,
    MultiplyQuantum,
    SubtractQuantum,
)
from projectq.meta import Compute, Control, Dagger, Uncompute
from projectq.ops import All, BasicMathGate, ClassicalInstructionGate, Measure, X
from projectq.setups.decompositions import swap2cnot


def print_all_probabilities(eng, qureg):
    i = 0
    y = len(qureg)
    while i < (2**y):
        qubit_list = [int(x) for x in list((f'{i:0b}').zfill(y))]
        qubit_list = qubit_list[::-1]
        prob = eng.backend.get_probability(qubit_list, qureg)
        if prob != 0.0:
            print(prob, qubit_list, i)
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


@pytest.fixture
def eng():
    return MainEngine(
        backend=Simulator(),
        engine_list=[AutoReplacer(rule_set), InstructionFilter(no_math_emulation)],
    )


@pytest.mark.parametrize('carry', (False, True))
@pytest.mark.parametrize('inverse', (False, True))
@pytest.mark.parametrize('qubit_idx', (0, 1, 2))
def test_quantumadder_size_mismatch(eng, qubit_idx, inverse, carry):
    qureg_a = eng.allocate_qureg(4 if qubit_idx != 0 else 3)
    qureg_b = eng.allocate_qureg(4 if qubit_idx != 1 else 3)
    qureg_c = eng.allocate_qureg(1 if qubit_idx != 2 else 2)

    if carry and inverse:
        pytest.skip('Inverse addition with carry not supported')
    elif not carry and qubit_idx == 2:
        pytest.skip('Invalid test parameter combination')

    with pytest.raises(ValueError):
        if inverse:
            with Dagger(eng):
                AddQuantum | (qureg_a, qureg_b, qureg_c if carry else [])
        else:
            AddQuantum | (qureg_a, qureg_b, qureg_c if carry else [])


@pytest.mark.parametrize('qubit_idx', (0, 1, 2))
def test_quantum_conditional_adder_size_mismatch(eng, qubit_idx):
    qureg_a = eng.allocate_qureg(4 if qubit_idx != 0 else 3)
    qureg_b = eng.allocate_qureg(4 if qubit_idx != 1 else 3)
    control = eng.allocate_qureg(1 if qubit_idx != 2 else 2)

    with pytest.raises(ValueError):
        with Control(eng, control):
            AddQuantum | (qureg_a, qureg_b)


@pytest.mark.parametrize('inverse', (False, True))
@pytest.mark.parametrize('qubit_idx', (0, 1, 2, 3))
def test_quantum_conditional_add_carry_size_mismatch(eng, qubit_idx, inverse):
    qureg_a = eng.allocate_qureg(4 if qubit_idx != 0 else 3)
    qureg_b = eng.allocate_qureg(4 if qubit_idx != 1 else 3)
    qureg_c = eng.allocate_qureg(2 if qubit_idx != 2 else 3)
    control = eng.allocate_qureg(1 if qubit_idx != 3 else 2)

    with pytest.raises(ValueError):
        with Control(eng, control):
            if inverse:
                with Dagger(eng):
                    AddQuantum | (qureg_a, qureg_b, qureg_c)
            else:
                AddQuantum | (qureg_a, qureg_b, qureg_c)


def test_quantum_adder(eng):
    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    control_qubit = eng.allocate_qubit()

    init(eng, qureg_a, 2)
    init(eng, qureg_b, 1)
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 0, 0], qureg_b))

    with Control(eng, control_qubit):
        AddQuantum | (qureg_a, qureg_b)

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 0, 0], qureg_b))

    X | control_qubit

    with Control(eng, control_qubit):
        AddQuantum | (qureg_a, qureg_b)

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0, 0], qureg_b))

    init(eng, qureg_a, 2)  # reset
    init(eng, qureg_b, 3)  # reset

    c = eng.allocate_qubit()
    init(eng, qureg_a, 15)
    init(eng, qureg_b, 15)

    AddQuantum | (qureg_a, qureg_b, c)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 1, 1], qureg_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1], c))

    with Compute(eng):
        with Control(eng, control_qubit):
            AddQuantum | (qureg_a, qureg_b)
    Uncompute(eng)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 1, 1], qureg_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1], c))

    AddQuantum | (qureg_a, qureg_b)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 1, 1], qureg_b))

    with Compute(eng):
        AddQuantum | (qureg_a, qureg_b)
    Uncompute(eng)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 1, 1], qureg_b))

    d = eng.allocate_qureg(2)

    with Compute(eng):
        with Control(eng, control_qubit):
            AddQuantum | (qureg_a, qureg_b, d)
    Uncompute(eng)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1, 1], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 1, 1], qureg_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0], d))

    All(Measure) | qureg_b
    Measure | c


def test_quantumsubtraction(eng):
    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    control_qubit = eng.allocate_qubit()

    init(eng, qureg_a, 5)
    init(eng, qureg_b, 7)

    X | control_qubit
    with Control(eng, control_qubit):
        SubtractQuantum | (qureg_a, qureg_b)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 1, 0, 0], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0, 0, 0], qureg_b))

    # Size mismatch
    with pytest.raises(ValueError):
        SubtractQuantum | (qureg_a, qureg_b[:-1])
        eng.flush()

    init(eng, qureg_a, 5)  # reset
    init(eng, qureg_b, 2)  # reset

    init(eng, qureg_a, 5)
    init(eng, qureg_b, 3)

    SubtractQuantum | (qureg_a, qureg_b)

    print_all_probabilities(eng, qureg_b)
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 1, 0, 0], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 1, 1, 0], qureg_b))

    init(eng, qureg_a, 5)  # reset
    init(eng, qureg_b, 14)  # reset
    init(eng, qureg_a, 5)
    init(eng, qureg_b, 3)

    with Compute(eng):
        SubtractQuantum | (qureg_a, qureg_b)
    Uncompute(eng)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 1, 0, 0], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0, 0, 0], qureg_b))
    All(Measure) | qureg_a
    All(Measure) | qureg_b


def test_comparator(eng):
    qureg_a = eng.allocate_qureg(3)
    qureg_b = eng.allocate_qureg(3)
    compare_qubit = eng.allocate_qubit()

    init(eng, qureg_a, 5)
    init(eng, qureg_b, 3)

    ComparatorQuantum | (qureg_a, qureg_b, compare_qubit)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 1], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0], qureg_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1], compare_qubit))

    # Size mismatch in qubit registers
    with pytest.raises(ValueError):
        ComparatorQuantum | (qureg_a, qureg_b[:-1], compare_qubit)

    # Only single qubit for compare qubit
    with pytest.raises(ValueError):
        ComparatorQuantum | (qureg_a, qureg_b, [*compare_qubit, *compare_qubit])

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    Measure | compare_qubit


class _BasisBackend(BasicEngine):
    """Exact basis-state backend accepting only multi-controlled X and lifecycle gates."""

    def __init__(self):
        super().__init__()
        self.state = {}

    def is_available(self, cmd):
        return cmd.gate.__class__.__name__ in (
            'XGate',
            'AllocateQubitGate',
            'DeallocateQubitGate',
            'FlushGate',
            'MeasureGate',
        )

    def receive(self, commands):
        for cmd in commands:
            name = cmd.gate.__class__.__name__
            if name == 'AllocateQubitGate':
                self.state[cmd.qubits[0][0].id] = 0
            elif name == 'XGate' and all(self.state[c.id] for c in cmd.control_qubits):
                self.state[cmd.qubits[0][0].id] ^= 1


def _run_comparator_decomposition(a_val, b_val, c_val, n_bits=3):
    backend = _BasisBackend()
    rules = DecompositionRuleSet(modules=[projectq.libs.math])
    engine = MainEngine(backend=backend, engine_list=[AutoReplacer(rules)])
    reg_a = engine.allocate_qureg(n_bits)
    reg_b = engine.allocate_qureg(n_bits)
    reg_c = engine.allocate_qureg(1)
    for i, qubit in enumerate(reg_a):
        if (a_val >> i) & 1:
            X | qubit
    for i, qubit in enumerate(reg_b):
        if (b_val >> i) & 1:
            X | qubit
    if c_val:
        X | reg_c[0]
    ComparatorQuantum | (reg_a, reg_b, reg_c)
    All(Measure) | (reg_a + reg_b + reg_c)
    engine.flush()
    res_a = sum(backend.state[q.id] << i for i, q in enumerate(reg_a))
    res_b = sum(backend.state[q.id] << i for i, q in enumerate(reg_b))
    res_c = backend.state[reg_c[0].id]
    return res_a, res_b, res_c


@pytest.mark.parametrize(
    'a, b, c_in, expected_c',
    [
        (1, 0, 0, 1),
        (0, 1, 0, 0),
        (2, 2, 0, 0),
        (1, 0, 1, 0),
        (0, 1, 1, 1),
        (7, 0, 0, 1),
        (0, 7, 0, 0),
        (7, 7, 1, 1),
    ],
)
def test_comparator_decomposition_restore_registers(a, b, c_in, expected_c):
    res_a, res_b, res_c = _run_comparator_decomposition(a, b, c_in, n_bits=3)
    assert res_a == a
    assert res_b == b
    assert res_c == expected_c


def test_comparator_decomposition_all_3bit_cases():
    for a in range(8):
        for b in range(8):
            for c_in in (0, 1):
                res_a, res_b, res_c = _run_comparator_decomposition(a, b, c_in, n_bits=3)
                assert res_a == a
                assert res_b == b
                assert res_c == c_in ^ int(a > b)


@pytest.mark.parametrize('qubit_idx', (0, 1, 2))
def test_quantumdivision_size_mismatch(eng, qubit_idx):
    qureg_a = eng.allocate_qureg(4 if qubit_idx != 0 else 3)
    qureg_b = eng.allocate_qureg(4 if qubit_idx != 1 else 3)
    qureg_c = eng.allocate_qureg(4 if qubit_idx != 2 else 3)

    with pytest.raises(ValueError):
        DivideQuantum | (qureg_a, qureg_b, qureg_c)

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c


@pytest.mark.parametrize('qubit_idx', (0, 1, 2))
def test_quantumdivision_size_mismatch_inverse(eng, qubit_idx):
    qureg_a = eng.allocate_qureg(4 if qubit_idx != 0 else 3)
    qureg_b = eng.allocate_qureg(4 if qubit_idx != 1 else 3)
    qureg_c = eng.allocate_qureg(4 if qubit_idx != 2 else 3)

    with pytest.raises(ValueError):
        with Dagger(eng):
            DivideQuantum | (qureg_a, qureg_b, qureg_c)

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c


def test_quantumdivision(eng):
    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    qureg_c = eng.allocate_qureg(4)

    init(eng, qureg_a, 10)
    init(eng, qureg_c, 3)

    DivideQuantum | (qureg_a, qureg_b, qureg_c)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 0, 0], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0, 0], qureg_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0, 0], qureg_c))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c

    init(eng, qureg_a, 1)  # reset
    init(eng, qureg_b, 3)  # reset

    init(eng, qureg_a, 11)

    with Compute(eng):
        DivideQuantum | (qureg_a, qureg_b, qureg_c)
    Uncompute(eng)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0, 1], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 0], qureg_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0, 0], qureg_c))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c


@pytest.mark.parametrize('qubit_idx', (0, 1, 2))
def test_quantummultiplication_size_mismatch(eng, qubit_idx):
    qureg_a = eng.allocate_qureg(3 if qubit_idx != 0 else 2)
    qureg_b = eng.allocate_qureg(3 if qubit_idx != 1 else 2)
    qureg_c = eng.allocate_qureg(7 if qubit_idx != 2 else 6)

    with pytest.raises(ValueError):
        MultiplyQuantum | (qureg_a, qureg_b, qureg_c)

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c


@pytest.mark.parametrize('qubit_idx', (0, 1, 2))
def test_quantummultiplication_size_mismatch_inverse(eng, qubit_idx):
    qureg_a = eng.allocate_qureg(4 if qubit_idx != 0 else 3)
    qureg_b = eng.allocate_qureg(4 if qubit_idx != 1 else 3)
    qureg_c = eng.allocate_qureg(4 if qubit_idx != 2 else 3)

    with pytest.raises(ValueError):
        with Dagger(eng):
            MultiplyQuantum | (qureg_a, qureg_b, qureg_c)

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c


def test_quantummultiplication(eng):
    qureg_a = eng.allocate_qureg(3)
    qureg_b = eng.allocate_qureg(3)
    qureg_c = eng.allocate_qureg(7)

    init(eng, qureg_a, 7)
    init(eng, qureg_b, 3)

    MultiplyQuantum | (qureg_a, qureg_b, qureg_c)

    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 1], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0], qureg_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 0, 1, 0, 1, 0, 0], qureg_c))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    All(Measure) | qureg_c

    init(eng, qureg_a, 7)
    init(eng, qureg_b, 3)
    init(eng, qureg_c, 21)

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 0, 0, 0, 0], qureg_c))
    init(eng, qureg_a, 2)
    init(eng, qureg_b, 3)

    with Compute(eng):
        MultiplyQuantum | (qureg_a, qureg_b, qureg_c)
    Uncompute(eng)

    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 1, 0], qureg_a))
    assert 1.0 == pytest.approx(eng.backend.get_probability([1, 1, 0], qureg_b))
    assert 1.0 == pytest.approx(eng.backend.get_probability([0, 0, 0, 0, 0, 0, 0], qureg_c))
