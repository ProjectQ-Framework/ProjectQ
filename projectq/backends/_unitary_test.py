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

from projectq.cengines import DummyEngine, MainEngine, NotYetMeasuredError
from projectq.meta import Control, LogicalQubitIDTag
from projectq.ops import (
    CNOT,
    All,
    Allocate,
    BasicGate,
    Command,
    Deallocate,
    H,
    MatrixGate,
    Measure,
    Rx,
    Rxx,
    X,
    Y,
)
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
    assert sim.is_available(Command(None, X, qubits=([qb0],), controls=[qb1]))
    assert sim.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='1'))

    assert not sim.is_available(Command(None, BasicGate(), qubits=([qb0],)))
    assert not sim.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='0'))

    with pytest.warns(UserWarning):
        assert sim.is_available(
            Command(
                None,
                MatrixGate(np.identity(2 ** 7)),
                qubits=([qb0, qb1, qb2, qb3, qb4, qb5, qb6],),
            )
        )


def test_unitary_warnings():
    eng = MainEngine(backend=DummyEngine(save_commands=True), engine_list=[UnitarySimulator()])
    qubit = eng.allocate_qubit()
    X | qubit

    with pytest.raises(RuntimeError):
        Measure | qubit


def test_unitary_not_last_engine():
    eng = MainEngine(backend=DummyEngine(save_commands=True), engine_list=[UnitarySimulator()])
    qubit = eng.allocate_qubit()
    X | qubit
    eng.flush()
    Measure | qubit
    assert len(eng.backend.received_commands) == 4


def test_unitary_flush_does_not_invalidate():
    eng = MainEngine(backend=UnitarySimulator(), engine_list=[])
    qureg = eng.allocate_qureg(2)

    X | qureg[0]
    eng.flush()

    Y | qureg[1]
    eng.flush()

    # Make sure that calling flush() multiple time is ok (before measurements)
    eng.flush()
    eng.flush()

    # Nothing should be added to the history here since no measurements or qubit deallocation happened
    assert not eng.backend.history
    assert np.allclose(eng.backend.unitary, np.kron(Y.matrix, X.matrix))

    All(Measure) | qureg

    # Make sure that calling flush() multiple time is ok (after measurement)
    eng.flush()
    eng.flush()

    # Nothing should be added to the history here since no gate since measurements or qubit deallocation happened
    assert not eng.backend.history
    assert np.allclose(eng.backend.unitary, np.kron(Y.matrix, X.matrix))


def test_unitary_after_deallocation_or_measurement():
    eng = MainEngine(backend=UnitarySimulator(), engine_list=[])
    qubit = eng.allocate_qubit()
    X | qubit

    assert not eng.backend.history

    eng.flush()
    Measure | qubit

    # FlushGate and MeasureGate do not append to the history
    assert not eng.backend.history
    assert np.allclose(eng.backend.unitary, X.matrix)

    with pytest.warns(UserWarning):
        Y | qubit

    # YGate after FlushGate and MeasureGate does not append current unitary (identity) to the history
    assert len(eng.backend.history) == 1
    assert np.allclose(eng.backend.unitary, Y.matrix)  # Reset of unitary when applying Y above
    assert np.allclose(eng.backend.history[0], X.matrix)

    # Still ok
    eng.flush()
    Measure | qubit

    # FlushGate and MeasureGate do not append to the history
    assert len(eng.backend.history) == 1
    assert np.allclose(eng.backend.unitary, Y.matrix)
    assert np.allclose(eng.backend.history[0], X.matrix)

    # Make sure that the new gate will trigger appending to the history and modify the current unitary
    with pytest.warns(UserWarning):
        Rx(1) | qubit
    assert len(eng.backend.history) == 2
    assert np.allclose(eng.backend.unitary, Rx(1).matrix)
    assert np.allclose(eng.backend.history[0], X.matrix)
    assert np.allclose(eng.backend.history[1], Y.matrix)

    # --------------------------------------------------------------------------

    eng = MainEngine(backend=UnitarySimulator(), engine_list=[])
    qureg = eng.allocate_qureg(2)
    All(X) | qureg

    XX_matrix = np.kron(X.matrix, X.matrix)
    assert not eng.backend.history
    assert np.allclose(eng.backend.unitary, XX_matrix)

    eng.deallocate_qubit(qureg[0])

    assert not eng.backend.history

    with pytest.warns(UserWarning):
        Y | qureg[1]

    # An internal call to flush() happens automatically since the X
    # gate occurs as the simulator is in an invalid state (after qubit
    # deallocation)
    assert len(eng.backend.history) == 1
    assert np.allclose(eng.backend.history[0], XX_matrix)
    assert np.allclose(eng.backend.unitary, Y.matrix)

    # Still ok
    eng.flush()
    Measure | qureg[1]

    # Nothing should have changed
    assert len(eng.backend.history) == 1
    assert np.allclose(eng.backend.history[0], XX_matrix)
    assert np.allclose(eng.backend.unitary, Y.matrix)


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

        with Control(eng, qureg[1], ctrl_state='0'):
            MatrixGate(mat1) | qureg[0]
            with Control(eng, qureg[2], ctrl_state='0'):
                MatrixGate(mat1) | qureg[0]

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

        ref_eng.flush()
        test_eng.flush()
        All(Measure) | ref_qureg
        All(Measure) | test_qureg


def test_unitary_functional_measurement():
    eng = MainEngine(UnitarySimulator())
    qubits = eng.allocate_qureg(5)
    # entangle all qubits:
    H | qubits[0]
    for qb in qubits[1:]:
        CNOT | (qubits[0], qb)
    eng.flush()
    All(Measure) | qubits

    bit_value_sum = sum([int(qubit) for qubit in qubits])
    assert bit_value_sum == 0 or bit_value_sum == 5

    qb1 = WeakQubitRef(engine=eng, idx=qubits[0].id)
    qb2 = WeakQubitRef(engine=eng, idx=qubits[1].id)
    with pytest.raises(ValueError):
        eng.backend._handle(Command(engine=eng, gate=Measure, qubits=([qb1],), controls=[qb2]))


def test_unitary_measure_mapped_qubit():
    eng = MainEngine(UnitarySimulator())
    qb1 = WeakQubitRef(engine=eng, idx=1)
    qb2 = WeakQubitRef(engine=eng, idx=2)
    cmd0 = Command(engine=eng, gate=Allocate, qubits=([qb1],))
    cmd1 = Command(engine=eng, gate=X, qubits=([qb1],))
    cmd2 = Command(
        engine=eng,
        gate=Measure,
        qubits=([qb1],),
        controls=[],
        tags=[LogicalQubitIDTag(2)],
    )
    with pytest.raises(NotYetMeasuredError):
        int(qb1)
    with pytest.raises(NotYetMeasuredError):
        int(qb2)

    eng.send([cmd0, cmd1])
    eng.flush()
    eng.send([cmd2])
    with pytest.raises(NotYetMeasuredError):
        int(qb1)
    assert int(qb2) == 1
