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
try:
    from math import gcd
except ImportError:
    from fractions import gcd

from projectq.ops import R, X, Swap, Measure, CNOT, QFT
from projectq.meta import Control, Compute, Uncompute, CustomUncompute, Dagger
from ._gates import AddConstant, SubConstant, AddConstantModN, SubConstantModN


# Draper's addition by constant https://arxiv.org/abs/quant-ph/0008033
def add_constant(eng, c, quint):
    """
    Adds a classical constant c to the quantum integer (qureg) quint using
    Draper addition.

    Note: Uses the Fourier-transform adder from
          https://arxiv.org/abs/quant-ph/0008033.
    """

    with Compute(eng):
        QFT | quint

    for i in range(len(quint)):
        for j in range(i, -1, -1):
            if ((c >> j) & 1):
                R(math.pi / (1 << (i - j))) | quint[i]

    Uncompute(eng)


# Modular adder by Beauregard https://arxiv.org/abs/quant-ph/0205095
def add_constant_modN(eng, c, N, quint):
    """
    Adds a classical constant c to a quantum integer (qureg) quint modulo N
    using Draper addition and the construction from
    https://arxiv.org/abs/quant-ph/0205095.
    """
    assert(c < N and c >= 0)

    AddConstant(c) | quint

    with Compute(eng):
        SubConstant(N) | quint
        ancilla = eng.allocate_qubit()
        CNOT | (quint[-1], ancilla)
        with Control(eng, ancilla):
            AddConstant(N) | quint

    SubConstant(c) | quint

    with CustomUncompute(eng):
        X | quint[-1]
        CNOT | (quint[-1], ancilla)
        X | quint[-1]
        del ancilla

    AddConstant(c) | quint


# Modular multiplication by modular addition & shift, followed by uncompute
# from https://arxiv.org/abs/quant-ph/0205095
def mul_by_constant_modN(eng, c, N, quint_in):
    """
    Multiplies a quantum integer by a classical number a modulo N, i.e.,

    |x> -> |a*x mod N>

    (only works if a and N are relative primes, otherwise the modular inverse
    does not exist).
    """
    assert(c < N and c >= 0)
    assert(gcd(c, N) == 1)

    n = len(quint_in)
    quint_out = eng.allocate_qureg(n + 1)

    for i in range(n):
        with Control(eng, quint_in[i]):
            AddConstantModN((c << i) % N, N) | quint_out

    for i in range(n):
        Swap | (quint_out[i], quint_in[i])

    cinv = inv_mod_N(c, N)

    for i in range(n):
        with Control(eng, quint_in[i]):
            SubConstantModN((cinv << i) % N, N) | quint_out
    del quint_out


# calculates the inverse of a modulo N
def inv_mod_N(a, N):
    s = 0
    old_s = 1
    r = N
    old_r = a
    while r != 0:
        q = int(old_r / r)
        tmp = r
        r = old_r - q * r
        old_r = tmp
        tmp = s
        s = old_s - q * s
        old_s = tmp
    return (old_s + N) % N
