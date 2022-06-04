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

import math

from projectq.cengines import DummyEngine, MainEngine
from projectq.types import WeakQubitRef
from projectq.ops import (
    Allocate,
    Barrier,
    Command,
    CNOT,
    CX,
    Deallocate,
    H,
    Measure,
    NOT,
    Rx,
    Rxx,
    Ry,
    Ryy,
    Rz,
    Rzz,
    S,
    Sdag,
    Sdagger,
    SqrtX,
    Swap,
    T,
    Tdag,
    Tdagger,
    X,
    Y,
    Z
)

from projectq.backends._azure._util import (  # noqa
    is_available_ionq,
    is_available_quantinuum,
    to_json,
    to_qasm
)

import pytest


@pytest.mark.parametrize(
    "single_qubit_gate, expected_result",
    [
        (NOT, True),
        (X, True),
        (Y, True),
        (Z, True),
        (H, True),
        (S, True),
        (T, True),
        (SqrtX, True),
        (Rx(math.pi/2), True),
        (Ry(math.pi/2), True),
        (Rz(math.pi/2), True),
        (Sdag, True),
        (Sdagger, True),
        (Tdag, True),
        (Tdagger, True),
        (Measure, True),
        (Allocate, True),
        (Deallocate, True),
        (Barrier, True)
    ]
)
def test_ionq_is_available_single_qubit_gates(single_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()

    cmd = Command(eng, single_qubit_gate, (qb0,))
    assert is_available_ionq(cmd) == expected_result, 'Failing on {} gate'.format(single_qubit_gate)


@pytest.mark.parametrize(
    "two_qubit_gate, expected_result",
    [
        (Swap, True),
        (CNOT, True),
        (CX, True),
        (Rxx(math.pi/2), True),
        (Ryy(math.pi/2), True),
        (Rzz(math.pi/2), True)
    ]
)
def test_ionq_is_available_two_qubit_gates(two_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()

    cmd = Command(eng, two_qubit_gate, (qb0, qb1))
    assert is_available_ionq(cmd) == expected_result, 'Failing on {} gate'.format(two_qubit_gate)


@pytest.mark.parametrize(
    "num_ctrl_qubits, expected_result",
    [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
        (8, False),
    ],
)
def test_ionq_is_available_controlled_qubits(num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    cmd = Command(eng, X, (qb0,), controls=qureg)
    assert is_available_ionq(cmd) == expected_result, 'Failing on {}-controlled gate'.format(num_ctrl_qubits)


@pytest.mark.parametrize(
    "single_qubit_gate, expected_result",
    [
        (NOT, True),
        (X, True),
        (Y, True),
        (Z, True),
        (H, True),
        (S, True),
        (T, True),
        (Rx(math.pi/2), True),
        (Ry(math.pi/2), True),
        (Rz(math.pi/2), True),
        (Sdag, True),
        (Sdagger, True),
        (Tdag, True),
        (Tdagger, True),
        (Measure, True),
        (Allocate, True),
        (Deallocate, True),
        (Barrier, True),
        (SqrtX, False)
    ]
)
def test_quantinuum_is_available_single_qubit_gates(single_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()

    cmd = Command(eng, single_qubit_gate, (qb0,))
    assert is_available_quantinuum(cmd) == expected_result, 'Failing on {} gate'.format(single_qubit_gate)


@pytest.mark.parametrize(
    "two_qubit_gate, expected_result",
    [
        (CNOT, True),
        (CX, True),
        (Rxx(math.pi/2), True),
        (Ryy(math.pi/2), True),
        (Rzz(math.pi/2), True),
        (Swap, False)
    ]
)
def test_quantinuum_is_available_two_qubit_gates(two_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()

    cmd = Command(eng, two_qubit_gate, (qb0, qb1))
    assert is_available_quantinuum(cmd) == expected_result, 'Failing on {} gate'.format(two_qubit_gate)


@pytest.mark.parametrize(
    "num_ctrl_qubits, expected_result",
    [
        (0, True),
        (1, True),
        (2, True),
        (3, False),
    ]
)
def test_quantinuum_is_available_controlled_qubits(num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    cmd = Command(eng, X, (qb0,), controls=qureg)
    assert is_available_quantinuum(cmd) == expected_result, 'Failing on {}-controlled gate'.format(num_ctrl_qubits)


@pytest.mark.parametrize(
    "single_qubit_gate, expected_result",
    [
        (NOT, {'gate': 'x', 'targets': [0]}),
        (X, {'gate': 'x', 'targets': [0]}),
        (Y, {'gate': 'y', 'targets': [0]}),
        (Z, {'gate': 'z', 'targets': [0]}),
        (H, {'gate': 'h', 'targets': [0]}),
        (S, {'gate': 's', 'targets': [0]}),
        (T, {'gate': 't', 'targets': [0]}),
        (Rx(0), {'gate': 'rx', 'rotation': 0.0, 'targets': [0]}),
        (Ry(0), {'gate': 'ry', 'rotation': 0.0, 'targets': [0]}),
        (Rz(0), {'gate': 'rz', 'rotation': 0.0, 'targets': [0]}),
        (Rx(math.pi/4), {'gate': 'rx', 'rotation': 0.785398163397, 'targets': [0]}),
        (Ry(math.pi/4), {'gate': 'ry', 'rotation': 0.785398163397, 'targets': [0]}),
        (Rz(math.pi/4), {'gate': 'rz', 'rotation': 0.785398163397, 'targets': [0]}),
        (Rx(math.pi/2), {'gate': 'rx', 'rotation': 1.570796326795, 'targets': [0]}),
        (Ry(math.pi/2), {'gate': 'ry', 'rotation': 1.570796326795, 'targets': [0]}),
        (Rz(math.pi/2), {'gate': 'rz', 'rotation': 1.570796326795, 'targets': [0]}),
        (Rx(math.pi), {'gate': 'rx', 'rotation': 3.14159265359, 'targets': [0]}),
        (Ry(math.pi), {'gate': 'ry', 'rotation': 3.14159265359, 'targets': [0]}),
        (Rz(math.pi), {'gate': 'rz', 'rotation': 3.14159265359, 'targets': [0]}),
        (Sdag, {'gate': 'si', 'targets': [0]}),
        (Sdagger, {'gate': 'si', 'targets': [0]}),
        (Tdag, {'gate': 'ti', 'targets': [0]}),
        (Tdagger, {'gate': 'ti', 'targets': [0]}),
        # (Barrier, {'gate': 'h', 'targets': [0]}),  # TODO: Fix this
        (SqrtX, {'gate': 'v', 'targets': [0]})
    ]
)
def test_to_json_single_qubit_gates(single_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = WeakQubitRef(engine=eng, idx=0)

    assert to_json(Command(eng, single_qubit_gate, ([qb0],))) == expected_result


@pytest.mark.parametrize(
    "two_qubit_gate, expected_result",
    [
        (Swap, {'gate': 'swap', 'targets': [0, 1]}),
        # (CNOT, {'gate': 'x', 'targets': [0, 1]}),  # TODO: Fix this
        # (CX, {'gate': 'x', 'targets': [0, 1]}),
        (Rxx(0), {'gate': 'xx', 'rotation': 0.0, 'targets': [0, 1]}),
        (Ryy(0), {'gate': 'yy', 'rotation': 0.0, 'targets': [0, 1]}),
        (Rzz(0), {'gate': 'zz', 'rotation': 0.0, 'targets': [0, 1]}),
        (Rxx(math.pi/4), {'gate': 'xx', 'rotation': 0.785398163397, 'targets': [0, 1]}),
        (Ryy(math.pi/4), {'gate': 'yy', 'rotation': 0.785398163397, 'targets': [0, 1]}),
        (Rzz(math.pi/4), {'gate': 'zz', 'rotation': 0.785398163397, 'targets': [0, 1]}),
        (Rxx(math.pi/2), {'gate': 'xx', 'rotation': 1.570796326795, 'targets': [0, 1]}),
        (Ryy(math.pi/2), {'gate': 'yy', 'rotation': 1.570796326795, 'targets': [0, 1]}),
        (Rzz(math.pi/2), {'gate': 'zz', 'rotation': 1.570796326795, 'targets': [0, 1]}),
        (Rxx(math.pi), {'gate': 'xx', 'rotation': 3.14159265359, 'targets': [0, 1]}),
        (Ryy(math.pi), {'gate': 'yy', 'rotation': 3.14159265359, 'targets': [0, 1]}),
        (Rzz(math.pi), {'gate': 'zz', 'rotation': 3.14159265359, 'targets': [0, 1]})
    ]
)
def test_to_json_two_qubit_gates(two_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = WeakQubitRef(engine=eng, idx=0)
    qb1 = WeakQubitRef(engine=eng, idx=1)

    assert to_json(Command(eng, two_qubit_gate, ([qb0], [qb1]))) == expected_result


def test_to_qasm():
    assert True
