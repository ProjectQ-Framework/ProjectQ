# Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ._basics import BasicGate, NotInvertible, NotMergeable

import copy
import numpy as np


class Isometry(BasicGate):
    """
    A gate that represents an arbitrary isometry. It is constructed from a
    matrix of size 2^n by k. The isometry acts on n qubits, the action on
    states |i> with i >= k is undefined. The value of k must be in [1,2^n].

    Example:
        .. code-block:: python
            matrix([[1./sqrt(2), 0],
                    [0, 1./sqrt(2)]
                    [1./sqrt(2), 0]
                    [0, 1./sqrt(2)]]
            V = Isometry([col_0, col_1])
            V | qureg

    Attributes:
        matrix: 2^n by k matrix with orthonormal columns

    Note:
        If possible use DiagonalGate of UniformlyControlledGate instead. In
        general the gate complexity is exponential in the number of qubits,
        so it is very inefficient to decompose large isometries.
    """
    def __init__(self, matrix):
        array = np.asarray(matrix)
        cols = []
        for i in range(array.shape[1]):
            cols.append(matrix[:, i])

        k = len(cols)
        if k == 0:
            raise ValueError("An isometry needs at least one column.")
        n = int(np.log2(len(cols[0])))
        if 2**n != len(cols[0]):
            raise ValueError("The length of the columns of an isometry must be"
                             " a power of 2.")
        if k > 2**n:
            raise ValueError("An isometry can contain at most 2^n columns.")
        for i in range(k):
            if len(cols[i]) != 2**n:
                raise ValueError("All columns of an isometry must have the"
                                 " same length.")

        for i in range(k):
            if not np.isclose(np.linalg.norm(cols[i]), 1):
                raise ValueError("The columns of an isometry have to be"
                                 " normalized.")
            for j in range(k):
                if i != j:
                    if not np.isclose(np.vdot(cols[i], cols[j]), 0):
                        raise ValueError("The columns of an isometry have to"
                                         " be orthogonal.")

        self.cols = cols
        self.interchangeable_qubit_indices = []
        self._decomposition = None
        self._threshold = _get_ucg_mcg_threshold(n)

    @property
    def decomposition(self):
        if self._decomposition is None:
            from projectq.libs.isometries import _decompose_isometry
            self._decomposition = _decompose_isometry(self.cols,
                                                      self._threshold)
        return self._decomposition

    def __str__(self):
        return "V"

    def __eq__(self, other):
        """ Not implemented as this object is a floating point type."""
        return NotImplemented

    def __ne__(self, other):
        """ Not implemented as this object is a floating point type."""
        return NotImplemented


# When decomposing up to diagonal gate, for a small number of controls
# a UCG is cheaper than a MCG. Here we empirically find that threshold
def _my_is_available(cmd):
    from projectq.ops import (Command, X, Y, Z, T, H, Tdag, S, Sdag, Measure,
                              Allocate, Deallocate, NOT, Rx, Ry, Rz, Barrier,
                              Entangle)
    from projectq.meta import Control, Compute, Uncompute, get_control_count

    g = cmd.gate
    if g == NOT and get_control_count(cmd) <= 1:
        return True
    if get_control_count(cmd) == 0:
        if g in (T, Tdag, S, Sdag, H, Y, Z):
            return True
        if isinstance(g, (Rx, Ry, Rz)):
            return True
    if g in (Measure, Allocate, Deallocate, Barrier):
        return True
    return False


def _count_cnot_in_mcg(n):
    from projectq import MainEngine
    from projectq.ops import C, Z, H
    from projectq.backends import ResourceCounter
    from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                                   DummyEngine, BasicEngine)
    import projectq.setups.decompositions

    resource_counter = ResourceCounter()
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    engines = [AutoReplacer(rule_set), resource_counter]
    backend = DummyEngine()
    backend.is_available = _my_is_available
    eng = MainEngine(backend, engines)
    qureg = eng.allocate_qureg(n+1)
    C(H, n) | (qureg[1:], qureg[0])
    for item in str(resource_counter).split("\n"):
        if "CX : " in item:
            return int(item.strip()[5:])
    return 0


def _get_ucg_mcg_threshold(n):
    for ctrl in range(2, n):
        if (1 << ctrl)-1 > _count_cnot_in_mcg(ctrl):
            return ctrl
    return n
