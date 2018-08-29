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
from ._gates import AddQuantum, SubtractQuantum, Comparator

"""
Quantum addition using ripple carry from: https://arxiv.org/pdf/0910.2530.pdf.

Ancilla: 0, Size: 7n-6, Toffoli: 2n-1, Depth: 5n-3
"""

def add_quantum(eng, quint_a, quint_b, carry):
    """
    Adds two quantum integers, i.e.,

    |a0...a(n-1)>|b(0)...b(n-1)>|c> -> |a0...a(n-1)>|b(0)...b(n)>

    (only works if quint_a and quint_b are the same size and carry is a single qubit)
    """

    assert(len(quint_a) == len(quint_b))
    assert(len(carry) == 1)

    n = len(quint_a) + 1 
    
    for i in range(1,n-1):   
        CNOT | (quint_a[i], quint_b[i])

    CNOT | (quint_a[n-2], carry)

    for j in range(n-3,0,-1):
        CNOT | (quint_a[j], quint_a[j+1])

    for k in range(0,n-2):
        with Control(eng, [quint_a[k],quint_b[k]]):
            X | (quint_a[k+1])
    
    with Control(eng,[quint_a[n-2], quint_b[n-2]]):
            X | carry

    for l in range(n-2,0,-1):
        CNOT | (quint_a[l], quint_b[l])
        with Control(eng,[quint_a[l-1], quint_b[l-1]]):
            X | quint_a[l]

    for m in range(1,n-2):
        CNOT | (quint_a[m],quint_a[m+1])

    for n in range(0,n-1):
        CNOT | (quint_a[n],quint_b[n])
    
"""
Quantum subtraction using bitwise complementation of quantum adder:
b-a = (a + b')'. Largely the same as the quantum addition circuit 
except that the steps involving the carry qubit are left out and 
complement b at the start and at the end of the circuit is added.

Ancilla: 0, Size: 9n-8, Toffoli: 2n-2, Depth: 5n-5
"""

def subtract_quantum(eng, quint_a, quint_b):
    """
    Subtracts two quantum integers, i.e.,
    
    |a>|b>|c> -> |a>|b-a>
    
    (only works if quint_a and quint_b are the same size)
    """
    assert(len(quint_a) == len(quint_b))
    
    n = len(quint_a) + 1

    All(X) | quint_b

    for i in range(1,n-1):
        CNOT | (quint_a[i], quint_b[i])
    
    for j in range(n-3,0,-1):
        CNOT | (quint_a[j], quint_a[j+1])

    for k in range(0,n-2):
        with Control(eng, [quint_a[k],quint_b[k]]):
            X | (quint_a[k+1])

    for l in range(n-2,0,-1):
        CNOT | (quint_a[l], quint_b[l])
        with Control(eng,[quint_a[l-1], quint_b[l-1]]):
            X | quint_a[l]

    for m in range(1,n-2):
        CNOT | (quint_a[m],quint_a[m+1])

    for n in range(0,n-1):
        CNOT | (quint_a[n],quint_b[n])

    All(X) | quint_b

"""
Comparator flipping a compare qubit by computing the high bit of b-a, 
which is 1 if and only if a > b. The high bit is computed using the first half of 
circuit in AddQuantum (such that the high bit is written to  the carry qubit) and 
then undoing the first half of the circuit. By complementing b at the start and 
b+a at the end the high bit of b-a is calculated.

"""
def comparator(eng, quint_a, quint_b, comparator):

    """                                                     
    Compares the size of two quantum integers, i.e,
    if a>b: |a>|b>|c> -> |a>|b>|c⊕1>
    else:   |a>|b>|c> -> |a>|b>|c>
    (only works if quint_a and quint_b are the same size and the comparator is 1 
    qubit)

    Ancilla: 0,Size: 8n-3,Toffoli: 2n+1, Depth: 4n+3
    """

    assert(len(quint_a) == len(quint_b))
    assert(len(comparator) == 1)
    
    n = len(quint_a) + 1

    All(X) | quint_b
    
    for i in range(1,n-1):
        CNOT | (quint_a[i], quint_b[i])

    CNOT | (quint_a[n-2], comparator)

    for j in range(n-3,0,-1):
        CNOT | (quint_a[j], quint_a[j+1])

    for k in range(0,n-2):
        with Control(eng, [quint_a[k],quint_b[k]]):
            X | (quint_a[k+1])

    with Control(eng,[quint_a[n-2], quint_b[n-2]]):
        X | comparator

    for k in range(0,n-2):
        with Control(eng, [quint_a[k],quint_b[k]]):
            X | (quint_a[k+1])

    for j in range(n-3,0,-1):
        CNOT | (quint_a[j], quint_a[j+1])

    for i in range(1,n-1):
        CNOT | (quint_a[i], quint_b[i])

    All(X) | quint_b
