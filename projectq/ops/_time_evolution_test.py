#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
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

"""Tests for projectq.ops._time_evolution."""
import cmath
import copy

import numpy
import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import QubitOperator, BasicGate, NotMergeable, Ph

from projectq.ops import _time_evolution as te


@pytest.mark.parametrize("coefficient", [0.5, numpy.float64(2.303)])
def test_time_evolution_init_int_time(coefficient):
    hamiltonian = coefficient * QubitOperator("X0 Z1")
    hamiltonian += QubitOperator("Z2", 0.5)
    gate1 = te.TimeEvolution(2, hamiltonian)
    assert gate1.hamiltonian.isclose(hamiltonian)
    assert gate1.time == 2


@pytest.mark.parametrize("coefficient", [0.5, numpy.float64(2.303)])
def test_init_float_time(coefficient):
    hamiltonian = coefficient * QubitOperator("X0 Z1")
    hamiltonian += QubitOperator("Z2", 0.5)
    gate2 = te.TimeEvolution(2.1, hamiltonian)
    assert gate2.hamiltonian.isclose(hamiltonian)
    assert gate2.time == pytest.approx(2.1)


def test_init_makes_copy():
    hamiltonian = QubitOperator("X0 Z1")
    gate = te.TimeEvolution(2.1, hamiltonian)
    hamiltonian = None
    assert gate.hamiltonian is not None


def test_init_bad_time():
    hamiltonian = QubitOperator("Z2", 0.5)
    with pytest.raises(TypeError):
        gate = te.TimeEvolution(1.5j, hamiltonian)


def test_init_bad_hamiltonian():
    with pytest.raises(TypeError):
        gate = te.TimeEvolution(2, "something else")


def test_init_not_hermitian():
    hamiltonian = QubitOperator("Z2", 1e-12j)
    with pytest.raises(te.NotHermitianOperatorError):
        gate = te.TimeEvolution(1, hamiltonian)


def test_init_cast_complex_to_float():
    hamiltonian = QubitOperator("Z2", 2+0j)
    gate = te.TimeEvolution(1, hamiltonian)
    assert isinstance(gate.hamiltonian.terms[((2, 'Z'),)], float)
    pytest.approx(gate.hamiltonian.terms[((2, 'Z'),)]) == 2.0


def test_init_negative_time():
    hamiltonian = QubitOperator("Z2", 2)
    gate = te.TimeEvolution(-1, hamiltonian)
    assert gate.time == -1


def test_get_inverse():
    hamiltonian = QubitOperator("Z2", 2)
    gate = te.TimeEvolution(2, hamiltonian)
    inverse = gate.get_inverse()
    assert gate.time == 2
    assert gate.hamiltonian.isclose(hamiltonian)
    assert inverse.time == -2
    assert inverse.hamiltonian.isclose(hamiltonian)


def test_get_merged_one_term():
    hamiltonian = QubitOperator("Z2", 2)
    gate = te.TimeEvolution(2, hamiltonian)
    hamiltonian2 = QubitOperator("Z2", 4)
    gate2 = te.TimeEvolution(5, hamiltonian2)
    merged = gate.get_merged(gate2)
    # This is not a requirement, the hamiltonian could also be the other
    # if we change implementation
    assert merged.hamiltonian.isclose(hamiltonian)
    assert merged.time == pytest.approx(12)


def test_get_merged_multiple_terms():
    hamiltonian = QubitOperator("Z2", 2)
    hamiltonian += QubitOperator("X3", 1)
    gate = te.TimeEvolution(2, hamiltonian)
    hamiltonian2 = QubitOperator("Z2", 4)
    hamiltonian2 += QubitOperator("X3", 2 + 1e-10)
    gate2 = te.TimeEvolution(5, hamiltonian2)
    merged = gate.get_merged(gate2)
    # This is not a requirement, the hamiltonian could also be the other
    # if we change implementation
    assert merged.hamiltonian.isclose(hamiltonian)
    assert merged.time == pytest.approx(12)


def test_get_merged_not_close_enough():
    hamiltonian = QubitOperator("Z2", 2)
    hamiltonian += QubitOperator("X3", 1)
    gate = te.TimeEvolution(2, hamiltonian)
    hamiltonian2 = QubitOperator("Z2", 4)
    hamiltonian2 += QubitOperator("X3", 2+1e-8)
    gate2 = te.TimeEvolution(5, hamiltonian2)
    with pytest.raises(NotMergeable):
        merged = gate.get_merged(gate2)


def test_get_merged_bad_gate():
    hamiltonian = QubitOperator("Z2", 2)
    gate = te.TimeEvolution(2, hamiltonian)
    other = BasicGate()
    with pytest.raises(NotMergeable):
        gate.get_merged(other)


def test_get_merged_different_hamiltonian():
    hamiltonian = QubitOperator("Z2", 2)
    gate = te.TimeEvolution(2, hamiltonian)
    hamiltonian2 = QubitOperator("Y2", 2)
    gate2 = te.TimeEvolution(2, hamiltonian2)
    with pytest.raises(NotMergeable):
        gate.get_merged(gate2)


def test_or_one_qubit():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qubit = eng.allocate_qubit()
    hamiltonian = QubitOperator("Z0", 2)
    te.TimeEvolution(2.1, hamiltonian) | qubit[0]
    te.TimeEvolution(3, hamiltonian) | (qubit[0],)
    eng.flush()
    cmd1 = saving_backend.received_commands[1]
    assert cmd1.gate.hamiltonian.isclose(hamiltonian)
    assert cmd1.gate.time == pytest.approx(2.1)
    assert len(cmd1.qubits) == 1 and len(cmd1.qubits[0]) == 1
    assert cmd1.qubits[0][0].id == qubit[0].id
    cmd2 = saving_backend.received_commands[2]
    assert cmd2.gate.hamiltonian.isclose(hamiltonian)
    assert cmd2.gate.time == pytest.approx(3)
    assert len(cmd2.qubits) == 1 and len(cmd2.qubits[0]) == 1
    assert cmd2.qubits[0][0].id == qubit[0].id


def test_or_one_qureg():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(5)
    hamiltonian = QubitOperator("X0 Z4", 2)
    te.TimeEvolution(2.1, hamiltonian) | qureg
    te.TimeEvolution(3, hamiltonian) | (qureg,)
    eng.flush()
    rescaled_h = QubitOperator("X0 Z1", 2)
    cmd1 = saving_backend.received_commands[5]
    assert cmd1.gate.hamiltonian.isclose(rescaled_h)
    assert cmd1.gate.time == pytest.approx(2.1)
    assert len(cmd1.qubits) == 1 and len(cmd1.qubits[0]) == 2
    assert cmd1.qubits[0][0].id == qureg[0].id
    assert cmd1.qubits[0][1].id == qureg[4].id
    cmd2 = saving_backend.received_commands[6]
    assert cmd2.gate.hamiltonian.isclose(rescaled_h)
    assert cmd2.gate.time == pytest.approx(3)
    assert len(cmd2.qubits) == 1 and len(cmd2.qubits[0]) == 2
    assert cmd2.qubits[0][0].id == qureg[0].id
    assert cmd2.qubits[0][1].id == qureg[4].id


def test_or_two_qubits_error():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(2)
    hamiltonian = QubitOperator("Z0", 2)
    with pytest.raises(TypeError):
        te.TimeEvolution(2.1, hamiltonian) | (qureg[0], qureg[1])


def test_or_two_quregs_error():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(2)
    qureg2 = eng.allocate_qureg(2)
    hamiltonian = QubitOperator("Z0", 2)
    with pytest.raises(TypeError):
        te.TimeEvolution(2.1, hamiltonian) | (qureg, qureg2)


def test_or_not_enough_qubits():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(2)
    hamiltonian = QubitOperator("Z0 X3", 2)
    with pytest.raises(ValueError):
        te.TimeEvolution(2.1, hamiltonian) | qureg


def test_or_multiple_terms():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(4)
    hamiltonian = QubitOperator("X0 Z3", 2)
    hamiltonian += QubitOperator("Y1", 0.5)
    te.TimeEvolution(2.1, hamiltonian) | qureg
    eng.flush()
    rescaled_h = QubitOperator("X0 Z2", 2)
    rescaled_h += QubitOperator("Y1", 0.5)
    cmd1 = saving_backend.received_commands[4]
    assert cmd1.gate.hamiltonian.isclose(rescaled_h)
    assert cmd1.gate.time == pytest.approx(2.1)
    assert len(cmd1.qubits) == 1 and len(cmd1.qubits[0]) == 3
    assert cmd1.qubits[0][0].id == qureg[0].id
    assert cmd1.qubits[0][1].id == qureg[1].id
    assert cmd1.qubits[0][2].id == qureg[3].id


def test_or_gate_not_mutated():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(4)
    hamiltonian = QubitOperator("X0 Z3", 2)
    hamiltonian += QubitOperator("Y1", 0.5)
    correct_h = copy.deepcopy(hamiltonian)
    gate = te.TimeEvolution(2.1, hamiltonian)
    gate | qureg
    eng.flush()
    assert gate.hamiltonian.isclose(correct_h)
    assert gate.time == pytest.approx(2.1)


def test_or_gate_identity():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    qureg = eng.allocate_qureg(4)
    hamiltonian = QubitOperator((), 3.4)
    correct_h = copy.deepcopy(hamiltonian)
    gate = te.TimeEvolution(2.1, hamiltonian)
    gate | qureg
    eng.flush()
    cmd = saving_backend.received_commands[4]
    assert isinstance(cmd.gate, Ph)
    assert cmd.gate == Ph(-3.4 * 2.1)
    correct = numpy.array([[cmath.exp(-1j * 3.4 * 2.1), 0],
                           [0, cmath.exp(-1j * 3.4 * 2.1)]])
    print(correct)
    print(cmd.gate.matrix)
    assert numpy.allclose(cmd.gate.matrix, correct)


def test_eq_not_implemented():
    hamiltonian = QubitOperator("X0 Z1")
    gate = te.TimeEvolution(2.1, hamiltonian)
    assert gate.__eq__("0") == NotImplemented


def test_ne_not_implemented():
    hamiltonian = QubitOperator("X0 Z1")
    gate = te.TimeEvolution(2.1, hamiltonian)
    assert gate.__ne__("0") == NotImplemented


def test_str():
    hamiltonian = QubitOperator("X0 Z1")
    hamiltonian += QubitOperator("Y1", 0.5)
    gate = te.TimeEvolution(2.1, hamiltonian)
    assert (str(gate) == "exp(-2.1j * (0.5 Y1 +\n1.0 X0 Z1))" or
            str(gate) == "exp(-2.1j * (1.0 X0 Z1 +\n0.5 Y1))")
