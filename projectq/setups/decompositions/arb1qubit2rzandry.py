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
Registers the Z-Y decomposition for an arbitrary one qubit gate.

See paper "Elementary gates for quantum computing" by Adriano Barenco et al.,
arXiv:quant-ph/9503016v1. (Note: They use different gate definitions!)
Or see theorem 4.1 in Nielsen and Chuang.

Decompose an arbitrary one qubit gate U into
U = e^(i alpha) Rz(beta) Ry(gamma) Rz(delta). If a gate V is element of SU(2),
i.e., determinant == 1, then
V = Rz(beta) Ry(gamma) Rz(delta)

"""

import cmath
import math

import numpy

from projectq.cengines import DecompositionRule
from projectq.meta import Control
from projectq.ops import BasicGate, Ph, Rz, Ry


def _recognize_arb1qubit(cmd):
    """ Recognize an arbitrary one qubit gate which has a matrix property."""
    try:
        m = cmd.gate.matrix
        if len(m) == 2:
            return True
        else:
            return False
    except:
        return False


def _decompose_arb1qubit(cmd):
    """
    Use Z-Y decomposition of Nielsen and Chuang (theorem 4.1).

    An arbitrary one qubit gate matrix can be writen as
    U = [[exp(j*(a-b/2-d/2))*cos(c/2), -exp(j*(a-b/2+d/2))*sin(c/2)],
         [exp(j*(a+b/2-d/2))*sin(c/2), exp(j*(a+b/2+d/2))*cos(c/2)]]
    where a,b,c,d are real numbers.
    Then U = exp(j*a) Rz(b) Ry(c) Rz(d).
    If the matrix is element of SU(2) (determinant == 1), then
    a = 0.
    """
    matrix = cmd.gate.matrix.tolist()
    cos_c_div_2 = abs(matrix[0][0])
    c = 2 * math.acos(cos_c_div_2)
    b = cmath.phase(matrix[1][0]) - cmath.phase(matrix[0][0])
    d = cmath.phase(matrix[1][1]) - cmath.phase(matrix[1][0])
    if numpy.linalg.det(numpy.matrix(matrix)).real > 1. - 1e-12:
        # This branch is technically not necessary but it avoids
        # having `a` close to 0 and then removing it later...
        a = 0
    else:
        a = cmath.phase(matrix[0][0]) + b/2. + d/2.
    qb = cmd.qubits
    eng = cmd.engine
    with Control(eng, cmd.control_qubits):
        Rz(d) | qb
        Ry(c) | qb
        Rz(b) | qb
        if a != 0:
            Ph(a) | qb


all_defined_decomposition_rules = [
    DecompositionRule(BasicGate, _decompose_arb1qubit, _recognize_arb1qubit)
]
