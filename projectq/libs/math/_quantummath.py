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
from ._gates import AddQuantum

def add_quantum(eng, quint_a, quint_b, carry):
    
    assert(len(quint_a) == len(quint_b))
    assert(len(carry) == 1)

    n = len(quint_a) + 1 
    
    for i in range(1,n-1):
        CNOT | (quint_a[i], quint_b[i])

    for j in range(n-1,1):
        CNOT | (quint_a[j], quint_a[j+1])

    for k in range(0,n-2):
        with Control(eng, [quint_a[k],quint_b[k]]):
            X | (quint_a[k+1])
    
    with Control(eng,[quint_a[n-2], quint_b[n-2]]):
            X | carry

    for l in range(n-1,1):
        CNOT | (quint_a[l], quint_b[l])
        with Control(eng,[quint_a[l-1], quint_b[l-1]]):
            X | quint_a[l]

    for m in range(1,n-2):
        CNOT | (quint_a[m],quint_a[m+1])

    for n in range(0,n-1):
        CNOT | (quint_a[n],quint_b[n])

