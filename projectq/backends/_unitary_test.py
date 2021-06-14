# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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
Contains the tests for the UnitarySimulator
"""

import itertools
import numpy as np
import pytest
from scipy.stats import unitary_group

from projectq.cengines import MainEngine, DummyEngine
from projectq.ops import (
    BasicGate,
    MatrixGate,
    All,
    Measure,
    Allocate,
    Deallocate,
    Command,
    X,
    Rx,
    Rxx,
)
from projectq.meta import Control
from projectq.types import WeakQubitRef

from ._unitary import UnitarySimulator


def test_unitary_is_available():
    sim = UnitarySimulator()
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=2)
    qb4 = WeakQubitRef(engine=None, idx=2)
    qb5 = WeakQubitRef(engine=None, idx=2)
    qb6 = WeakQubitRef(engine=None, idx=2)

    assert sim.is_available(Command(None, Allocate, qubits=([qb0],)))
    assert sim.is_available(Command(None, Deallocate, qubits=([qb0],)))
    assert sim.is_available(Command(None, Measure, qubits=([qb0],)))
    assert sim.is_available(Command(None, X, qubits=([qb0],)))
    assert sim.is_available(Command(None, Rx(1.2), qubits=([qb0],)))
    assert sim.is_available(Command(None, Rxx(1.2), qubits=([qb0, qb1],)))

    assert not sim.is_available(Command(None, BasicGate(), qubits=([qb0],)))

    with pytest.warns(UserWarning):
        assert sim.is_available(
            Command(
                None,
                MatrixGate(np.identity(2 ** 7)),
                qubits=([qb0, qb1, qb2, qb3, qb4, qb5, qb6],),
            )
        )


def test_unitary_not_last_engine():
    eng = MainEngine(backend=DummyEngine(save_commands=True), engine_list=[UnitarySimulator()])
    qubit = eng.allocate_qubit()
    X | qubit
    Measure | qubit
    assert len(eng.backend.received_commands) == 3


def test_unitary_error_after_deallocation_or_measurement():
    eng = MainEngine(backend=UnitarySimulator(), engine_list=[])
    qubit = eng.allocate_qubit()
    X | qubit
    Measure | qubit
    eng.flush()

    with pytest.raises(RuntimeError):
        X | qubit

    # Still ok
    Measure | qubit
    eng.flush()

    eng = MainEngine(backend=UnitarySimulator(), engine_list=[])
    qureg = eng.allocate_qureg(2)
    All(X) | qureg
    eng.deallocate_qubit(qureg[0])

    with pytest.raises(RuntimeError):
        X | qureg[1]

    # Still ok
    Measure | qubit
    eng.flush()


def test_unitary_simulator():
    def create_random_unitary(n):
        return unitary_group.rvs(2 ** n)

    mat1 = create_random_unitary(1)
    mat2 = create_random_unitary(2)
    mat3 = create_random_unitary(3)
    mat4 = create_random_unitary(1)

    n_qubits = 3

    def apply_gates(eng, qureg):
        MatrixGate(mat1) | qureg[0]
        MatrixGate(mat2) | qureg[1:]
        MatrixGate(mat3) | qureg

        with Control(eng, qureg[1]):
            MatrixGate(mat2) | (qureg[0], qureg[2])
            MatrixGate(mat4) | qureg[0]

        # TODO: uncomment once the general control state branch has been merged
        # with Control(eng, qureg[1], ctrl_state='0'):
        #     MatrixGate(mat1) | qureg[0]
        #     with Control(test_eng,qureg[2],ctrl_state='0'):
        #         MatrixGate(mat1) | qureg[0]

    for basis_state in [list(x[::-1]) for x in itertools.product([0, 1], repeat=2 ** n_qubits)][1:]:
        ref_eng = MainEngine(engine_list=[], verbose=True)
        ref_qureg = ref_eng.allocate_qureg(n_qubits)
        ref_eng.backend.set_wavefunction(basis_state, ref_qureg)
        apply_gates(ref_eng, ref_qureg)

        test_eng = MainEngine(backend=UnitarySimulator(), engine_list=[], verbose=True)
        test_qureg = test_eng.allocate_qureg(n_qubits)

        assert np.allclose(test_eng.backend.unitary, np.identity(2 ** n_qubits))

        apply_gates(test_eng, test_qureg)

        qubit_map, ref_state = ref_eng.backend.cheat()
        assert qubit_map == {i: i for i in range(n_qubits)}

        test_state = test_eng.backend.unitary @ np.array(basis_state)

        assert np.allclose(ref_eng.backend.cheat()[1], test_state)

        All(Measure) | ref_qureg
        All(Measure) | test_qureg
