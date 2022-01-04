# -*- coding: utf-8 -*-
#   Copyright 2021 <Huawei Technologies Co., Ltd>
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

import platform
import tempfile

import pytest

from projectq.backends import CommandPrinter
from projectq.cengines import DummyEngine, MainEngine
from projectq.ops import AllocateQubitGate, HGate, MeasureGate, SGate, TGate, XGate

# ==============================================================================

_has_qiskit = True
try:
    import qiskit  # noqa: F401

    from ._parse_qasm_qiskit import read_qasm_file, read_qasm_str
except ImportError:
    _has_qiskit = False

has_qiskit = pytest.mark.skipif(not _has_qiskit, reason="Qiskit is not installed")

# ------------------------------------------------------------------------------


@pytest.fixture
def eng():
    return MainEngine(backend=DummyEngine(save_commands=True), engine_list=[])


@pytest.fixture
def dummy_eng():
    dummy = DummyEngine(save_commands=True)
    eng = MainEngine(backend=CommandPrinter(accept_input=False, default_measure=True), engine_list=[dummy])
    return dummy, eng


@pytest.fixture
def iqft_example():
    return '''
// QFT and measure, version 1
OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
creg c[4];
h q;
barrier q;
h q[0];

measure q[0] -> c[0];
if(c==1) u1(pi/2) q[1];
h q[1];
measure q[1] -> c[1];
if(c==1) u1(pi/4) q[2];
if(c==2) u1(pi/2) q[2];
if(c==3) u1(pi/2+pi/4) q[2];
h q[2];
measure q[2] -> c[2];
if(c==1) u1(pi/8) q[3];
if(c==2) u1(pi/4) q[3];
if(c==3) u1(pi/4+pi/8) q[3];
if(c==4) u1(pi/2) q[3];
if(c==5) u1(pi/2+pi/8) q[3];
if(c==6) u1(pi/2+pi/4) q[3];
if(c==7) u1(pi/2+pi/4+pi/8) q[3];
h q[3];
measure q[3] -> c[3];
'''


# ==============================================================================


def filter_gates(dummy, gate_class):
    return [cmd for cmd in dummy.received_commands if isinstance(cmd.gate, gate_class)]


def exclude_gates(dummy, gate_class):
    return [cmd for cmd in dummy.received_commands if not isinstance(cmd.gate, gate_class)]


# ==============================================================================


@has_qiskit
def test_read_qasm_allocation(eng):
    qasm_str = '''
OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
creg c[1];
qreg q2[3];
creg c2[2];
'''
    qubits_map, bits_map = read_qasm_str(eng, qasm_str)
    assert {'q', 'q2'} == set(qubits_map)
    assert len(qubits_map['q']) == 1
    assert len(qubits_map['q2']) == 3
    assert {'c', 'c2'} == set(bits_map)
    assert len(bits_map['c']) == 1
    assert len(bits_map['c2']) == 2
    assert all(isinstance(cmd.gate, AllocateQubitGate) for cmd in eng.backend.received_commands)


@has_qiskit
def test_read_qasm_if_expr_single_cbit(dummy_eng):
    dummy, eng = dummy_eng
    qasm_str = '''
OPENQASM 2.0;
include "qelib1.inc";
qreg a[1];
creg b[1];
if(b==1) x a;
measure a -> b;
if(b==1) x a;
measure a -> b;
'''
    qubits_map, bits_map = read_qasm_str(eng, qasm_str)
    assert {'a'} == set(qubits_map)
    assert len(qubits_map['a']) == 1
    assert {'b'} == set(bits_map)
    assert len(bits_map['b']) == 1
    assert len(filter_gates(dummy, AllocateQubitGate)) == 1
    assert len(filter_gates(dummy, XGate)) == 1
    assert len(filter_gates(dummy, MeasureGate)) == 2


@has_qiskit
def test_read_qasm_custom_gate(eng):
    qasm_str = '''
OPENQASM 2.0;
include "qelib1.inc";

qreg q[3];
creg c[3];
gate cH a,b {
h b;
sdg b;
cx a,b;
h b;
t b;
cx a,b;
t b;
h b;
s b;
x b;
s a;
 }
cH q[0],q[1];
'''

    qubits_map, bits_map = read_qasm_str(eng, qasm_str)
    assert {'q'} == set(qubits_map)
    assert len(qubits_map['q']) == 3
    assert {'c'} == set(bits_map)
    assert len(bits_map['c']) == 3
    assert len(filter_gates(eng.backend, AllocateQubitGate)) == 3
    assert len(filter_gates(eng.backend, XGate)) == 3
    assert len(filter_gates(eng.backend, HGate)) == 3
    assert len(filter_gates(eng.backend, TGate)) == 2
    assert len(filter_gates(eng.backend, SGate)) == 2
    # + 1 DaggeredGate for sdg


@has_qiskit
def test_read_qasm_opaque_gate(eng):
    qasm_str = '''
OPENQASM 2.0;
include "qelib1.inc";

opaque mygate q1, q2, q3;
qreg q[3];
creg c[3];

mygate q[0], q[1], q[2];
'''
    qubits_map, bits_map = read_qasm_str(eng, qasm_str)
    assert {'q'} == set(qubits_map)
    assert len(qubits_map['q']) == 3
    assert {'c'} == set(bits_map)
    assert len(bits_map['c']) == 3
    assert len(eng.backend.received_commands) == 3  # Only allocate gates


@has_qiskit
def test_read_qasm2_str(dummy_eng, iqft_example):
    dummy, eng = dummy_eng
    qubits_map, bits_map = read_qasm_str(eng, iqft_example)
    assert {'q'} == set(qubits_map)
    assert len(qubits_map['q']) == 4
    assert {'c'} == set(bits_map)
    assert len(bits_map['c']) == 4


@has_qiskit
def test_read_qasm2_file(dummy_eng, iqft_example):
    dummy, eng = dummy_eng

    with tempfile.NamedTemporaryFile(mode='w', delete=True if platform.system() != 'Windows' else False) as fd:
        fd.write(iqft_example)
        fd.flush()
        qubits_map, bits_map = read_qasm_file(eng, fd.name)

    assert {'q'} == set(qubits_map)
    assert len(qubits_map['q']) == 4
    assert {'c'} == set(bits_map)
    assert len(bits_map['c']) == 4
