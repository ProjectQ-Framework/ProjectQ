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

"""Definition of some mathematical quantum operations"""

from projectq.ops import All, X, CNOT
from projectq.meta import Control
from ._gates import AddQuantum, SubtractQuantum


def add_quantum(eng, quint_a, quint_b, carry=None):
    """
    Adds two quantum integers, i.e.,

    |a0...a(n-1)>|b(0)...b(n-1)>|c> -> |a0...a(n-1)>|b+a(0)...b+a(n)>

    (only works if quint_a and quint_b are the same size and carry is a single
    qubit)

    Args:
        eng (MainEngine): ProjectQ MainEngine
        quint_a (list): Quantum register (or list of qubits)
        quint_b (list): Quantum register (or list of qubits)
        carry (list): Carry qubit

    Notes:
        Ancilla: 0, size: 7n-6, toffoli: 2n-1, depth: 5n-3.

    .. rubric:: References

    Quantum addition using ripple carry from: https://arxiv.org/pdf/0910.2530.pdf
    """
    # pylint: disable = pointless-statement

    if len(quint_a) != len(quint_b):
        raise ValueError('quint_a and quint_b must have the same size!')
    if carry and len(carry) != 1:
        raise ValueError('Either no carry bit or a single carry qubit is allowed!')

    n_qubits = len(quint_a) + 1

    for i in range(1, n_qubits - 1):
        CNOT | (quint_a[i], quint_b[i])

    if carry:
        CNOT | (quint_a[n_qubits - 2], carry)

    for j in range(n_qubits - 3, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(0, n_qubits - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    if carry:
        with Control(eng, [quint_a[n_qubits - 2], quint_b[n_qubits - 2]]):
            X | carry

    for i in range(n_qubits - 2, 0, -1):  # noqa: E741
        CNOT | (quint_a[i], quint_b[i])
        with Control(eng, [quint_a[i - 1], quint_b[i - 1]]):
            X | quint_a[i]

    for j in range(1, n_qubits - 2):
        CNOT | (quint_a[j], quint_a[j + 1])

    for n_qubits in range(0, n_qubits - 1):
        CNOT | (quint_a[n_qubits], quint_b[n_qubits])


def subtract_quantum(eng, quint_a, quint_b):
    """
    Subtracts two quantum integers, i.e.,

    |a>|b> -> |a>|b-a>

    (only works if quint_a and quint_b are the same size)

    Args:
        eng (MainEngine): ProjectQ MainEngine
        quint_a (list): Quantum register (or list of qubits)
        quint_b (list): Quantum register (or list of qubits)

    Notes:
        Quantum subtraction using bitwise complementation of quantum adder: b-a = (a + b')'. Same as the quantum
        addition circuit except that the steps involving the carry qubit are left out and complement b at the start
        and at the end of the circuit is added.

        Ancilla: 0, size: 9n-8, toffoli: 2n-2, depth: 5n-5.


    .. rubric:: References

    Quantum addition using ripple carry from:
    https://arxiv.org/pdf/0910.2530.pdf
    """
    # pylint: disable = pointless-statement, expression-not-assigned

    if len(quint_a) != len(quint_b):
        raise ValueError('quint_a and quint_b must have the same size!')
    n_qubits = len(quint_a) + 1

    All(X) | quint_b

    for i in range(1, n_qubits - 1):
        CNOT | (quint_a[i], quint_b[i])

    for j in range(n_qubits - 3, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(0, n_qubits - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    for i in range(n_qubits - 2, 0, -1):  # noqa: E741
        CNOT | (quint_a[i], quint_b[i])
        with Control(eng, [quint_a[i - 1], quint_b[i - 1]]):
            X | quint_a[i]

    for j in range(1, n_qubits - 2):
        CNOT | (quint_a[j], quint_a[j + 1])

    for n_qubits in range(0, n_qubits - 1):
        CNOT | (quint_a[n_qubits], quint_b[n_qubits])

    All(X) | quint_b


def inverse_add_quantum_carry(eng, quint_a, quint_b):
    """
    Inverse of quantum addition with carry

    Args:
        eng (MainEngine): ProjectQ MainEngine
        quint_a (list): Quantum register (or list of qubits)
        quint_b (list): Quantum register (or list of qubits)
    """
    # pylint: disable = pointless-statement, expression-not-assigned
    # pylint: disable = unused-argument

    if len(quint_a) != len(quint_b[0]):
        raise ValueError('quint_a and quint_b must have the same size!')

    All(X) | quint_b[0]
    X | quint_b[1][0]

    AddQuantum | (quint_a, quint_b[0], quint_b[1])

    All(X) | quint_b[0]
    X | quint_b[1][0]


def comparator(eng, quint_a, quint_b, comp):
    """
    Compares the size of two quantum integers, i.e,

    if a>b: |a>|b>|c> -> |a>|b>|c+1>

    else:   |a>|b>|c> -> |a>|b>|c>

    (only works if quint_a and quint_b are the same size and the comparator is 1 qubit)

    Args:
        eng (MainEngine): ProjectQ MainEngine
        quint_a (list): Quantum register (or list of qubits)
        quint_b (list): Quantum register (or list of qubits)
        comp (Qubit): Comparator qubit

    Notes:
        Comparator flipping a compare qubit by computing the high bit of b-a, which is 1 if and only if a > b. The
        high bit is computed using the first half of circuit in AddQuantum (such that the high bit is written to the
        carry qubit) and then undoing the first half of the circuit. By complementing b at the start and b+a at the
        end the high bit of b-a is calculated.

        Ancilla: 0, size: 8n-3, toffoli: 2n+1, depth: 4n+3.
    """
    # pylint: disable = pointless-statement, expression-not-assigned

    if len(quint_a) != len(quint_b):
        raise ValueError('quint_a and quint_b must have the same size!')
    if len(comp) != 1:
        raise ValueError('Comparator output qubit must be a single qubit!')

    n_qubits = len(quint_a) + 1

    All(X) | quint_b

    for i in range(1, n_qubits - 1):
        CNOT | (quint_a[i], quint_b[i])

    CNOT | (quint_a[n_qubits - 2], comp)

    for j in range(n_qubits - 3, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(0, n_qubits - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    with Control(eng, [quint_a[n_qubits - 2], quint_b[n_qubits - 2]]):
        X | comp

    for k in range(0, n_qubits - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    for j in range(n_qubits - 3, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for i in range(1, n_qubits - 1):
        CNOT | (quint_a[i], quint_b[i])

    All(X) | quint_b


def quantum_conditional_add(eng, quint_a, quint_b, conditional):
    """
    Adds up two quantum integers if conditional is high, i.e.,

    |a>|b>|c> -> |a>|b+a>|c>
    (without a carry out qubit)

    if conditional is low, no operation is performed, i.e.,
    |a>|b>|c> -> |a>|b>|c>

    Args:
        eng (MainEngine): ProjectQ MainEngine
        quint_a (list): Quantum register (or list of qubits)
        quint_b (list): Quantum register (or list of qubits)
        conditional (list): Conditional qubit

    Notes:
        Ancilla: 0, Size: 7n-7, Toffoli: 3n-3, Depth: 5n-3.

    .. rubric:: References

    Quantum Conditional Add from https://arxiv.org/pdf/1609.01241.pdf
    """
    # pylint: disable = pointless-statement, expression-not-assigned

    if len(quint_a) != len(quint_b):
        raise ValueError('quint_a and quint_b must have the same size!')
    if len(conditional) != 1:
        raise ValueError('Conditional qubit must be a single qubit!')

    n_qubits = len(quint_a) + 1

    for i in range(1, n_qubits - 1):
        CNOT | (quint_a[i], quint_b[i])

    for i in range(n_qubits - 2, 1, -1):
        CNOT | (quint_a[i - 1], quint_a[i])

    for k in range(0, n_qubits - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    with Control(eng, [quint_a[n_qubits - 2], conditional[0]]):
        X | quint_b[n_qubits - 2]

    for i in range(n_qubits - 2, 0, -1):  # noqa: E741
        with Control(eng, [quint_a[i - 1], quint_b[i - 1]]):
            X | quint_a[i]
        with Control(eng, [quint_a[i - 1], conditional[0]]):
            X | (quint_b[i - 1])

    for j in range(1, n_qubits - 2):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(1, n_qubits - 1):
        CNOT | (quint_a[k], quint_b[k])


def quantum_division(eng, dividend, remainder, divisor):
    """
    Performs restoring integer division, i.e.,

    |dividend>|remainder>|divisor> -> |remainder>|quotient>|divisor>

    (only works if all three qubits are of equal length)

    Args:
        eng (MainEngine): ProjectQ MainEngine
        dividend (list): Quantum register (or list of qubits)
        remainder (list): Quantum register (or list of qubits)
        divisor (list): Quantum register (or list of qubits)

    Notes:
        Ancilla: n, size 16n^2 - 13, toffoli: 5n^2 -5 , depth: 10n^2-6.

    .. rubric:: References

    Quantum Restoring Integer Division from:
    https://arxiv.org/pdf/1609.01241.pdf.
    """
    # The circuit consits of three parts
    # i) leftshift
    # ii) subtraction
    # iii) conditional add operation.

    if not len(dividend) == len(remainder) == len(divisor):
        raise ValueError('Size mismatch in dividend, divisor and remainder!')

    j = len(remainder)
    n_dividend = len(dividend)

    while j != 0:
        combined_reg = []

        combined_reg.append(dividend[n_dividend - 1])

        for i in range(0, n_dividend - 1):
            combined_reg.append(remainder[i])

        SubtractQuantum | (divisor[0:n_dividend], combined_reg)
        CNOT | (combined_reg[n_dividend - 1], remainder[n_dividend - 1])
        with Control(eng, remainder[n_dividend - 1]):
            AddQuantum | (divisor[0:n_dividend], combined_reg)
        X | remainder[n_dividend - 1]

        remainder.insert(0, dividend[n_dividend - 1])
        dividend.insert(0, remainder[n_dividend])
        del remainder[n_dividend]
        del dividend[n_dividend]

        j -= 1


def inverse_quantum_division(eng, remainder, quotient, divisor):
    """
    Performs the inverse of a restoring integer division, i.e.,

    |remainder>|quotient>|divisor> ->  |dividend>|remainder(0)>|divisor>

    Args:
        eng (MainEngine): ProjectQ MainEngine
        dividend (list): Quantum register (or list of qubits)
        remainder (list): Quantum register (or list of qubits)
        divisor (list): Quantum register (or list of qubits)
    """
    if not len(quotient) == len(remainder) == len(divisor):
        raise ValueError('Size mismatch in quotient, divisor and remainder!')

    j = 0
    n_quotient = len(quotient)

    while j != n_quotient:
        X | quotient[0]
        with Control(eng, quotient[0]):
            SubtractQuantum | (divisor, remainder)
        CNOT | (remainder[-1], quotient[0])

        AddQuantum | (divisor, remainder)

        remainder.insert(n_quotient, quotient[0])
        quotient.insert(n_quotient, remainder[0])
        del remainder[0]
        del quotient[0]
        j += 1


def quantum_conditional_add_carry(eng, quint_a, quint_b, ctrl, z):  # pylint: disable=invalid-name
    """
    Adds up two quantum integers if the control qubit is |1>, i.e.,

    |a>|b>|ctrl>|z(0)z(1)> -> |a>|s(0)...s(n-1)>|ctrl>|s(n)z(1)>
    (where s denotes the sum of a and b)

    If the control qubit is |0> no operation is performed:

    |a>|b>|ctrl>|z(0)z(1)> -> |a>|b>|ctrl>|z(0)z(1)>

    (only works if quint_a and quint_b are of the same size, ctrl is a
    single qubit and z is a quantum register with 2 qubits.

    Args:
        eng (MainEngine): ProjectQ MainEngine
        quint_a (list): Quantum register (or list of qubits)
        quint_b (list): Quantum register (or list of qubits)
        ctrl (list): Control qubit
        z (list): Quantum register with 2 qubits

    Notes:
        Ancilla: 2, size: 7n - 4, toffoli: 3n + 2, depth: 5n.

    .. rubric:: References

    Quantum conditional add with no input carry from: https://arxiv.org/pdf/1706.05113.pdf
    """
    if len(quint_a) != len(quint_b):
        raise ValueError('quint_a and quint_b must have the same size!')
    if len(ctrl) != 1:
        raise ValueError('Only a single control qubit is allowed!')
    if len(z) != 2:
        raise ValueError('Z quantum register must have 2 qubits!')

    n_a = len(quint_a)

    for i in range(1, n_a):
        CNOT | (quint_a[i], quint_b[i])

    with Control(eng, [quint_a[n_a - 1], ctrl[0]]):
        X | z[0]

    for j in range(n_a - 2, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(0, n_a - 1):
        with Control(eng, [quint_b[k], quint_a[k]]):
            X | quint_a[k + 1]

    with Control(eng, [quint_b[n_a - 1], quint_a[n_a - 1]]):
        X | z[1]

    with Control(eng, [ctrl[0], z[1]]):
        X | z[0]

    with Control(eng, [quint_b[n_a - 1], quint_a[n_a - 1]]):
        X | z[1]

    for i in range(n_a - 1, 0, -1):  # noqa: E741
        with Control(eng, [ctrl[0], quint_a[i]]):
            X | quint_b[i]
        with Control(eng, [quint_a[i - 1], quint_b[i - 1]]):
            X | quint_a[i]

    with Control(eng, [quint_a[0], ctrl[0]]):
        X | quint_b[0]

    for j in range(1, n_a - 1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for n_a in range(1, n_a):
        CNOT | (quint_a[n_a], quint_b[n_a])


def quantum_multiplication(eng, quint_a, quint_b, product):
    """
    Multiplies two quantum integers, i.e,

    |a>|b>|0> -> |a>|b>|a*b>

    (only works if quint_a and quint_b are of the same size, n qubits and product has size 2n+1).

    Args:
        eng (MainEngine): ProjectQ MainEngine
        quint_a (list): Quantum register (or list of qubits)
        quint_b (list): Quantum register (or list of qubits)
        product (list): Quantum register (or list of qubits) storing
            the result

    Notes:
        Ancilla: 2n + 1, size: 7n^2 - 9n + 4, toffoli: 5n^2 - 4n, depth: 3n^2 - 2.

    .. rubric:: References

    Quantum multiplication from: https://arxiv.org/abs/1706.05113.

    """
    n_a = len(quint_a)

    if len(quint_a) != len(quint_b):
        raise ValueError('quint_a and quint_b must have the same size!')
    if len(product) != ((2 * n_a) + 1):
        raise ValueError('product size must be 2*n + 1')

    for i in range(0, n_a):
        with Control(eng, [quint_a[i], quint_b[0]]):
            X | product[i]

    with Control(eng, quint_b[1]):
        AddQuantum | (
            quint_a[0 : (n_a - 1)],  # noqa: E203
            product[1:n_a],
            [product[n_a + 1], product[n_a + 2]],
        )

    for j in range(2, n_a):
        with Control(eng, quint_b[j]):
            AddQuantum | (
                quint_a[0 : (n_a - 1)],  # noqa: E203
                product[(0 + j) : (n_a - 1 + j)],  # noqa: E203
                [product[n_a + j], product[n_a + j + 1]],
            )


def inverse_quantum_multiplication(eng, quint_a, quint_b, product):
    """
    Inverse of the multiplication of two quantum integers, i.e,

    |a>|b>|a*b> -> |a>|b>|0>

    (only works if quint_a and quint_b are of the same size, n qubits and product has size 2n+1)

    Args:
        eng (MainEngine): ProjectQ MainEngine
        quint_a (list): Quantum register (or list of qubits)
        quint_b (list): Quantum register (or list of qubits)
        product (list): Quantum register (or list of qubits) storing the result

    """
    n_a = len(quint_a)

    if len(quint_a) != len(quint_b):
        raise ValueError('quint_a and quint_b must have the same size!')
    if len(product) != ((2 * n_a) + 1):
        raise ValueError('product size must be 2*n + 1')

    for j in range(2, n_a):
        with Control(eng, quint_b[j]):
            SubtractQuantum | (
                quint_a[0 : (n_a - 1)],  # noqa: E203
                product[(0 + j) : (n_a - 1 + j)],  # noqa: E203
                [product[n_a + j], product[n_a + j + 1]],
            )
    for i in range(0, n_a):
        with Control(eng, [quint_a[i], quint_b[0]]):
            X | product[i]

    with Control(eng, quint_b[1]):
        SubtractQuantum | (
            quint_a[0 : (n_a - 1)],  # noqa: E203
            product[1:n_a],
            [product[n_a + 1], product[n_a + 2]],
        )
