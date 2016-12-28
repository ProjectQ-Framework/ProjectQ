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

"""Tests for projectq.ops._gates."""

import cmath
import math
import numpy as np
import pytest

from projectq.types import Qubit, Qureg
from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import (T, Y, NotInvertible, Entangle, Rx, 
                          FastForwardingGate, Command,
                          ClassicalInstructionGate)

from projectq.ops import _metagates


def test_daggered_gate_init():
	# Choose gate which does not have an inverse gate:
	not_invertible_gate = T
	with pytest.raises(NotInvertible):
		not_invertible_gate.get_inverse()
	# Choose gate which does have an inverse defined:
	invertible_gate = Y
	assert invertible_gate.get_inverse() == Y
	# Test init and matrix
	dagger_inv = _metagates.DaggeredGate(not_invertible_gate)
	assert dagger_inv._gate == not_invertible_gate
	assert np.array_equal(dagger_inv.matrix, 
		np.matrix([[1, 0], [0, cmath.exp(-1j * cmath.pi / 4)]]))
	inv = _metagates.DaggeredGate(invertible_gate)
	assert inv._gate == invertible_gate
	assert np.array_equal(inv.matrix, np.matrix([[0, -1j], [1j, 0]]))
	# Test matrix 
	no_matrix_gate = Entangle
	with pytest.raises(AttributeError):
		no_matrix_gate.matrix
	inv_no_matrix_gate = _metagates.DaggeredGate(no_matrix_gate)
	with pytest.raises(AttributeError):
		inv_no_matrix_gate.matrix


def test_daggered_gate_str():
	daggered_gate = _metagates.DaggeredGate(Y)
	assert str(daggered_gate) == str(Y) + "^\dagger"


def test_daggered_gate_get_inverse():
	daggered_gate = _metagates.DaggeredGate(Y)
	assert daggered_gate.get_inverse() == Y


def test_daggered_gate_comparison():
	daggered_gate = _metagates.DaggeredGate(Y)
	daggered_gate2 = _metagates.DaggeredGate(Y)
	assert daggered_gate == daggered_gate2


def test_get_inverse():
	# Choose gate which does not have an inverse gate:
	not_invertible_gate = T
	with pytest.raises(NotInvertible):
		not_invertible_gate.get_inverse()
	# Choose gate which does have an inverse defined:
	invertible_gate = Y
	assert invertible_gate.get_inverse() == Y
	# Check get_inverse(gate)
	inv = _metagates.get_inverse(not_invertible_gate)
	assert (isinstance(inv, _metagates.DaggeredGate) and 
	        inv._gate == not_invertible_gate)
	inv2 = _metagates.get_inverse(invertible_gate)
	assert inv2 == Y


def test_controlled_gate_init():
	one_control = _metagates.ControlledGate(Y,1)
	two_control = _metagates.ControlledGate(Y,2)
	three_control = _metagates.ControlledGate(one_control, 2)
	assert one_control._gate == Y
	assert one_control._n == 1
	assert two_control._gate == Y
	assert two_control._n == 2
	assert three_control._gate == Y
	assert three_control._n == 3


def test_controlled_gate_str():
	one_control = _metagates.ControlledGate(Y,2)
	assert str(one_control) == "CC" + str(Y)


def test_controlled_gate_get_inverse():
	one_control = _metagates.ControlledGate(Rx(0.5),1)
	expected = _metagates.ControlledGate(Rx(-0.5 + 4 * math.pi),1)
	assert one_control.get_inverse() == expected


def test_controlled_gate_or():
	saving_backend = DummyEngine(save_commands = True)
	main_engine = MainEngine(backend = saving_backend,
	                         engine_list = [DummyEngine()])
	gate = Rx(0.6)
	qubit0 = Qubit(main_engine, 0)
	qubit1 = Qubit(main_engine, 1)
	qubit2 = Qubit(main_engine, 2)
	qubit3 = Qubit(main_engine, 3)
	expected_cmd = Command(main_engine, gate, ([qubit3],))
	expected_cmd.add_control_qubits([qubit0, qubit1, qubit2])
	received_commands = []
	# Option 1:
	_metagates.ControlledGate(gate, 3) | ([qubit1], [qubit0], [qubit2], [qubit3])
	# Option 2:
	_metagates.ControlledGate(gate, 3) | (qubit1, qubit0, qubit2, qubit3)
	# Option 3:
	_metagates.ControlledGate(gate, 3) | ([qubit1, qubit0], qubit2, qubit3)
	# Option 4:
	_metagates.ControlledGate(gate, 3) | (qubit1, [qubit0, qubit2], qubit3)
	# Wrong option 5:
	with pytest.raises(_metagates.ControlQubitError):
		_metagates.ControlledGate(gate, 3) | (qubit1, [qubit0, qubit2, qubit3])
	# Remove Allocate and Deallocate gates
	for cmd in saving_backend.received_commands:
		if not (isinstance(cmd.gate, FastForwardingGate) or 
	            isinstance(cmd.gate, ClassicalInstructionGate)):
			received_commands.append(cmd)
	assert len(received_commands) == 4
	for cmd in received_commands:
		assert cmd == expected_cmd


def test_controlled_gate_comparison():
	gate1 = _metagates.ControlledGate(Y,1)
	gate2 = _metagates.ControlledGate(Y,1)
	gate3 = _metagates.ControlledGate(T,1)
	gate4 = _metagates.ControlledGate(Y,2)
	assert gate1 == gate2
	assert not gate1 == gate3
	assert gate1 != gate4


def test_c():
	expected = _metagates.ControlledGate(Y,2)
	assert _metagates.C(Y, 2) == expected


def test_tensor_init():
	gate = _metagates.Tensor(Y)
	assert gate._gate == Y


def test_tensor_str():
	gate = _metagates.Tensor(Y)
	assert str(gate) == "Tensor(" + str(Y) + ")"


def test_tensor_get_inverse():
	gate = _metagates.Tensor(Rx(0.6))
	inverse = gate.get_inverse()
	assert isinstance(inverse, _metagates.Tensor)
	assert inverse._gate == Rx(-0.6 + 4 * math.pi)


def test_tensor_comparison():
	gate1 = _metagates.Tensor(Rx(0.6))
	gate2 = _metagates.Tensor(Rx(0.6 + 4 * math.pi))
	assert gate1 == gate2
	assert gate1 != Rx(0.6)


def test_tensor_or():
	saving_backend = DummyEngine(save_commands = True)
	main_engine = MainEngine(backend = saving_backend,
	                         engine_list = [DummyEngine()])
	gate = Rx(0.6)
	qubit0 = Qubit(main_engine, 0)
	qubit1 = Qubit(main_engine, 1)
	qubit2 = Qubit(main_engine, 2)
	# Option 1:
	_metagates.Tensor(gate) | ([qubit0, qubit1, qubit2],)
	# Option 2:
	_metagates.Tensor(gate) | [qubit0, qubit1, qubit2]
	received_commands = []
	# Remove Allocate and Deallocate gates
	for cmd in saving_backend.received_commands:
		if not (isinstance(cmd.gate, FastForwardingGate) or 
	            isinstance(cmd.gate, ClassicalInstructionGate)):
			received_commands.append(cmd)
	# Check results
	assert len(received_commands) == 6
	qubit_ids = []
	for cmd in received_commands:
		assert len(cmd.qubits) == 1
		assert cmd.gate == gate
		qubit_ids.append(cmd.qubits[0][0].id)
	assert sorted(qubit_ids) == [0,0,1,1,2,2]
