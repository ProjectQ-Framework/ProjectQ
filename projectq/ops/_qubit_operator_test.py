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
"""Tests for _qubit_operator.py."""
import cmath
import copy
import math

import numpy
import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from ._basics import NotInvertible, NotMergeable
from ._gates import Ph, T, X, Y, Z

from projectq.ops import _qubit_operator as qo


def test_pauli_operator_product_unchanged():
    correct = {
        ('I', 'I'): (1.0, 'I'),
        ('I', 'X'): (1.0, 'X'),
        ('X', 'I'): (1.0, 'X'),
        ('I', 'Y'): (1.0, 'Y'),
        ('Y', 'I'): (1.0, 'Y'),
        ('I', 'Z'): (1.0, 'Z'),
        ('Z', 'I'): (1.0, 'Z'),
        ('X', 'X'): (1.0, 'I'),
        ('Y', 'Y'): (1.0, 'I'),
        ('Z', 'Z'): (1.0, 'I'),
        ('X', 'Y'): (1.0j, 'Z'),
        ('X', 'Z'): (-1.0j, 'Y'),
        ('Y', 'X'): (-1.0j, 'Z'),
        ('Y', 'Z'): (1.0j, 'X'),
        ('Z', 'X'): (1.0j, 'Y'),
        ('Z', 'Y'): (-1.0j, 'X'),
    }
    assert qo._PAULI_OPERATOR_PRODUCTS == correct


def test_init_defaults():
    loc_op = qo.QubitOperator()
    assert len(loc_op.terms) == 0


@pytest.mark.parametrize("coefficient", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j)])
def test_init_tuple(coefficient):
    loc_op = ((0, 'X'), (5, 'Y'), (6, 'Z'))
    qubit_op = qo.QubitOperator(loc_op, coefficient)
    assert len(qubit_op.terms) == 1
    assert qubit_op.terms[loc_op] == coefficient


def test_init_str():
    qubit_op = qo.QubitOperator('X0 Y5 Z12', -1.0)
    correct = ((0, 'X'), (5, 'Y'), (12, 'Z'))
    assert correct in qubit_op.terms
    assert qubit_op.terms[correct] == -1.0


def test_init_str_identity():
    qubit_op = qo.QubitOperator('', 2.0)
    assert len(qubit_op.terms) == 1
    assert () in qubit_op.terms
    assert qubit_op.terms[()] == pytest.approx(2.0)


def test_init_bad_term():
    with pytest.raises(ValueError):
        qo.QubitOperator(list())


def test_init_bad_coefficient():
    with pytest.raises(ValueError):
        qo.QubitOperator('X0', "0.5")


def test_init_bad_action():
    with pytest.raises(ValueError):
        qo.QubitOperator('Q0')


def test_init_bad_action_in_tuple():
    with pytest.raises(ValueError):
        qo.QubitOperator(((1, 'Q'),))


def test_init_bad_qubit_num_in_tuple():
    with pytest.raises(qo.QubitOperatorError):
        qo.QubitOperator((("1", 'X'),))


def test_init_bad_tuple():
    with pytest.raises(ValueError):
        qo.QubitOperator(((0, 1, 'X'),))


def test_init_bad_str():
    with pytest.raises(ValueError):
        qo.QubitOperator('X')


def test_init_bad_qubit_num():
    with pytest.raises(qo.QubitOperatorError):
        qo.QubitOperator('X-1')


def test_isclose_abs_tol():
    a = qo.QubitOperator('X0', -1.0)
    b = qo.QubitOperator('X0', -1.05)
    c = qo.QubitOperator('X0', -1.11)
    assert a.isclose(b, rel_tol=1e-14, abs_tol=0.1)
    assert not a.isclose(c, rel_tol=1e-14, abs_tol=0.1)
    a = qo.QubitOperator('X0', -1.0j)
    b = qo.QubitOperator('X0', -1.05j)
    c = qo.QubitOperator('X0', -1.11j)
    assert a.isclose(b, rel_tol=1e-14, abs_tol=0.1)
    assert not a.isclose(c, rel_tol=1e-14, abs_tol=0.1)


def test_compress():
    a = qo.QubitOperator('X0', 0.9e-12)
    assert len(a.terms) == 1
    a.compress()
    assert len(a.terms) == 0
    a = qo.QubitOperator('X0', 1.0 + 1j)
    a.compress(0.5)
    assert len(a.terms) == 1
    for term in a.terms:
        assert a.terms[term] == 1.0 + 1j
    a = qo.QubitOperator('X0', 1.1 + 1j)
    a.compress(1.0)
    assert len(a.terms) == 1
    for term in a.terms:
        assert a.terms[term] == 1.1
    a = qo.QubitOperator('X0', 1.1 + 1j) + qo.QubitOperator('X1', 1.0e-6j)
    a.compress()
    assert len(a.terms) == 2
    for term in a.terms:
        assert isinstance(a.terms[term], complex)
    a.compress(1.0e-5)
    assert len(a.terms) == 1
    for term in a.terms:
        assert isinstance(a.terms[term], complex)
    a.compress(1.0)
    assert len(a.terms) == 1
    for term in a.terms:
        assert isinstance(a.terms[term], float)


def test_isclose_rel_tol():
    a = qo.QubitOperator('X0', 1)
    b = qo.QubitOperator('X0', 2)
    assert a.isclose(b, rel_tol=2.5, abs_tol=0.1)
    # Test symmetry
    assert a.isclose(b, rel_tol=1, abs_tol=0.1)
    assert b.isclose(a, rel_tol=1, abs_tol=0.1)


def test_isclose_zero_terms():
    op = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j) * 0
    assert op.isclose(qo.QubitOperator((), 0.0), rel_tol=1e-12, abs_tol=1e-12)
    assert qo.QubitOperator((), 0.0).isclose(op, rel_tol=1e-12, abs_tol=1e-12)


def test_isclose_different_terms():
    a = qo.QubitOperator(((1, 'Y'),), -0.1j)
    b = qo.QubitOperator(((1, 'X'),), -0.1j)
    assert a.isclose(b, rel_tol=1e-12, abs_tol=0.2)
    assert not a.isclose(b, rel_tol=1e-12, abs_tol=0.05)
    assert b.isclose(a, rel_tol=1e-12, abs_tol=0.2)
    assert not b.isclose(a, rel_tol=1e-12, abs_tol=0.05)


def test_isclose_different_num_terms():
    a = qo.QubitOperator(((1, 'Y'),), -0.1j)
    a += qo.QubitOperator(((2, 'Y'),), -0.1j)
    b = qo.QubitOperator(((1, 'X'),), -0.1j)
    assert not b.isclose(a, rel_tol=1e-12, abs_tol=0.05)
    assert not a.isclose(b, rel_tol=1e-12, abs_tol=0.05)


def test_get_inverse():
    qo0 = qo.QubitOperator("X1 Z2", cmath.exp(0.6j))
    qo1 = qo.QubitOperator("", 1j)
    assert qo0.get_inverse().isclose(qo.QubitOperator("X1 Z2", cmath.exp(-0.6j)))
    assert qo1.get_inverse().isclose(qo.QubitOperator("", -1j))
    qo0 += qo1
    with pytest.raises(NotInvertible):
        qo0.get_inverse()


def test_get_merged():
    qo0 = qo.QubitOperator("X1 Z2", 1j)
    qo1 = qo.QubitOperator("Y3", 1j)
    assert qo0.isclose(qo.QubitOperator("X1 Z2", 1j))
    assert qo1.isclose(qo.QubitOperator("Y3", 1j))
    assert qo0.get_merged(qo1).isclose(qo.QubitOperator("X1 Z2 Y3", -1))
    with pytest.raises(NotMergeable):
        qo1.get_merged(T)
    qo2 = qo0 + qo1
    with pytest.raises(NotMergeable):
        qo2.get_merged(qo0)
    with pytest.raises(NotMergeable):
        qo0.get_merged(qo2)


def test_or_one_qubit():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(3)
    eng.flush()
    identity = qo.QubitOperator("", 1j)
    x = qo.QubitOperator("X1", cmath.exp(0.5j))
    y = qo.QubitOperator("Y2", cmath.exp(0.6j))
    z = qo.QubitOperator("Z0", cmath.exp(4.5j))
    identity | qureg
    eng.flush()
    x | qureg
    eng.flush()
    y | qureg
    eng.flush()
    z | qureg
    eng.flush()
    assert saving_backend.received_commands[4].gate == Ph(math.pi / 2.0)

    assert saving_backend.received_commands[6].gate == X
    assert saving_backend.received_commands[6].qubits == ([qureg[1]],)
    assert saving_backend.received_commands[7].gate == Ph(0.5)
    assert saving_backend.received_commands[7].qubits == ([qureg[1]],)

    assert saving_backend.received_commands[9].gate == Y
    assert saving_backend.received_commands[9].qubits == ([qureg[2]],)
    assert saving_backend.received_commands[10].gate == Ph(0.6)
    assert saving_backend.received_commands[10].qubits == ([qureg[2]],)

    assert saving_backend.received_commands[12].gate == Z
    assert saving_backend.received_commands[12].qubits == ([qureg[0]],)
    assert saving_backend.received_commands[13].gate == Ph(4.5)
    assert saving_backend.received_commands[13].qubits == ([qureg[0]],)


def test_wrong_input():
    eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    op0 = qo.QubitOperator("X1", 0.99)
    with pytest.raises(TypeError):
        op0 | qureg
    op1 = qo.QubitOperator("X2", 1)
    with pytest.raises(ValueError):
        op1 | qureg[1]
    with pytest.raises(TypeError):
        op0 | (qureg[1], qureg[2])
    op2 = op0 + op1
    with pytest.raises(TypeError):
        op2 | qureg


def test_rescaling_of_indices():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(4)
    eng.flush()
    op = qo.QubitOperator("X0 Y1 Z3", 1j)
    op | qureg
    eng.flush()
    assert saving_backend.received_commands[5].gate.isclose(qo.QubitOperator("X0 Y1 Z2", 1j))
    # test that gate creates a new QubitOperator
    assert op.isclose(qo.QubitOperator("X0 Y1 Z3", 1j))


def test_imul_inplace():
    qubit_op = qo.QubitOperator("X1")
    prev_id = id(qubit_op)
    qubit_op *= 3.0
    assert id(qubit_op) == prev_id


@pytest.mark.parametrize("multiplier", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j)])
def test_imul_scalar(multiplier):
    loc_op = ((1, 'X'), (2, 'Y'))
    qubit_op = qo.QubitOperator(loc_op)
    qubit_op *= multiplier
    assert qubit_op.terms[loc_op] == pytest.approx(multiplier)


def test_imul_qubit_op():
    op1 = qo.QubitOperator(((0, 'Y'), (3, 'X'), (8, 'Z'), (11, 'X')), 3.0j)
    op2 = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    op1 *= op2
    correct_coefficient = 1.0j * 3.0j * 0.5
    correct_term = ((0, 'Y'), (1, 'X'), (3, 'Z'), (11, 'X'))
    assert len(op1.terms) == 1
    assert correct_term in op1.terms
    assert op1.terms[correct_term] == correct_coefficient


def test_imul_qubit_op_2():
    op3 = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j)
    op4 = qo.QubitOperator(((1, 'Y'), (0, 'X'), (2, 'Z')), -1.5)
    op3 *= op4
    op4 *= op3
    assert ((2, 'Z'),) in op3.terms
    assert op3.terms[((2, 'Z'),)] == 1.5j


def test_imul_bidir():
    op_a = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j)
    op_b = qo.QubitOperator(((1, 'Y'), (0, 'X'), (2, 'Z')), -1.5)
    op_a *= op_b
    op_b *= op_a
    assert ((2, 'Z'),) in op_a.terms
    assert op_a.terms[((2, 'Z'),)] == 1.5j
    assert ((0, 'X'), (1, 'Y')) in op_b.terms
    assert op_b.terms[((0, 'X'), (1, 'Y'))] == -2.25j


def test_imul_bad_multiplier():
    op = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j)
    with pytest.raises(TypeError):
        op *= "1"


def test_mul_by_scalarzero():
    op = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j) * 0
    assert ((0, 'X'), (1, 'Y')) in op.terms
    assert op.terms[((0, 'X'), (1, 'Y'))] == pytest.approx(0.0)


def test_mul_bad_multiplier():
    op = qo.QubitOperator(((1, 'Y'), (0, 'X')), -1j)
    with pytest.raises(TypeError):
        op = op * "0.5"


def test_mul_out_of_place():
    op1 = qo.QubitOperator(((0, 'Y'), (3, 'X'), (8, 'Z'), (11, 'X')), 3.0j)
    op2 = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    op3 = op1 * op2
    correct_coefficient = 1.0j * 3.0j * 0.5
    correct_term = ((0, 'Y'), (1, 'X'), (3, 'Z'), (11, 'X'))
    assert op1.isclose(qo.QubitOperator(((0, 'Y'), (3, 'X'), (8, 'Z'), (11, 'X')), 3.0j))
    assert op2.isclose(qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5))
    assert op3.isclose(qo.QubitOperator(correct_term, correct_coefficient))


def test_mul_npfloat64():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y')), 0.5)
    res = op * numpy.float64(0.5)
    assert res.isclose(qo.QubitOperator(((1, 'X'), (3, 'Y')), 0.5 * 0.5))


def test_mul_multiple_terms():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    op += qo.QubitOperator(((1, 'Z'), (3, 'X'), (8, 'Z')), 1.2)
    op += qo.QubitOperator(((1, 'Z'), (3, 'Y'), (9, 'Z')), 1.4j)
    res = op * op
    correct = qo.QubitOperator((), 0.5 ** 2 + 1.2 ** 2 + 1.4j ** 2)
    correct += qo.QubitOperator(((1, 'Y'), (3, 'Z')), 2j * 1j * 0.5 * 1.2)
    assert res.isclose(correct)


@pytest.mark.parametrize("multiplier", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j)])
def test_rmul_scalar(multiplier):
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    res1 = op * multiplier
    res2 = multiplier * op
    assert res1.isclose(res2)


def test_rmul_bad_multiplier():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    with pytest.raises(TypeError):
        op = "0.5" * op


@pytest.mark.parametrize("divisor", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j), 2])
def test_truediv_and_div(divisor):
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    original = copy.deepcopy(op)
    res = op / divisor
    correct = op * (1.0 / divisor)
    assert res.isclose(correct)
    # Test if done out of place
    assert op.isclose(original)


def test_truediv_bad_divisor():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    with pytest.raises(TypeError):
        op = op / "0.5"


@pytest.mark.parametrize("divisor", [0.5, 0.6j, numpy.float64(2.303), numpy.complex128(-1j), 2])
def test_itruediv_and_idiv(divisor):
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    original = copy.deepcopy(op)
    correct = op * (1.0 / divisor)
    op /= divisor
    assert op.isclose(correct)
    # Test if done in-place
    assert not op.isclose(original)


def test_itruediv_bad_divisor():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    with pytest.raises(TypeError):
        op /= "0.5"


def test_iadd_cancellation():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    a += qo.QubitOperator(term_b, -1.0)
    assert len(a.terms) == 0


def test_iadd_different_term():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    a += qo.QubitOperator(term_b, 0.5)
    assert len(a.terms) == 2
    assert a.terms[term_a] == pytest.approx(1.0)
    assert a.terms[term_b] == pytest.approx(0.5)
    a += qo.QubitOperator(term_b, 0.5)
    assert len(a.terms) == 2
    assert a.terms[term_a] == pytest.approx(1.0)
    assert a.terms[term_b] == pytest.approx(1.0)


def test_iadd_bad_addend():
    op = qo.QubitOperator((), 1.0)
    with pytest.raises(TypeError):
        op += "0.5"


def test_add():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    b = qo.QubitOperator(term_b, 0.5)
    res = a + b + b
    assert len(res.terms) == 2
    assert res.terms[term_a] == pytest.approx(1.0)
    assert res.terms[term_b] == pytest.approx(1.0)
    # Test out of place
    assert a.isclose(qo.QubitOperator(term_a, 1.0))
    assert b.isclose(qo.QubitOperator(term_b, 0.5))


def test_add_bad_addend():
    op = qo.QubitOperator((), 1.0)
    with pytest.raises(TypeError):
        op = op + "0.5"


def test_sub():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    b = qo.QubitOperator(term_b, 0.5)
    res = a - b
    assert len(res.terms) == 2
    assert res.terms[term_a] == pytest.approx(1.0)
    assert res.terms[term_b] == pytest.approx(-0.5)
    res2 = b - a
    assert len(res2.terms) == 2
    assert res2.terms[term_a] == pytest.approx(-1.0)
    assert res2.terms[term_b] == pytest.approx(0.5)


def test_sub_bad_subtrahend():
    op = qo.QubitOperator((), 1.0)
    with pytest.raises(TypeError):
        op = op - "0.5"


def test_isub_different_term():
    term_a = ((1, 'X'), (3, 'Y'), (8, 'Z'))
    term_b = ((1, 'Z'), (3, 'Y'), (8, 'Z'))
    a = qo.QubitOperator(term_a, 1.0)
    a -= qo.QubitOperator(term_b, 0.5)
    assert len(a.terms) == 2
    assert a.terms[term_a] == pytest.approx(1.0)
    assert a.terms[term_b] == pytest.approx(-0.5)
    a -= qo.QubitOperator(term_b, 0.5)
    assert len(a.terms) == 2
    assert a.terms[term_a] == pytest.approx(1.0)
    assert a.terms[term_b] == pytest.approx(-1.0)
    b = qo.QubitOperator(term_a, 1.0)
    b -= qo.QubitOperator(term_a, 1.0)
    assert b.terms == {}


def test_isub_bad_addend():
    op = qo.QubitOperator((), 1.0)
    with pytest.raises(TypeError):
        op -= "0.5"


def test_neg():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    -op
    # out of place
    assert op.isclose(qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5))
    correct = -1.0 * op
    assert correct.isclose(-op)


def test_str():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    assert str(op) == "0.5 X1 Y3 Z8"
    op2 = qo.QubitOperator((), 2)
    assert str(op2) == "2 I"


def test_hash():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    assert hash(op) == hash("0.5 X1 Y3 Z8")


def test_str_empty():
    op = qo.QubitOperator()
    assert str(op) == '0'


def test_str_multiple_terms():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    op += qo.QubitOperator(((1, 'Y'), (3, 'Y'), (8, 'Z')), 0.6)
    assert str(op) == "0.5 X1 Y3 Z8 +\n0.6 Y1 Y3 Z8" or str(op) == "0.6 Y1 Y3 Z8 +\n0.5 X1 Y3 Z8"
    op2 = qo.QubitOperator((), 2)
    assert str(op2) == "2 I"


def test_rep():
    op = qo.QubitOperator(((1, 'X'), (3, 'Y'), (8, 'Z')), 0.5)
    # Not necessary, repr could do something in addition
    assert repr(op) == str(op)
