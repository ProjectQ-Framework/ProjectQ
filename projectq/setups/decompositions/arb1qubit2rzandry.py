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
import itertools
import math


import numpy

from projectq.cengines import DecompositionRule
from projectq.meta import Control
from projectq.ops import BasicGate, Ph, Ry, Rz


TOLERANCE = 1e-12


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


def _test_parameters(matrix, a, b_half, c_half, d_half):
    """
    It builds matrix U with parameters (a, b/2, c/2, d/2) and compares against
    matrix.

    U = [[exp(j*(a-b/2-d/2))*cos(c/2), -exp(j*(a-b/2+d/2))*sin(c/2)],
         [exp(j*(a+b/2-d/2))*sin(c/2), exp(j*(a+b/2+d/2))*cos(c/2)]]

    Args:
        matrix(list): 2x2 matrix
        a: parameter of U
        b_half: b/2. parameter of U
        c_half: c/2. parameter of U
        d_half: d/2. parameter of U

    Returns:
        True if matrix elements of U and `matrix` are TOLERANCE close.
    """
    U = [[cmath.exp(1j*(a-b_half-d_half))*math.cos(c_half),
          -cmath.exp(1j*(a-b_half+d_half))*math.sin(c_half)],
         [cmath.exp(1j*(a+b_half-d_half))*math.sin(c_half),
          cmath.exp(1j*(a+b_half+d_half))*math.cos(c_half)]]
    return numpy.allclose(U, matrix, rtol=10*TOLERANCE, atol=TOLERANCE)


def _find_parameters(matrix):
    """
    Given a 2x2 unitary matrix, find the parameters
    a, b/2, c/2, and d/2 such that
    matrix == [[exp(j*(a-b/2-d/2))*cos(c/2), -exp(j*(a-b/2+d/2))*sin(c/2)],
               [exp(j*(a+b/2-d/2))*sin(c/2), exp(j*(a+b/2+d/2))*cos(c/2)]]

    Note:
    If the matrix is element of SU(2) (determinant == 1), then
    we can choose a = 0.

    Args:
        matrix(list): 2x2 unitary matrix

    Returns:
        parameters of the matrix: (a, b/2, c/2, d/2)
    """
    # Determine a, b/2, c/2 and d/2 (3 different cases).
    # Note: everything is modulo 2pi.
    # Case 1: sin(c/2) == 0:
    if abs(matrix[0][1]) < TOLERANCE:
        two_a = cmath.phase(matrix[0][0]*matrix[1][1]) % (2*math.pi)
        if abs(two_a) < TOLERANCE or abs(two_a) > 2*math.pi-TOLERANCE:
            # from 2a==0 (mod 2pi), it follows that a==0 or a==pi,
            # w.l.g. we can choose a==0 because (see U above)
            # c/2 -> c/2 + pi would have the same effect as as a==0 -> a==pi.
            a = 0
        else:
            a = two_a/2.
        d_half = 0  # w.l.g
        b = cmath.phase(matrix[1][1])-cmath.phase(matrix[0][0])
        possible_b_half = [(b/2.) % (2*math.pi), (b/2.+math.pi) % (2*math.pi)]
        # As we have fixed a, we need to find correct sign for cos(c/2)
        possible_c_half = [0.0, math.pi]
        found = False
        for b_half, c_half in itertools.product(possible_b_half,
                                                possible_c_half):
            if _test_parameters(matrix, a, b_half, c_half, d_half):
                found = True
                break
        if not found:
            raise Exception("Couldn't find parameters for matrix ", matrix,
                            "This shouldn't happen. Maybe the matrix is " +
                            "not unitary?")
    # Case 2: cos(c/2) == 0:
    elif abs(matrix[0][0]) < TOLERANCE:
        two_a = cmath.phase(-matrix[0][1]*matrix[1][0]) % (2*math.pi)
        if abs(two_a) < TOLERANCE or abs(two_a) > 2*math.pi-TOLERANCE:
            # from 2a==0 (mod 2pi), it follows that a==0 or a==pi,
            # w.l.g. we can choose a==0 because (see U above)
            # c/2 -> c/2 + pi would have the same effect as as a==0 -> a==pi.
            a = 0
        else:
            a = two_a/2.
        d_half = 0  # w.l.g
        b = cmath.phase(matrix[1][0])-cmath.phase(matrix[0][1]) + math.pi
        possible_b_half = [(b/2.) % (2*math.pi), (b/2.+math.pi) % (2*math.pi)]
        # As we have fixed a, we need to find correct sign for sin(c/2)
        possible_c_half = [math.pi/2., 3./2.*math.pi]
        found = False
        for b_half, c_half in itertools.product(possible_b_half,
                                                possible_c_half):
            if _test_parameters(matrix, a, b_half, c_half, d_half):
                found = True
                break
        if not found:
            raise Exception("Couldn't find parameters for matrix ", matrix,
                            "This shouldn't happen. Maybe the matrix is " +
                            "not unitary?")
    # Case 3: sin(c/2) != 0 and cos(c/2) !=0:
    else:
        two_a = cmath.phase(matrix[0][0]*matrix[1][1]) % (2*math.pi)
        if abs(two_a) < TOLERANCE or abs(two_a) > 2*math.pi-TOLERANCE:
            # from 2a==0 (mod 2pi), it follows that a==0 or a==pi,
            # w.l.g. we can choose a==0 because (see U above)
            # c/2 -> c/2 + pi would have the same effect as as a==0 -> a==pi.
            a = 0
        else:
            a = two_a/2.
        two_d = 2.*cmath.phase(matrix[0][1])-2.*cmath.phase(matrix[0][0])
        possible_d_half = [two_d/4. % (2*math.pi),
                           (two_d/4.+math.pi/2.) % (2*math.pi),
                           (two_d/4.+math.pi) % (2*math.pi),
                           (two_d/4.+3./2.*math.pi) % (2*math.pi)]
        two_b = 2.*cmath.phase(matrix[1][0])-2.*cmath.phase(matrix[0][0])
        possible_b_half = [two_b/4. % (2*math.pi),
                           (two_b/4.+math.pi/2.) % (2*math.pi),
                           (two_b/4.+math.pi) % (2*math.pi),
                           (two_b/4.+3./2.*math.pi) % (2*math.pi)]
        tmp = math.acos(abs(matrix[1][1]))
        possible_c_half = [tmp % (2*math.pi),
                           (tmp+math.pi) % (2*math.pi),
                           (-1.*tmp) % (2*math.pi),
                           (-1.*tmp+math.pi) % (2*math.pi)]
        found = False
        for b_half, c_half, d_half in itertools.product(possible_b_half,
                                                        possible_c_half,
                                                        possible_d_half):
            if _test_parameters(matrix, a, b_half, c_half, d_half):
                found = True
                break
        if not found:
            raise Exception("Couldn't find parameters for matrix ", matrix,
                            "This shouldn't happen. Maybe the matrix is " +
                            "not unitary?")
    return (a, b_half, c_half, d_half)


def _decompose_arb1qubit(cmd):
    """
    Use Z-Y decomposition of Nielsen and Chuang (Theorem 4.1).

    An arbitrary one qubit gate matrix can be writen as
    U = [[exp(j*(a-b/2-d/2))*cos(c/2), -exp(j*(a-b/2+d/2))*sin(c/2)],
         [exp(j*(a+b/2-d/2))*sin(c/2), exp(j*(a+b/2+d/2))*cos(c/2)]]
    where a,b,c,d are real numbers.
    Then U = exp(j*a) Rz(b) Ry(c) Rz(d).
    If the matrix is element of SU(2) (determinant == 1), then
    we can choose a = 0.
    """
    matrix = cmd.gate.matrix.tolist()
    a, b_half, c_half, d_half = _find_parameters(matrix)
    qb = cmd.qubits
    eng = cmd.engine
    with Control(eng, cmd.control_qubits):
        if Rz(2*d_half) != Rz(0):
            Rz(2*d_half) | qb
        if Ry(2*c_half) != Ry(0):
            Ry(2*c_half) | qb
        if Rz(2*b_half) != Rz(0):
            Rz(2*b_half) | qb
        if a != 0:
            Ph(a) | qb


all_defined_decomposition_rules = [
    DecompositionRule(BasicGate, _decompose_arb1qubit, _recognize_arb1qubit)
]
