

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

import math

from projectq.ops import All, X, Swap, Measure, CNOT
from projectq.meta import Control, Compute, Uncompute, CustomUncompute, Dagger
from ._gates import (AddQuantum, 
                     SubtractQuantum) 
#from projectq.libs.math._gates_math_test import get_all_probabilities

"""
Quantum addition using ripple carry from: https://arxiv.org/pdf/0910.2530.pdf.
With carry bit,
Ancilla: 0, Size: 7n-6, Toffoli: 2n-1, Depth: 5n-3.
Without carry?
"""
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


def add_quantum(eng, quint_a, quint_b, carry=[]):
    """
    Adds two quantum integers, i.e.,

    |a0...a(n-1)>|b(0)...b(n-1)>|c> -> |a0...a(n-1)>|b+a(0)...b+a(n)>

    (only works if quint_a and quint_b are the same size and carry is a single 
    qubit)
    """

    assert(len(quint_a) == len(quint_b))
    assert(len(carry) == 1 or carry == [])

    n = len(quint_a) + 1

    for i in range(1, n - 1):
        CNOT | (quint_a[i], quint_b[i])

    if carry != []:
        CNOT | (quint_a[n - 2], carry)

    for j in range(n - 3, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(0, n - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    if carry != []:
        with Control(eng, [quint_a[n - 2], quint_b[n - 2]]):
            X | carry

    for l in range(n - 2, 0, -1):
        CNOT | (quint_a[l], quint_b[l])
        with Control(eng, [quint_a[l - 1], quint_b[l - 1]]):
            X | quint_a[l]

    for m in range(1, n - 2):
        CNOT | (quint_a[m], quint_a[m + 1])

    for n in range(0, n - 1):
        CNOT | (quint_a[n], quint_b[n])



"""
Quantum subtraction using bitwise complementation of quantum adder: 
b-a = (a + b')'. Same as the quantum addition circuit except that the steps 
involving the carry qubit are left out and complement b at the start and at 
the end of the circuit is added.

Ancilla: 0, Size: 9n-8, Toffoli: 2n-2, Depth: 5n-5.
"""


def subtract_quantum(eng, quint_a, quint_b):
    """
    Subtracts two quantum integers, i.e.,

    |a>|b> -> |a>|b-a>

    (only works if quint_a and quint_b are the same size or quint_b is one qubit longer than quint_a)
    """
    assert(len(quint_a) == len(quint_b))
    n = len(quint_a) + 1

    All(X) | quint_b

    for i in range(1, n - 1):
        CNOT | (quint_a[i], quint_b[i])

    for j in range(n - 3, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(0, n - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    for l in range(n - 2, 0, -1):
        CNOT | (quint_a[l], quint_b[l])
        with Control(eng, [quint_a[l - 1], quint_b[l - 1]]):
            X | quint_a[l]

    for m in range(1, n - 2):
        CNOT | (quint_a[m], quint_a[m + 1])

    for n in range(0, n - 1):
        CNOT | (quint_a[n], quint_b[n])

    All(X) | quint_b


def inverse_add_quantum_carry(eng, quint_a, quint_b):

    assert(len(quint_a) == len(quint_b[0]))

    All(X) | quint_b[0]
    X | quint_b[1]

    AddQuantum() | (quint_a, quint_b[0], quint_b[1])

    All(X) | quint_b[0]
    X | quint_b[1]

"""
Comparator flipping a compare qubit by computing the high bit of b-a, which is
1 if and only if a > b. The high bit is computed using the first half of 
circuit in AddQuantum (such that the high bit is written to  the carry qubit) 
and then undoing the first half of the circuit. By complementing b at the 
start and b+a at the end the high bit of b-a is calculated.

Ancilla: 0, Size: 8n-3, Toffoli: 2n+1, Depth: 4n+3.
"""


def comparator(eng, quint_a, quint_b, comparator):
    """
    Compares the size of two quantum integers, i.e,

    if a>b: |a>|b>|c> -> |a>|b>|c+1>

    else:   |a>|b>|c> -> |a>|b>|c>

    (only works if quint_a and quint_b are the same size and the comparator
    is 1 qubit)
    """
    assert(len(quint_a) == len(quint_b))
    assert(len(comparator) == 1)

    n = len(quint_a) + 1

    All(X) | quint_b

    for i in range(1, n - 1):
        CNOT | (quint_a[i], quint_b[i])

    CNOT | (quint_a[n - 2], comparator)

    for j in range(n - 3, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(0, n - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    with Control(eng, [quint_a[n - 2], quint_b[n - 2]]):
        X | comparator

    for k in range(0, n - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    for j in range(n - 3, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for i in range(1, n - 1):
        CNOT | (quint_a[i], quint_b[i])

    All(X) | quint_b


"""
Quantum Conditional Add from https://arxiv.org/pdf/1609.01241.pdf.
If an input qubit labeled "conditional" is high, the two quantum integers
are added, if "conditional" is low no operation is performed.

Ancilla: 0, Size: 7n-7, Toffoli: 3n-3, Depth: 5n-3. 
"""


def quantum_conditional_add(eng, quint_a, quint_b, conditional):
    """
    Adds up two quantum integers if conditional is high, i.e.,

    |a>|b>|c> -> |a>|b+a>|c>
    (without a carry out qubit)

    if conditional is low, no operation is performed, i.e.,
    |a>|b>|c> -> |a>|b>|c>
    """
    assert(len(quint_a) == len(quint_b))
    assert(len(conditional) == 1)

    n = len(quint_a) + 1

    for i in range(1, n - 1):
        CNOT | (quint_a[i], quint_b[i])

    for i in range(n - 2, 1, -1):
        CNOT | (quint_a[i - 1], quint_a[i])

    for k in range(0, n - 2):
        with Control(eng, [quint_a[k], quint_b[k]]):
            X | (quint_a[k + 1])

    with Control(eng, [quint_a[n - 2], conditional[0]]):
        X | quint_b[n - 2]

    for l in range(n - 2, 0, -1):
        with Control(eng, [quint_a[l - 1], quint_b[l - 1]]):
            X | quint_a[l]
        with Control(eng, [quint_a[l - 1], conditional[0]]):
            X | (quint_b[l - 1])

    for m in range(1, n - 2):
        CNOT | (quint_a[m], quint_a[m + 1])

    for o in range(1, n - 1):
        CNOT | (quint_a[o], quint_b[o])


"""
Quantum Restoring Integer Division from: https://arxiv.org/pdf/1609.01241.pdf.
The circuit consits of three parts i) leftshift ii) subtraction 
iii) conditional add operation.

Ancilla: n, Size 16n^2 - 13, Toffoli: 5n^2 -5 , Depth: 10n^2 - 6.

"""


def quantum_division(eng, dividend, remainder, divisor):
    """
    Performs restoring integer division, i.e.,

    |dividend>|remainder>|divisor> -> |remainder>|quotient>|divisor>

    (only works if all three qubits are of equal length)
    """
    assert(len(dividend) == len(remainder) == len(divisor))
    j = len(remainder)
    n = len(dividend)

    while j != 0:
        combined_reg = []

        combined_reg.append(dividend[n - 1])

        for i in range(0, n - 1):
            combined_reg.append(remainder[i])

        SubtractQuantum() | (divisor[0:n], combined_reg)
        CNOT | (combined_reg[n - 1], remainder[n - 1])
        with Control(eng, remainder[n-1]):
            AddQuantum() | (divisor[0:n], combined_reg)
        X | remainder[n - 1]

        remainder.insert(0, dividend[n - 1])
        dividend.insert(0, remainder[n])
        del remainder[n]
        del dividend[n]

        j -= 1
    
def inverse_quantum_division(eng, remainder, quotient, divisor):
    """
    |remainder>|quotient>|divisor> ->  |dividend>|remainder(0)>|divisor>
    
    """

    assert(len(remainder) == len(quotient) == len(divisor))
    j = 0
    n = len(quotient)
    while j != n:
        X | quotient[0]
        with Control(eng,quotient[0]):
            SubtractQuantum() | (divisor, remainder)
        CNOT | (remainder[-1], quotient[0])
        
        AddQuantum() | (divisor,remainder)
       
        remainder.insert(n, quotient[0])
        quotient.insert(n,remainder[0])
        del remainder[0]
        del quotient[0]
        j += 1
    

"""
Quantum conditional add with no input carry from: 
https://arxiv.org/pdf/1706.05113.pdf

Ancilla: 2, Size: 7n - 4, Toffoli: 3n + 2, Depth: 5n.
"""


def quantum_conditional_add_carry(eng, quint_a, quint_b, ctrl, z):
    """
    Adds up two quantum integers if the control qubit is |1>, i.e.,

    |a>|b>|ctrl>|z(0)z(1)> -> |a>|s(0)...s(n-1)>|ctrl>|s(n)z(1)>
    (where s denotes the sum of a and b)

    If the control qubit is |0> no operation is performed:

    |a>|b>|ctrl>|z(0)z(1)> -> |a>|b>|ctrl>|z(0)z(1)>

    (only works if quint_a and quint_b are of the same size, ctrl is a
    single qubit and z is a quantum register with 2 qubits.
    """

    assert(len(quint_a) == len(quint_b))
    assert(len(ctrl) == 1)
    assert(len(z) == 2)

    n = len(quint_a)

    for i in range(1, n):
        CNOT | (quint_a[i], quint_b[i])

    with Control(eng, [quint_a[n - 1], ctrl[0]]):
        X | z[0]

    for j in range(n - 2, 0, -1):
        CNOT | (quint_a[j], quint_a[j + 1])

    for k in range(0, n - 1):
        with Control(eng, [quint_b[k], quint_a[k]]):
            X | quint_a[k + 1]

    with Control(eng, [quint_b[n - 1], quint_a[n - 1]]):
        X | z[1]

    with Control(eng, [ctrl[0], z[1]]):
        X | z[0]

    with Control(eng, [quint_b[n - 1], quint_a[n - 1]]):
        X | z[1]

    for l in range(n - 1, 0, -1):
        with Control(eng, [ctrl[0], quint_a[l]]):
            X | quint_b[l]
        with Control(eng, [quint_a[l - 1], quint_b[l - 1]]):
            X | quint_a[l]

    with Control(eng, [quint_a[0], ctrl[0]]):
        X | quint_b[0]

    for m in range(1, n - 1):
        CNOT | (quint_a[m], quint_a[m + 1])

    for n in range(1, n):
        CNOT | (quint_a[n], quint_b[n])


"""
Quantum multiplication from: https://arxiv.org/abs/1706.05113.

Ancilla: 2n + 1, Size: 7n^2 - 9n + 4, Toffoli: 5n^2 - 4n, Depth: 3n^2 - 2.
"""


def quantum_multiplication(eng, quint_a, quint_b, product):
    """
    Multiplies two quintum integers, i.e,

    |a>|b>|0> -> |a>|b>|a*b>

    (only works if quint_a and quint_b are of the same size, n qubits and
    product has size 2n+1).
    """
    assert(len(quint_a) == len(quint_b))
    n = len(quint_a)
    assert(len(product) == ((2 * n) + 1))

    for i in range(0, n):
        with Control(eng, [quint_a[i], quint_b[0]]):
            X | product[i]

    with Control(eng, quint_b[1]):
        AddQuantum() | (quint_a[0:(n - 1)], 
                                    product[1:n], 
                                    [product[n + 1], product[n + 2]])

    for j in range(2, n):
        with Control(eng, quint_b[j]):  
            AddQuantum() | (quint_a[0:(n - 1)], product[(0 + j):(n - 1 + j)], 
                                        [product[n + j], product[n + j + 1]])
