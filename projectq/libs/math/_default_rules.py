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
"""
Registers a few default replacement rules for Shor's algorithm to work
(see Examples).
"""

from projectq.meta import Control
from projectq.cengines import DecompositionRule

from ._gates import (
    AddConstant,
    AddConstantModN,
    MultiplyByConstantModN,
    AddQuantum,
    SubtractQuantum,
    ComparatorQuantum,
    DivideQuantum,
    MultiplyQuantum,
)

from ._gates import (
    _InverseAddQuantumGate,
    _InverseDivideQuantumGate,
    _InverseMultiplyQuantumGate,
)

from ._constantmath import (
    add_constant,
    add_constant_modN,
    mul_by_constant_modN,
)

from ._quantummath import (
    add_quantum,
    subtract_quantum,
    inverse_add_quantum_carry,
    comparator,
    quantum_conditional_add,
    quantum_division,
    inverse_quantum_division,
    quantum_conditional_add_carry,
    quantum_multiplication,
    inverse_quantum_multiplication,
)


def _replace_addconstant(cmd):
    eng = cmd.engine
    const = cmd.gate.a
    quint = cmd.qubits[0]

    with Control(eng, cmd.control_qubits):
        add_constant(eng, const, quint)


def _replace_addconstmodN(cmd):  # pylint: disable=invalid-name
    eng = cmd.engine
    const = cmd.gate.a
    N = cmd.gate.N
    quint = cmd.qubits[0]

    with Control(eng, cmd.control_qubits):
        add_constant_modN(eng, const, N, quint)


def _replace_multiplybyconstantmodN(cmd):  # pylint: disable=invalid-name
    eng = cmd.engine
    const = cmd.gate.a
    N = cmd.gate.N
    quint = cmd.qubits[0]

    with Control(eng, cmd.control_qubits):
        mul_by_constant_modN(eng, const, N, quint)


def _replace_addquantum(cmd):
    eng = cmd.engine
    if cmd.control_qubits == []:
        quint_a = cmd.qubits[0]
        quint_b = cmd.qubits[1]
        if len(cmd.qubits) == 3:
            carry = cmd.qubits[2]
            add_quantum(eng, quint_a, quint_b, carry)
        else:
            add_quantum(eng, quint_a, quint_b)
    else:
        quint_a = cmd.qubits[0]
        quint_b = cmd.qubits[1]
        if len(cmd.qubits) == 3:
            carry = cmd.qubits[2]
            with Control(eng, cmd.control_qubits):
                quantum_conditional_add_carry(eng, quint_a, quint_b, cmd.control_qubits, carry)
        else:
            with Control(eng, cmd.control_qubits):
                quantum_conditional_add(eng, quint_a, quint_b, cmd.control_qubits)


def _replace_inverse_add_quantum(cmd):
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]

    if len(cmd.qubits) == 3:
        quint_c = cmd.qubits[2]
        with Control(eng, cmd.control_qubits):
            inverse_add_quantum_carry(eng, quint_a, [quint_b, quint_c])
    else:
        with Control(eng, cmd.control_qubits):
            subtract_quantum(eng, quint_a, quint_b)


def _replace_comparator(cmd):
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]
    carry = cmd.qubits[2]

    with Control(eng, cmd.control_qubits):
        comparator(eng, quint_a, quint_b, carry)


def _replace_quantumdivision(cmd):
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]
    quint_c = cmd.qubits[2]

    with Control(eng, cmd.control_qubits):
        quantum_division(eng, quint_a, quint_b, quint_c)


def _replace_inversequantumdivision(cmd):
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]
    quint_c = cmd.qubits[2]

    with Control(eng, cmd.control_qubits):
        inverse_quantum_division(eng, quint_a, quint_b, quint_c)


def _replace_quantummultiplication(cmd):
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]
    quint_c = cmd.qubits[2]

    with Control(eng, cmd.control_qubits):
        quantum_multiplication(eng, quint_a, quint_b, quint_c)


def _replace_inversequantummultiplication(cmd):
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]
    quint_c = cmd.qubits[2]

    with Control(eng, cmd.control_qubits):
        inverse_quantum_multiplication(eng, quint_a, quint_b, quint_c)


all_defined_decomposition_rules = [
    DecompositionRule(AddConstant, _replace_addconstant),
    DecompositionRule(AddConstantModN, _replace_addconstmodN),
    DecompositionRule(MultiplyByConstantModN, _replace_multiplybyconstantmodN),
    DecompositionRule(AddQuantum.__class__, _replace_addquantum),
    DecompositionRule(_InverseAddQuantumGate, _replace_inverse_add_quantum),
    DecompositionRule(SubtractQuantum.__class__, _replace_inverse_add_quantum),
    DecompositionRule(ComparatorQuantum.__class__, _replace_comparator),
    DecompositionRule(DivideQuantum.__class__, _replace_quantumdivision),
    DecompositionRule(_InverseDivideQuantumGate, _replace_inversequantumdivision),
    DecompositionRule(MultiplyQuantum.__class__, _replace_quantummultiplication),
    DecompositionRule(_InverseMultiplyQuantumGate, _replace_inversequantummultiplication),
]
