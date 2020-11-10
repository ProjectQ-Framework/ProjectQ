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
"""Tests for projectq.libs.qasm._parse_qasm_qiskit.py."""

import pytest

from projectq.types import WeakQubitRef
from projectq.cengines import MainEngine, DummyEngine, BasicEngine
from projectq.ops import (X, Y, Z, T, Tdagger, S, Sdagger, H, Ph, R, Rx, Ry, Rz,
                          U2, U3, Swap, Toffoli, Barrier, All, C, Allocate,
                          Deallocate, Measure, FlushGate)
from copy import deepcopy
import tempfile

# ==============================================================================

try:
    from ._parse_qasm_qiskit import (apply_gate, apply_op, read_qasm_file,
                                     read_qasm_str)
    no_qiskit = False
except ImportError:
    no_qiskit = True

# ==============================================================================


class TestEngine(DummyEngine):
    def __init__(self, measurement_result=True):
        super().__init__(save_commands=True)
        self.is_last_engine = True
        self.measurement_result = measurement_result

    def is_available(self, cmd):
        return True

    def receive(self, command_list):
        for cmd in command_list:
            if cmd.gate == Measure:
                for qureg in cmd.qubits:
                    for qubit in qureg:
                        self.main_engine.set_measurement_result(
                            qubit, self.measurement_result)
            else:
                self.received_commands.append(cmd)


# ==============================================================================


@pytest.fixture
def eng():
    # rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])

    return MainEngine(backend=TestEngine(True), engine_list=[])


# ==============================================================================


@pytest.mark.skipif(no_qiskit, reason="Could not import Qiskit")
@pytest.mark.parametrize(
    'gate, n_qubits', (list(
        map(lambda x:
            (x, 1), [
                X, Y, Z, S, Sdagger, T, Tdagger, H, Barrier,
                Ph(1.12),
                Rx(1.12),
                Ry(1.12),
                Rz(1.12),
                R(1.12)
            ])) + list(map(lambda x:
                           (x, 2), [C(X), C(Y), C(Z), Swap, Barrier])) +
                       list(map(lambda x:
                                (x, 3), [Toffoli, C(Swap), Barrier])) +
                       list(map(lambda x: (x, 10), [Barrier]))),
    ids=lambda x: str(x))
def test_apply_gate(gate, n_qubits):
    backend = DummyEngine()
    backend.is_last_engine = True

    gate.engine = backend
    qubits = [WeakQubitRef(backend, idx) for idx in range(n_qubits)]

    apply_gate(gate, qubits)


# ==============================================================================
# OpenQASM 2.0 tests


def test_read_qasm2_empty(eng):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
"""

    read_qasm_str(eng, qasm_str)
    assert not eng.backend.received_commands


def test_read_qasm2_allocation(eng):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
"""

    engine = deepcopy(eng)
    qubits_map, bits_map = read_qasm_str(engine, qasm_str)
    assert not bits_map
    assert len(engine.backend.received_commands) == 1
    assert engine.backend.received_commands[0].gate == Allocate

    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
"""

    engine = deepcopy(eng)
    qubits_map, bits_map = read_qasm_str(engine, qasm_str)
    assert not bits_map
    assert len(engine.backend.received_commands) == 4
    assert all(cmd.gate == Allocate for cmd in engine.backend.received_commands)

    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[1];
creg d[2];
"""

    engine = deepcopy(eng)
    qubits_map, bits_map = read_qasm_str(engine, qasm_str)
    assert bits_map == {'c': [False], 'd': [False, False]}
    assert len(engine.backend.received_commands) == 3
    assert all(cmd.gate == Allocate for cmd in engine.backend.received_commands)


@pytest.mark.parametrize('gate, projectq_gate',
                         [('x', X), ('y', Y), ('z', Z), ('h', H), ('s', S),
                          ('sdg', Sdagger), ('t', T), ('tdg', Tdagger),
                          ('rx(1.12)', Rx(1.12)), ('ry(1.12)', Ry(1.12)),
                          ('rz(1.12)', Rz(1.12)), ('u1(1.12)', Rz(1.12)),
                          ('u2(1.12,1.12)', U2(1.12, 1.12)),
                          ('u3(1.12,1.12,1.12)', U3(1.12, 1.12, 1.12))],
                         ids=lambda x: str(x))
def test_read_qasm2_single_qubit_gates(eng, gate, projectq_gate):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
{} q[0];
""".format(gate)

    engine = deepcopy(eng)
    qubits_map, bits_map = read_qasm_str(engine, qasm_str)
    assert not bits_map
    assert len(engine.backend.received_commands) == 2
    assert engine.backend.received_commands[0].gate == Allocate
    assert engine.backend.received_commands[1].gate == projectq_gate


@pytest.mark.parametrize(
    'gate, projectq_gate',
    [
        ('cx', X),
        ('cy', Y),
        ('cz', Z),
        ('ch', H),
        ('crz(1.12)', Rz(1.12)),
        ('cu1(1.12)', Rz(1.12)),
        # ('cu2(1.12,1.12)',  U2(1.12, 1.12)),
        ('cu3(1.12,1.12,1.12)', U3(1.12, 1.12, 1.12)),
        ('swap', Swap)
    ],
    ids=lambda x: str(x))
def test_read_qasm2_two_qubit_gates(eng, gate, projectq_gate):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
{} q[0], q[1];
""".format(gate)

    engine = deepcopy(eng)
    qubits_map, bits_map = read_qasm_str(engine, qasm_str)
    assert not bits_map
    assert len(engine.backend.received_commands) == 3
    assert engine.backend.received_commands[0].gate == Allocate
    assert engine.backend.received_commands[1].gate == Allocate
    cmd = engine.backend.received_commands[2]
    assert cmd.gate == projectq_gate
    if cmd.gate == Swap:
        assert not cmd.control_qubits
        assert len([qubit for qureg in cmd.qubits for qubit in qureg]) == 2
    else:
        assert len(cmd.control_qubits) == 1
        assert len([qubit for qureg in cmd.qubits for qubit in qureg]) == 1


@pytest.mark.parametrize('gate, projectq_gate', [('ccx', X), ('cswap', Swap)],
                         ids=lambda x: str(x))
def test_read_qasm2_three_qubit_gates(eng, gate, projectq_gate):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
{} q[0], q[1], q[2];
""".format(gate)

    engine = deepcopy(eng)
    qubits_map, bits_map = read_qasm_str(engine, qasm_str)
    assert not bits_map
    assert len(engine.backend.received_commands) == 4
    assert engine.backend.received_commands[0].gate == Allocate
    assert engine.backend.received_commands[1].gate == Allocate
    assert engine.backend.received_commands[2].gate == Allocate
    cmd = engine.backend.received_commands[3]
    assert cmd.gate == projectq_gate
    if cmd.gate == Swap:
        assert len(cmd.control_qubits) == 1
        assert len([qubit for qureg in cmd.qubits for qubit in qureg]) == 2
    else:
        assert len(cmd.control_qubits) == 2
        assert len([qubit for qureg in cmd.qubits for qubit in qureg]) == 1


def test_read_qasm2_if_expr(eng):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c0[1];
measure q[0] -> c0;
if (c0 == 1) x q[0];
"""

    engine = deepcopy(eng)
    qubits_map, bits_map = read_qasm_str(engine, qasm_str)
    assert bits_map == {'c0': [True]}
    assert len(engine.backend.received_commands) == 4
    assert engine.backend.received_commands[0].gate == Allocate
    assert engine.backend.received_commands[1].gate == Allocate
    assert engine.backend.received_commands[2].gate == FlushGate()
    cmd = engine.backend.received_commands[3]
    assert cmd.gate == X
    assert len([qubit for qureg in cmd.qubits for qubit in qureg]) == 1

    engine = deepcopy(eng)
    engine.backend.measurement_result = False
    qubits_map, bits_map = read_qasm_str(engine, qasm_str)
    assert bits_map == {'c0': [False]}
    assert len(engine.backend.received_commands) == 3
    assert engine.backend.received_commands[0].gate == Allocate
    assert engine.backend.received_commands[1].gate == Allocate
    assert engine.backend.received_commands[2].gate == FlushGate()


def test_read_qasm2_gate_def(eng):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];

gate my_cu1(lambda) a,b
{
  u1(lambda/2) a;
  cx a,b;
  u1(-lambda/2) b;
  cx a,b;
  u1(lambda/2) b;
}
gate empty() a,b
{
}

empty q[0],q[1];
my_cu1(1) q[0],q[1];
"""

    qubits_map, bits_map = read_qasm_str(eng, qasm_str)
    assert not bits_map
    assert len(eng.backend.received_commands) == 7
    assert eng.backend.received_commands[0].gate == Allocate
    assert eng.backend.received_commands[1].gate == Allocate

    a, b = qubits_map['q']

    cmd = eng.backend.received_commands[2]
    assert cmd.gate == Rz(0.5)
    assert [qubit for qureg in cmd.qubits for qubit in qureg] == [a]

    cmd = eng.backend.received_commands[3]
    assert cmd.gate == X
    assert cmd.control_qubits == [a]
    assert [qubit for qureg in cmd.qubits for qubit in qureg] == [b]

    cmd = eng.backend.received_commands[4]
    assert cmd.gate == Rz(-0.5)
    assert [qubit for qureg in cmd.qubits for qubit in qureg] == [b]

    cmd = eng.backend.received_commands[5]
    assert cmd.gate == X
    assert cmd.control_qubits == [a]
    assert [qubit for qureg in cmd.qubits for qubit in qureg] == [b]

    cmd = eng.backend.received_commands[6]
    assert cmd.gate == Rz(0.5)
    assert [qubit for qureg in cmd.qubits for qubit in qureg] == [b]


def test_read_qasm2_file(eng):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c0[1];
"""

    with tempfile.NamedTemporaryFile() as fd:
        fd.write((qasm_str + '\n').encode())
        fd.seek(0)
        engine = deepcopy(eng)
        qubits_map, bits_map = read_qasm_file(engine, fd.name)
        assert bits_map == {'c0': [False]}
        assert len(engine.backend.received_commands) == 2
        assert engine.backend.received_commands[0].gate == Allocate
        assert engine.backend.received_commands[1].gate == Allocate


def test_qasm_qft2(eng):
    qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg a[2];
creg b[2];
measure a -> b;
qreg q[3];
creg c[3];
// optional post-rotation for state tomography
gate post q { }
u3(0.3,0.2,0.1) q[0];
h q[1];
cx q[1],q[2];
barrier q;
cx q[0],q[1];
h q[0];
measure q[0] -> c[0];
measure q[1] -> c[1];
if(c==1) z q[2];
if(c==2) x q[2];
if(c==3) y q[2];
if(c==4) z q[1];
if(c==5) x q[1];
if(c==6) y q[1];
if(c==7) z q[0];
if(c==8) x q[0];
post q[2];
measure q[2] -> c[2];
    """

    qubits_map, bits_map = read_qasm_str(eng, qasm_str)
    assert {'q', 'a'} == set(qubits_map)
    assert len(qubits_map['a']) == 2
    assert len(qubits_map['q']) == 3
    assert bits_map == {'b': [True, True], 'c': [True, True, True]}

    assert len([
        cmd for cmd in eng.backend.received_commands if cmd.gate == Allocate
    ]) == 5
    assert len([
        cmd for cmd in eng.backend.received_commands
        if isinstance(cmd.gate, U3)
    ]) == 1
    assert len([cmd for cmd in eng.backend.received_commands
                if cmd.gate == X]) == 2
    cmds = [cmd for cmd in eng.backend.received_commands if cmd.gate == Y]
    assert len(cmds) == 1
    assert ([qubits_map['q'][1]
             ] == [qubit for qureg in cmds[0].qubits for qubit in qureg])
    assert len([cmd for cmd in eng.backend.received_commands
                if cmd.gate == Z]) == 0
    assert len([cmd for cmd in eng.backend.received_commands
                if cmd.gate == H]) == 2
    cmds = [cmd for cmd in eng.backend.received_commands if cmd.gate == Barrier]
    assert len(cmds) == 1
    assert len([qubit for qureg in cmds[0].qubits for qubit in qureg]) == 3


# ==============================================================================
# OpenQASM 3.0 tests (experimental)


@pytest.mark.xfail
def test_read_qasm3_empty(eng):
    qasm_str = """
OPENQASM 3.0;
include "stdgates.qasm";
"""

    qubits_map, bits_map = read_qasm_str(eng, qasm_str)
    assert not eng.backend.received_commands
