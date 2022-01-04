# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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
"""Tests for projectq.cengines._openqasm.py."""

import re

import pytest

from projectq.cengines import DummyEngine, MainEngine
from projectq.meta import Control
from projectq.ops import (
    NOT,
    All,
    Allocate,
    Barrier,
    Command,
    Deallocate,
    Entangle,
    H,
    Measure,
    Ph,
    R,
    Rx,
    Ry,
    Rz,
    S,
    Sdagger,
    T,
    Tdagger,
    X,
    Y,
    Z,
)
from projectq.types import WeakQubitRef

from ._qasm import OpenQASMBackend

# ==============================================================================


def test_qasm_init():
    eng = OpenQASMBackend()
    assert isinstance(eng.qasm, list)
    assert not eng._qreg_dict
    assert not eng._creg_dict
    assert eng._reg_index == 0
    assert not eng._available_indices


@pytest.mark.parametrize("qubit_id_redux", [False, True])
def test_qasm_allocate_deallocate(qubit_id_redux):
    backend = OpenQASMBackend(qubit_id_mapping_redux=qubit_id_redux)
    assert backend._qubit_id_mapping_redux == qubit_id_redux

    eng = MainEngine(backend)
    qubit = eng.allocate_qubit()
    eng.flush()

    assert len(backend._qreg_dict) == 1
    assert len(backend._creg_dict) == 1
    assert backend._reg_index == 1
    assert not backend._available_indices
    qasm = '\n'.join(eng.backend.qasm)
    assert re.search(r'qubit\s+q0', qasm)
    assert re.search(r'bit\s+c0', qasm)

    qureg = eng.allocate_qureg(5)  # noqa: F841
    eng.flush()

    assert len(backend._qreg_dict) == 6
    assert len(backend._creg_dict) == 6
    assert backend._reg_index == 6
    assert not backend._available_indices
    qasm = '\n'.join(eng.backend.qasm)
    for i in range(1, 6):
        assert re.search(r'qubit\s+q{}'.format(i), qasm)
        assert re.search(r'bit\s+c{}'.format(i), qasm)

    del qubit
    eng.flush()
    if qubit_id_redux:
        assert len(backend._qreg_dict) == 5
        assert len(backend._creg_dict) == 5
        assert backend._reg_index == 6
        assert backend._available_indices == [0]
    else:
        assert len(backend._qreg_dict) == 6
        assert len(backend._creg_dict) == 6
        assert backend._reg_index == 6
        assert not backend._available_indices

    qubit = eng.allocate_qubit()  # noqa: F841
    eng.flush()

    if qubit_id_redux:
        assert len(backend._qreg_dict) == 6
        assert len(backend._creg_dict) == 6
        assert backend._reg_index == 6
        assert not backend._available_indices
    else:
        assert len(backend._qreg_dict) == 7
        assert len(backend._creg_dict) == 7
        assert backend._reg_index == 7
        assert not backend._available_indices


@pytest.mark.parametrize(
    "gate, is_available",
    [
        (X, True),
        (Y, True),
        (Z, True),
        (T, True),
        (Tdagger, True),
        (S, True),
        (Sdagger, True),
        (Allocate, True),
        (Deallocate, True),
        (Measure, True),
        (NOT, True),
        (Rx(0.5), True),
        (Ry(0.5), True),
        (Rz(0.5), True),
        (R(0.5), True),
        (Ph(0.5), True),
        (Barrier, True),
        (Entangle, False),
    ],
    ids=lambda l: str(l),
)
def test_qasm_is_available(gate, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[OpenQASMBackend()])
    qubit1 = eng.allocate_qubit()
    cmd = Command(eng, gate, (qubit1,))
    eng.is_available(cmd) == is_available

    eng = MainEngine(backend=OpenQASMBackend(), engine_list=[])
    qubit1 = eng.allocate_qubit()
    cmd = Command(eng, gate, (qubit1,))
    eng.is_available(cmd) == is_available


@pytest.mark.parametrize(
    "gate, is_available",
    [
        (H, True),
        (X, True),
        (NOT, True),
        (Y, True),
        (Z, True),
        (Rz(0.5), True),
        (R(0.5), True),
        (Rx(0.5), False),
        (Ry(0.5), False),
    ],
    ids=lambda l: str(l),
)
def test_qasm_is_available_1control(gate, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[OpenQASMBackend()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    cmd = Command(eng, gate, (qubit1,), controls=qureg)
    assert eng.is_available(cmd) == is_available

    eng = MainEngine(backend=OpenQASMBackend(), engine_list=[])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)
    cmd = Command(eng, gate, (qubit1,), controls=qureg)
    assert eng.is_available(cmd) == is_available


@pytest.mark.parametrize(
    "gate, is_available",
    [
        (X, True),
        (NOT, True),
        (Y, False),
        (Z, False),
        (Rz(0.5), False),
        (R(0.5), False),
        (Rx(0.5), False),
        (Ry(0.5), False),
    ],
    ids=lambda l: str(l),
)
def test_qasm_is_available_2control(gate, is_available):
    eng = MainEngine(backend=DummyEngine(), engine_list=[OpenQASMBackend()])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(2)
    cmd = Command(eng, gate, (qubit1,), controls=qureg)
    assert eng.is_available(cmd) == is_available

    eng = MainEngine(backend=OpenQASMBackend(), engine_list=[])
    qubit1 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(2)
    cmd = Command(eng, gate, (qubit1,), controls=qureg)
    assert eng.is_available(cmd) == is_available


def test_ibm_backend_is_available_negative_control():
    backend = OpenQASMBackend()
    backend.is_last_engine = True

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)

    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1]))
    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='1'))
    assert not backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='0'))

    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1]))
    assert backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='1'))
    assert not backend.is_available(Command(None, X, qubits=([qb0],), controls=[qb1], control_state='0'))


def test_qasm_test_qasm_single_qubit_gates():
    eng = MainEngine(backend=OpenQASMBackend(), engine_list=[])
    qubit = eng.allocate_qubit()

    H | qubit
    S | qubit
    T | qubit
    Sdagger | qubit
    Tdagger | qubit
    X | qubit
    Y | qubit
    Z | qubit
    R(0.5) | qubit
    Rx(0.5) | qubit
    Ry(0.5) | qubit
    Rz(0.5) | qubit
    Ph(0.5) | qubit
    NOT | qubit
    Measure | qubit
    eng.flush()

    qasm = eng.backend.qasm
    # Note: ignoring header and footer for comparison
    assert qasm[2:-1] == [
        'qubit q0;',
        'bit c0;',
        'h q0;',
        's q0;',
        't q0;',
        'sdg q0;',
        'tdg q0;',
        'x q0;',
        'y q0;',
        'z q0;',
        'u1(0.5) q0;',
        'rx(0.5) q0;',
        'ry(0.5) q0;',
        'rz(0.5) q0;',
        'u1(-0.25) q0;',
        'x q0;',
        'c0 = measure q0;',
    ]


def test_qasm_test_qasm_single_qubit_gates_control():
    eng = MainEngine(backend=OpenQASMBackend(), engine_list=[])
    qubit = eng.allocate_qubit()
    ctrl = eng.allocate_qubit()

    with Control(eng, ctrl):
        H | qubit
        X | qubit
        Y | qubit
        Z | qubit
        NOT | qubit
        R(0.5) | qubit
        Rz(0.5) | qubit
        Ph(0.5) | qubit
    All(Measure) | qubit + ctrl
    eng.flush()

    qasm = eng.backend.qasm
    # Note: ignoring header and footer for comparison
    assert qasm[2:-1] == [
        'qubit q0;',
        'bit c0;',
        'qubit q1;',
        'bit c1;',
        'ch q1,q0;',
        'cx q1,q0;',
        'cy q1,q0;',
        'cz q1,q0;',
        'cx q1,q0;',
        'cu1(0.5) q1,q0;',
        'crz(0.5) q1,q0;',
        'cu1(-0.25) q1,q0;',
        'c0 = measure q0;',
        'c1 = measure q1;',
    ]

    # Also test invalid gates with 1 control qubits
    with pytest.raises(RuntimeError):
        with Control(eng, ctrl):
            T | qubit
        eng.flush()


def test_qasm_test_qasm_single_qubit_gates_controls():
    eng = MainEngine(backend=OpenQASMBackend(), engine_list=[], verbose=True)
    qubit = eng.allocate_qubit()
    ctrls = eng.allocate_qureg(2)

    with Control(eng, ctrls):
        X | qubit
        NOT | qubit
    eng.flush()

    qasm = eng.backend.qasm
    # Note: ignoring header and footer for comparison
    assert qasm[2:-1] == [
        'qubit q0;',
        'bit c0;',
        'qubit q1;',
        'bit c1;',
        'qubit q2;',
        'bit c2;',
        'ccx q1,q2,q0;',
        'ccx q1,q2,q0;',
    ]

    # Also test invalid gates with 2 control qubits
    with pytest.raises(RuntimeError):
        with Control(eng, ctrls):
            Y | qubit
        eng.flush()


def test_qasm_no_collate():
    qasm_list = []

    def _process(output):
        qasm_list.append(output)

    eng = MainEngine(backend=OpenQASMBackend(collate_callback=_process, qubit_id_mapping_redux=False), engine_list=[])
    qubit = eng.allocate_qubit()
    ctrls = eng.allocate_qureg(2)

    H | qubit
    with Control(eng, ctrls):
        X | qubit
        NOT | qubit

    eng.flush()

    All(Measure) | qubit + ctrls
    eng.flush()

    print(qasm_list)
    assert len(qasm_list) == 2

    # Note: ignoring header for comparison
    assert qasm_list[0][2:] == [
        'qubit q0;',
        'bit c0;',
        'qubit q1;',
        'bit c1;',
        'qubit q2;',
        'bit c2;',
        'h q0;',
        'ccx q1,q2,q0;',
        'ccx q1,q2,q0;',
    ]

    # Note: ignoring header for comparison
    assert qasm_list[1][2:] == [
        'qubit q0;',
        'qubit q1;',
        'qubit q2;',
        'bit c0;',
        'bit c1;',
        'bit c2;',
        'c0 = measure q0;',
        'c1 = measure q1;',
        'c2 = measure q2;',
    ]


def test_qasm_name_callback():
    def _qubit(index):
        return 'qubit_{}'.format(index)

    def _bit(index):
        return 'classical_bit_{}'.format(index)

    eng = MainEngine(backend=OpenQASMBackend(qubit_callback=_qubit, bit_callback=_bit), engine_list=[])

    qubit = eng.allocate_qubit()
    Measure | qubit

    qasm = eng.backend.qasm
    assert qasm[2:] == ['qubit qubit_0;', 'bit classical_bit_0;', 'classical_bit_0 = measure qubit_0;']
