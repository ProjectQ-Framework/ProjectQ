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

import numpy as np
from math import ceil

from projectq.ops import Rz, X, CNOT, Ph
from projectq.meta import Dagger, Control, Compute, Uncompute
from . import _decompose_diagonal_gate


def _count_trailing_zero_bits(v):
    assert v > 0
    v = (v ^ (v - 1)) >> 1
    c = 0
    while(v):
        v >>= 1
        c += 1
    return c


def _apply_diagonal_gate(decomposition, qureg):
    n = len(qureg)
    assert n == len(decomposition) - 1

    for i in range(n):
        _apply_uniformly_controlled_rotation(decomposition[i], qureg[i:])

    p = decomposition[-1][0]
    Ph(p) | qureg[0]


def _apply_uniformly_controlled_rotation(angles, qureg):
    N = len(angles)
    n = len(qureg) - 1
    assert 1 << n == N
    assert N > 0

    target = qureg[0]
    controls = qureg[1:]

    if N == 1:
        Rz(angles[0]) | target
        return

    for i in range(N-1):
        Rz(angles[i]) | target
        control = controls[_count_trailing_zero_bits(i+1)]
        CNOT | (control, target)
    Rz(angles[N-1]) | target
    CNOT | (controls[-1], target)


def _apply_uniformly_controlled_gate(decomposition, target, choice_reg,
                                     up_to_diagonal):
    gates, phases = decomposition

    assert len(gates) == 1 << len(choice_reg)
    assert len(phases) == 2 << len(choice_reg)

    for i in range(len(gates) - 1):
        gates[i] | target
        control_index = _count_trailing_zero_bits(i+1)
        choice = choice_reg[control_index]
        CNOT | (choice, target)
    gates[-1] | target

    if up_to_diagonal:
        return

    decomposed_diagonal = _decompose_diagonal_gate(phases)
    _apply_diagonal_gate(decomposed_diagonal, [target]+choice_reg)


def _get_one_bits(qureg, bks):
    res = []
    for i in range(len(qureg)):
        if bks & (1 << i):
            res.append(qureg[i])
    return res


def _apply_multi_controlled_gate(decomposition, k, s, threshold, qureg):
    gates, phases = decomposition
    mask = k & ~(1 << s)
    ctrl = _get_one_bits(qureg, mask)
    eng = qureg[0].engine

    if len(gates) == 1:
        if np.allclose(gates[0].matrix, Rz(0).matrix):
            return

    if len(ctrl) == 0:
        gates[0] | qureg[s]
    elif len(ctrl) < threshold:
        _apply_uniformly_controlled_gate(decomposition, qureg[s], ctrl, True)
    else:
        with Control(eng, ctrl):
            gates[0] | qureg[s]


def _apply_isometry(decomposition, threshold, qureg):
    reductions, decomposed_diagonal = decomposition

    n = len(qureg)
    eng = qureg[0].engine

    with Dagger(eng):
        ncols = range(len(reductions))
        for k in ncols:
            for s in range(n):
                mcg, ucg = reductions[k][s]
                _apply_multi_controlled_gate(mcg, k, s, threshold, qureg)
                if len(ucg) > 0:
                    _apply_uniformly_controlled_gate(ucg, qureg[s],
                                                     qureg[s+1:], True)
        nqubits = int(ceil(np.log2(len(ncols))))
        if nqubits == 0:
            p = decomposed_diagonal[-1][0]
            Ph(p) | qureg[0]
        else:
            _apply_diagonal_gate(decomposed_diagonal, qureg[:nqubits])
