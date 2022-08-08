#   Copyright 2022 ProjectQ-Framework (www.projectq.ch)
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

"""Tests for projectq.backends._azure._utils.py."""

import math

import pytest

from projectq.cengines import DummyEngine, MainEngine
from projectq.ops import (
    CNOT,
    CX,
    NOT,
    Allocate,
    Barrier,
    C,
    Command,
    Deallocate,
    H,
    Measure,
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
    SqrtXGate,
    Swap,
    T,
    Tdag,
    Tdagger,
    X,
    Y,
    Z,
    get_inverse,
)
from projectq.types import WeakQubitRef

from .._exceptions import InvalidCommandError

_has_azure_quantum = True
try:
    import azure.quantum  # noqa: F401

    from projectq.backends._azure._utils import (
        is_available_ionq,
        is_available_quantinuum,
        to_json,
        to_qasm,
    )
except ImportError:
    _has_azure_quantum = False

has_azure_quantum = pytest.mark.skipif(not _has_azure_quantum, reason="azure quantum package is not installed")

V = SqrtXGate()
Vdag = get_inverse(V)


@has_azure_quantum
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
        (Rx(math.pi / 2), True),
        (Ry(math.pi / 2), True),
        (Rz(math.pi / 2), True),
        (Sdag, True),
        (Sdagger, True),
        (Tdag, True),
        (Tdagger, True),
        (Vdag, True),
        (Measure, True),
        (Allocate, True),
        (Deallocate, True),
        (Barrier, False),
    ],
)
def test_ionq_is_available_single_qubit_gates(single_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()

    cmd = Command(eng, single_qubit_gate, (qb0,))
    assert is_available_ionq(cmd) == expected_result, f'Failing on {single_qubit_gate} gate'


@has_azure_quantum
@pytest.mark.parametrize(
    "two_qubit_gate, expected_result",
    [
        (Swap, True),
        (CNOT, True),
        (CX, True),
        (Rxx(math.pi / 2), True),
        (Ryy(math.pi / 2), True),
        (Rzz(math.pi / 2), True),
    ],
)
def test_ionq_is_available_two_qubit_gates(two_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()

    cmd = Command(eng, two_qubit_gate, (qb0, qb1))
    assert is_available_ionq(cmd) == expected_result, f'Failing on {two_qubit_gate} gate'


@has_azure_quantum
@pytest.mark.parametrize(
    "base_gate, num_ctrl_qubits, expected_result",
    [
        (X, 0, True),
        (X, 1, True),
        (X, 2, True),
        (X, 3, True),
        (X, 4, True),
        (X, 5, True),
        (X, 6, True),
        (X, 7, True),
        (X, 8, False),
        (Y, 1, False),
    ],
)
def test_ionq_is_available_n_controlled_qubits_type_1(base_gate, num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    # pass controls as parameter
    cmd = Command(eng, base_gate, (qb0,), controls=qureg)
    assert is_available_ionq(cmd) == expected_result, 'Failing on {}-controlled {} gate'.format(
        num_ctrl_qubits, base_gate
    )


@has_azure_quantum
@pytest.mark.parametrize(
    "base_gate, num_ctrl_qubits, expected_result",
    [
        (X, 0, True),
        (X, 1, True),
        (X, 2, True),
        (X, 3, True),
        (X, 4, True),
        (X, 5, True),
        (X, 6, True),
        (X, 7, True),
        (X, 8, False),
        (Y, 1, False),
    ],
)
def test_ionq_is_available_n_controlled_qubits_type_2(base_gate, num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    n_controlled_gate = base_gate
    for index in range(num_ctrl_qubits):
        n_controlled_gate = C(n_controlled_gate)

    # pass controls as targets
    cmd = Command(
        eng,
        n_controlled_gate,
        (
            qureg,
            qb0,
        ),
    )
    assert is_available_ionq(cmd) == expected_result, 'Failing on {}-controlled {} gate'.format(
        num_ctrl_qubits, base_gate
    )


@has_azure_quantum
def test_ionq_is_available_negative_control():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)

    cmd = Command(eng, X, qubits=(qb0,), controls=qureg)
    assert is_available_ionq(cmd), "Failing on negative controlled gate"

    cmd = Command(eng, X, qubits=(qb0,), controls=qureg, control_state='1')
    assert is_available_ionq(cmd), "Failing on negative controlled gate"

    cmd = Command(eng, X, qubits=(qb0,), controls=qureg, control_state='0')
    assert not is_available_ionq(cmd), "Failing on negative controlled gate"


@has_azure_quantum
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
        (Rx(math.pi / 2), True),
        (Ry(math.pi / 2), True),
        (Rz(math.pi / 2), True),
        (Sdag, True),
        (Sdagger, True),
        (Tdag, True),
        (Tdagger, True),
        (Measure, True),
        (Allocate, True),
        (Deallocate, True),
        (Barrier, True),
        (SqrtX, False),
        (Vdag, False),
    ],
)
def test_quantinuum_is_available_single_qubit_gates(single_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()

    cmd = Command(eng, single_qubit_gate, (qb0,))
    assert is_available_quantinuum(cmd) == expected_result, f'Failing on {single_qubit_gate} gate'


@has_azure_quantum
@pytest.mark.parametrize(
    "two_qubit_gate, expected_result",
    [
        (CNOT, True),
        (CX, True),
        (Rxx(math.pi / 2), True),
        (Ryy(math.pi / 2), True),
        (Rzz(math.pi / 2), True),
        (Swap, False),
    ],
)
def test_quantinuum_is_available_two_qubit_gates(two_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()

    cmd = Command(eng, two_qubit_gate, (qb0, qb1))
    assert is_available_quantinuum(cmd) == expected_result, f'Failing on {two_qubit_gate} gate'


@has_azure_quantum
@pytest.mark.parametrize(
    "base_gate, num_ctrl_qubits, expected_result",
    [
        (X, 0, True),
        (X, 1, True),
        (X, 2, True),
        (X, 3, False),
        (Z, 0, True),
        (Z, 1, True),
        (Z, 2, True),
        (Z, 3, False),
        (Y, 1, False),
    ],
)
def test_quantinuum_is_available_n_controlled_qubits_type_1(base_gate, num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    cmd = Command(eng, base_gate, (qb0,), controls=qureg)
    assert is_available_quantinuum(cmd) == expected_result, 'Failing on {}-controlled {} gate'.format(
        num_ctrl_qubits, base_gate
    )


@has_azure_quantum
@pytest.mark.parametrize(
    "base_gate, num_ctrl_qubits, expected_result",
    [
        (X, 0, True),
        (X, 1, True),
        (X, 2, True),
        (X, 3, False),
        (Z, 0, True),
        (Z, 1, True),
        (Z, 2, True),
        (Z, 3, False),
        (Y, 1, False),
    ],
)
def test_quantinuum_is_available_n_controlled_qubits_type_2(base_gate, num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    n_controlled_gate = base_gate
    for index in range(num_ctrl_qubits):
        n_controlled_gate = C(n_controlled_gate)

    # pass controls as targets
    cmd = Command(
        eng,
        n_controlled_gate,
        (
            qureg,
            qb0,
        ),
    )
    assert is_available_quantinuum(cmd) == expected_result, 'Failing on {}-controlled {} gate'.format(
        num_ctrl_qubits, base_gate
    )


@has_azure_quantum
def test_quantinuum_is_available_negative_control():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(1)

    cmd = Command(eng, X, qubits=(qb0,), controls=qureg)
    assert is_available_quantinuum(cmd), "Failing on negative controlled gate"

    cmd = Command(eng, X, qubits=(qb0,), controls=qureg, control_state='1')
    assert is_available_quantinuum(cmd), "Failing on negative controlled gate"

    cmd = Command(eng, X, qubits=(qb0,), controls=qureg, control_state='0')
    assert not is_available_quantinuum(cmd), "Failing on negative controlled gate"


@has_azure_quantum
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
        (Rx(math.pi / 4), {'gate': 'rx', 'rotation': 0.785398163397, 'targets': [0]}),
        (Ry(math.pi / 4), {'gate': 'ry', 'rotation': 0.785398163397, 'targets': [0]}),
        (Rz(math.pi / 4), {'gate': 'rz', 'rotation': 0.785398163397, 'targets': [0]}),
        (Rx(math.pi / 2), {'gate': 'rx', 'rotation': 1.570796326795, 'targets': [0]}),
        (Ry(math.pi / 2), {'gate': 'ry', 'rotation': 1.570796326795, 'targets': [0]}),
        (Rz(math.pi / 2), {'gate': 'rz', 'rotation': 1.570796326795, 'targets': [0]}),
        (Rx(math.pi), {'gate': 'rx', 'rotation': 3.14159265359, 'targets': [0]}),
        (Ry(math.pi), {'gate': 'ry', 'rotation': 3.14159265359, 'targets': [0]}),
        (Rz(math.pi), {'gate': 'rz', 'rotation': 3.14159265359, 'targets': [0]}),
        (Sdag, {'gate': 'si', 'targets': [0]}),
        (Sdagger, {'gate': 'si', 'targets': [0]}),
        (Tdag, {'gate': 'ti', 'targets': [0]}),
        (Tdagger, {'gate': 'ti', 'targets': [0]}),
        (SqrtX, {'gate': 'v', 'targets': [0]}),
        (Vdag, {'gate': 'vi', 'targets': [0]}),
    ],
)
def test_to_json_single_qubit_gates(single_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = WeakQubitRef(engine=eng, idx=0)

    actual_result = to_json(Command(eng, single_qubit_gate, ([qb0],)))

    assert len(actual_result) == len(expected_result)
    assert actual_result['gate'] == expected_result['gate']
    assert actual_result['targets'] == expected_result['targets']
    if 'rotation' in expected_result:
        assert actual_result['rotation'] == pytest.approx(expected_result['rotation'])


@has_azure_quantum
@pytest.mark.parametrize(
    "two_qubit_gate, expected_result",
    [
        (Swap, {'gate': 'swap', 'targets': [0, 1]}),
        (CNOT, {'gate': 'x', 'targets': [1], 'controls': [0]}),
        (CX, {'gate': 'x', 'targets': [1], 'controls': [0]}),
        (Rxx(0), {'gate': 'xx', 'rotation': 0.0, 'targets': [0, 1]}),
        (Ryy(0), {'gate': 'yy', 'rotation': 0.0, 'targets': [0, 1]}),
        (Rzz(0), {'gate': 'zz', 'rotation': 0.0, 'targets': [0, 1]}),
        (Rxx(math.pi / 4), {'gate': 'xx', 'rotation': 0.785398163397, 'targets': [0, 1]}),
        (Ryy(math.pi / 4), {'gate': 'yy', 'rotation': 0.785398163397, 'targets': [0, 1]}),
        (Rzz(math.pi / 4), {'gate': 'zz', 'rotation': 0.785398163397, 'targets': [0, 1]}),
        (Rxx(math.pi / 2), {'gate': 'xx', 'rotation': 1.570796326795, 'targets': [0, 1]}),
        (Ryy(math.pi / 2), {'gate': 'yy', 'rotation': 1.570796326795, 'targets': [0, 1]}),
        (Rzz(math.pi / 2), {'gate': 'zz', 'rotation': 1.570796326795, 'targets': [0, 1]}),
        (Rxx(math.pi), {'gate': 'xx', 'rotation': 3.14159265359, 'targets': [0, 1]}),
        (Ryy(math.pi), {'gate': 'yy', 'rotation': 3.14159265359, 'targets': [0, 1]}),
        (Rzz(math.pi), {'gate': 'zz', 'rotation': 3.14159265359, 'targets': [0, 1]}),
    ],
)
def test_to_json_two_qubit_gates(two_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = WeakQubitRef(engine=eng, idx=0)
    qb1 = WeakQubitRef(engine=eng, idx=1)

    actual_result = to_json(Command(eng, two_qubit_gate, ([qb0], [qb1])))

    assert len(actual_result) == len(expected_result)
    assert actual_result['gate'] == expected_result['gate']
    assert actual_result['targets'] == expected_result['targets']
    if 'rotation' in expected_result:
        assert actual_result['rotation'] == pytest.approx(expected_result['rotation'])


@has_azure_quantum
@pytest.mark.parametrize(
    "base_gate, num_ctrl_qubits, expected_result",
    [
        (X, 0, {'gate': 'x', 'targets': [0]}),
        (X, 1, {'gate': 'x', 'targets': [0], 'controls': [1]}),
        (X, 2, {'gate': 'x', 'targets': [0], 'controls': [1, 2]}),
        (X, 3, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3]}),
        (X, 4, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3, 4]}),
        (X, 5, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3, 4, 5]}),
        (X, 6, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3, 4, 5, 6]}),
        (X, 7, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3, 4, 5, 6, 7]}),
    ],
)
def test_to_json_n_controlled_qubits_type_1(base_gate, num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    cmd = Command(eng, base_gate, (qb0,), controls=qureg)
    assert to_json(cmd) == expected_result, f'Failing on {num_ctrl_qubits}-controlled {base_gate} gate'


@has_azure_quantum
@pytest.mark.parametrize(
    "base_gate, num_ctrl_qubits, expected_result",
    [
        (X, 0, {'gate': 'x', 'targets': [0]}),
        (X, 1, {'gate': 'x', 'targets': [0], 'controls': [1]}),
        (X, 2, {'gate': 'x', 'targets': [0], 'controls': [1, 2]}),
        (X, 3, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3]}),
        (X, 4, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3, 4]}),
        (X, 5, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3, 4, 5]}),
        (X, 6, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3, 4, 5, 6]}),
        (X, 7, {'gate': 'x', 'targets': [0], 'controls': [1, 2, 3, 4, 5, 6, 7]}),
    ],
)
def test_to_json_n_controlled_qubits_type_2(base_gate, num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    n_controlled_gate = base_gate
    for index in range(num_ctrl_qubits):
        n_controlled_gate = C(n_controlled_gate)

    # pass controls as targets
    cmd = Command(
        eng,
        n_controlled_gate,
        (
            qureg,
            qb0,
        ),
    )
    assert to_json(cmd) == expected_result, f'Failing on {num_ctrl_qubits}-controlled {base_gate} gate'


@has_azure_quantum
def test_to_json_invalid_command_gate_not_available():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()

    cmd = Command(eng, Barrier, (qb0,))
    with pytest.raises(InvalidCommandError):
        to_json(cmd)


@has_azure_quantum
@pytest.mark.parametrize(
    "single_qubit_gate, expected_result",
    [
        (NOT, 'x q[0];'),
        (X, 'x q[0];'),
        (Y, 'y q[0];'),
        (Z, 'z q[0];'),
        (H, 'h q[0];'),
        (S, 's q[0];'),
        (T, 't q[0];'),
        (Rx(0), 'rx(0.0) q[0];'),
        (Ry(0), 'ry(0.0) q[0];'),
        (Rz(0), 'rz(0.0) q[0];'),
        (Rx(math.pi / 4), 'rx(0.785398163397) q[0];'),
        (Ry(math.pi / 4), 'ry(0.785398163397) q[0];'),
        (Rz(math.pi / 4), 'rz(0.785398163397) q[0];'),
        (Rx(math.pi / 2), 'rx(1.570796326795) q[0];'),
        (Ry(math.pi / 2), 'ry(1.570796326795) q[0];'),
        (Rz(math.pi / 2), 'rz(1.570796326795) q[0];'),
        (Rx(math.pi), 'rx(3.14159265359) q[0];'),
        (Ry(math.pi), 'ry(3.14159265359) q[0];'),
        (Rz(math.pi), 'rz(3.14159265359) q[0];'),
        (Sdag, 'sdg q[0];'),
        (Sdagger, 'sdg q[0];'),
        (Tdag, 'tdg q[0];'),
        (Tdagger, 'tdg q[0];'),
    ],
)
def test_to_qasm_single_qubit_gates(single_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = WeakQubitRef(engine=eng, idx=0)

    assert to_qasm(Command(eng, single_qubit_gate, ([qb0],))) == expected_result


@has_azure_quantum
@pytest.mark.parametrize(
    "two_qubit_gate, expected_result",
    [
        (CNOT, 'cx q[0], q[1];'),
        (CX, 'cx q[0], q[1];'),
        (Rxx(0), 'rxx(0.0) q[0], q[1];'),
        (Ryy(0), 'ryy(0.0) q[0], q[1];'),
        (Rzz(0), 'rzz(0.0) q[0], q[1];'),
        (Rxx(math.pi / 4), 'rxx(0.785398163397) q[0], q[1];'),
        (Ryy(math.pi / 4), 'ryy(0.785398163397) q[0], q[1];'),
        (Rzz(math.pi / 4), 'rzz(0.785398163397) q[0], q[1];'),
        (Rxx(math.pi / 2), 'rxx(1.570796326795) q[0], q[1];'),
        (Ryy(math.pi / 2), 'ryy(1.570796326795) q[0], q[1];'),
        (Rzz(math.pi / 2), 'rzz(1.570796326795) q[0], q[1];'),
        (Rxx(math.pi), 'rxx(3.14159265359) q[0], q[1];'),
        (Ryy(math.pi), 'ryy(3.14159265359) q[0], q[1];'),
        (Rzz(math.pi), 'rzz(3.14159265359) q[0], q[1];'),
    ],
)
def test_to_qasm_two_qubit_gates(two_qubit_gate, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = WeakQubitRef(engine=eng, idx=0)
    qb1 = WeakQubitRef(engine=eng, idx=1)

    assert to_qasm(Command(eng, two_qubit_gate, ([qb0], [qb1]))) == expected_result


@has_azure_quantum
@pytest.mark.parametrize(
    "n_qubit_gate, n, expected_result",
    [
        (Barrier, 2, 'barrier q[0], q[1];'),
        (Barrier, 3, 'barrier q[0], q[1], q[2];'),
        (Barrier, 4, 'barrier q[0], q[1], q[2], q[3];'),
    ],
)
def test_to_qasm_n_qubit_gates(n_qubit_gate, n, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qureg = eng.allocate_qureg(n)

    assert to_qasm(Command(eng, n_qubit_gate, (qureg,))) == expected_result


@has_azure_quantum
@pytest.mark.parametrize(
    "base_gate, num_ctrl_qubits, expected_result",
    [
        (X, 0, 'x q[0];'),
        (X, 1, 'cx q[1], q[0];'),
        (X, 2, 'ccx q[1], q[2], q[0];'),
        (Z, 0, 'z q[0];'),
        (Z, 1, 'cz q[1], q[0];'),
        (Z, 2, 'ccz q[1], q[2], q[0];'),
    ],
)
def test_to_qasm_n_controlled_qubits_type_1(base_gate, num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    cmd = Command(eng, base_gate, (qb0,), controls=qureg)
    assert to_qasm(cmd) == expected_result, f'Failing on {num_ctrl_qubits}-controlled {base_gate} gate'


@has_azure_quantum
@pytest.mark.parametrize(
    "base_gate, num_ctrl_qubits, expected_result",
    [
        (X, 0, 'x q[0];'),
        (X, 1, 'cx q[1], q[0];'),
        (X, 2, 'ccx q[1], q[2], q[0];'),
        (Z, 0, 'z q[0];'),
        (Z, 1, 'cz q[1], q[0];'),
        (Z, 2, 'ccz q[1], q[2], q[0];'),
    ],
)
def test_to_qasm_n_controlled_qubits_type_2(base_gate, num_ctrl_qubits, expected_result):
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qureg = eng.allocate_qureg(num_ctrl_qubits)

    n_controlled_gate = base_gate
    for index in range(num_ctrl_qubits):
        n_controlled_gate = C(n_controlled_gate)

    # pass controls as targets
    cmd = Command(
        eng,
        n_controlled_gate,
        (
            qureg,
            qb0,
        ),
    )
    assert to_qasm(cmd) == expected_result, f'Failing on {num_ctrl_qubits}-controlled {base_gate} gate'


@has_azure_quantum
def test_to_qasm_invalid_command_gate_not_available():
    qb0 = WeakQubitRef(None, idx=0)
    qb1 = WeakQubitRef(None, idx=1)

    cmd = Command(None, SqrtX, qubits=((qb0,),))
    with pytest.raises(InvalidCommandError):
        to_qasm(cmd)

    # NB: unsupported gate for 2 qubits
    cmd = Command(None, X, qubits=((qb0, qb1),))
    with pytest.raises(InvalidCommandError):
        to_qasm(cmd)
