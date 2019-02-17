from projectq import MainEngine
from projectq.ops import Measure, X, DiagonalGate, Rz, CNOT
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute, Dagger

from . import diagonal_gate as diag

import numpy as np
import math
import cmath
import copy
import random
import pytest


def create_initial_state(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 1:
            X | qureg[pos]


@pytest.mark.parametrize("init", range(16))
def test_decompose_diagonal_gate(init):
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
