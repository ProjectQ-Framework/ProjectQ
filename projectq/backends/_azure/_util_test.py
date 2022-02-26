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

from projectq.backends._azure._util import (
    is_available_ionq,
    is_available_honeywell,
    to_json,
    to_qasm
)


def test_is_available_ionq_success_cases():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()

    # Rotational gates
    for gate in (Rx, Ry, Rz, Rxx, Ryy, Rzz):
        cmd = Command(eng, gate(math.pi/2), (qubit1,))
        assert is_available_ionq(cmd), 'Failing on {} gate'.format(gate)

    # Shortcut gates (Single qubit)
    for gate in (NOT, X, Y, Z, H, S, T, SqrtX):
        cmd = Command(eng, gate, (qubit1,))
        assert is_available_ionq(cmd), 'Failing on {} gate'.format(gate)

    # Shortcut gates (Two qubit)
    for gate in (Swap, CNOT, CX):
        cmd = Command(eng, gate, (qubit1, qubit2))
        assert is_available_ionq(cmd), 'Failing on {} gate'.format(gate)

    # Meta gates
    for gate in (Measure, Allocate, Deallocate, Barrier):
        cmd = Command(eng, gate, (qubit1,))
        assert is_available_ionq(cmd), 'Failing on {} gate'.format(gate)

    # Daggered gates
    for gate in (Sdag, Sdagger, Tdag, Tdagger):
        cmd = Command(eng, gate, (qubit1,))
        assert is_available_ionq(cmd), 'Failing on {} gate'.format(gate)

    # Controlled gates
    for i in range(1, 8):
        qureg = eng.allocate_qureg(i)
        cmd = Command(eng, X, (qubit1,), controls=qureg)
        assert is_available_ionq(cmd), 'Failing on {}-Controlled X gate'.format(i)


def test_is_available_ionq_failure_cases():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()

    qureg = eng.allocate_qureg(8)
    cmd = Command(eng, X, (qubit1,), controls=qureg)
    assert not is_available_ionq(cmd), 'Failing on 8-Controlled X gate'


def test_is_available_honeywell_success_cases():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()

    # Rotational gates
    for gate in (Rx, Ry, Rz, Rxx, Ryy, Rzz):
        cmd = Command(eng, gate(math.pi / 2), (qubit1,))
        assert is_available_honeywell(cmd), 'Failing on {} gate'.format(gate)

    # Shortcut gates (Single qubit)
    for gate in (NOT, X, Y, Z, H, S, T):
        cmd = Command(eng, gate, (qubit1,))
        assert is_available_honeywell(cmd), 'Failing on {} gate'.format(gate)

    # Shortcut gates (Two qubit)
    for gate in (CNOT, CX):
        cmd = Command(eng, gate, (qubit1, qubit2))
        assert is_available_honeywell(cmd), 'Failing on {} gate'.format(gate)

    # Meta gates
    for gate in (Measure, Allocate, Deallocate, Barrier):
        cmd = Command(eng, gate, (qubit1,))
        assert is_available_honeywell(cmd), 'Failing on {} gate'.format(gate)

    # Daggered gates
    for gate in (Sdag, Sdagger, Tdag, Tdagger):
        cmd = Command(eng, gate, (qubit1,))
        assert is_available_honeywell(cmd), 'Failing on {} gate'.format(gate)

    # Controlled gates
    for i in range(1, 3):
        qureg = eng.allocate_qureg(i)
        cmd = Command(eng, X, (qubit1,), controls=qureg)
        assert is_available_honeywell(cmd), 'Failing on {}-Controlled X gate'.format(i)


def test_is_available_honeywell_failure_cases():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit1 = eng.allocate_qubit()

    qureg = eng.allocate_qureg(3)
    cmd = Command(eng, X, (qubit1,), controls=qureg)
    assert not is_available_honeywell(cmd), 'Failing on 3-Controlled X gate'


def test_to_json():
    assert True


def test_to_qasm():
    assert True
