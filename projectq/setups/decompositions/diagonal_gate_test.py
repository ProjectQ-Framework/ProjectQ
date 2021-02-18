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

from projectq import MainEngine
from projectq.ops import X, DiagonalGate
from . import diagonal_gate as diag
from ._isometries_fixture import iso_decomp_chooser

import numpy as np
import cmath
import pytest


def create_initial_state(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 1:
            X | qureg[pos]


@pytest.mark.parametrize("init", range(16))
def test_decompose_diagonal_gate(init, iso_decomp_chooser):
    angles = list(range(1, 9))
    eng = MainEngine(verbose=True)
    qureg = eng.allocate_qureg(4)
    eng.flush()
    create_initial_state(init, qureg)

    D = DiagonalGate(angles=angles)
    cmd = D.generate_command(qureg[1:])
    diag._decompose_diagonal_gate(cmd)

    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T

    print(vec.item(init) - cmath.exp(1j*(((init >> 1) & 7)+1)))
    assert np.isclose(vec.item(init), cmath.exp(1j*(((init >> 1) & 7)+1)))
