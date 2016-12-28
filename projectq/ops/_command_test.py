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

"""Tests for projectq.ops._command."""

from copy import deepcopy
import math
import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.meta import ComputeTag
from projectq.ops import BasicGate, Rx, NotMergeable
from projectq.types import Qubit, Qureg, WeakQubitRef

from projectq.ops import _command


@pytest.fixture
def main_engine():
	return MainEngine(backend = DummyEngine(), engine_list = [DummyEngine()])


def test_command_init(main_engine):
	qureg0 = Qureg([Qubit(main_engine, 0)])
	qureg1 = Qureg([Qubit(main_engine, 1)])
	qureg2 = Qureg([Qubit(main_engine, 2)])
	qureg3 = Qureg([Qubit(main_engine, 3)])
	qureg4 = Qureg([Qubit(main_engine, 4)])
	gate = BasicGate()
	cmd = _command.Command(main_engine, gate, (qureg0, qureg1, qureg2))
	assert cmd.gate == gate
	assert cmd.tags == []
	expected_tuple = (qureg0, qureg1, qureg2)
	for cmd_qureg, expected_qureg in zip(cmd.qubits, expected_tuple):
		assert cmd_qureg[0].id == expected_qureg[0].id
		# Testing that Qubits are now WeakQubitRef objects
		assert type(cmd_qureg[0]) == WeakQubitRef
	assert cmd._engine == main_engine
	# Test that quregs are ordered if gate has interchangeable qubits:
	symmetric_gate = BasicGate()
	symmetric_gate.interchangeable_qubit_indices=[[0,1]]
	symmetric_cmd = _command.Command(main_engine, symmetric_gate, 
		(qureg2, qureg1, qureg0))
	assert cmd.gate == gate
	assert cmd.tags == []
	expected_ordered_tuple = (qureg1, qureg2, qureg0)
	for cmd_qureg, expected_qureg in zip(symmetric_cmd.qubits, 
		expected_ordered_tuple):
		assert cmd_qureg[0].id == expected_qureg[0].id
	assert symmetric_cmd._engine == main_engine


def test_command_deepcopy(main_engine):
	qureg0 = Qureg([Qubit(main_engine, 0)])
	qureg1 = Qureg([Qubit(main_engine, 1)])
	gate = BasicGate()
	cmd = _command.Command(main_engine, gate, (qureg0,))
	cmd.add_control_qubits(qureg1)
	cmd.tags.append("MyTestTag")
	copied_cmd = deepcopy(cmd)
	# Test that deepcopy gives same cmd
	assert copied_cmd.gate == gate
	assert copied_cmd.tags == ["MyTestTag"]
	assert len(copied_cmd.qubits) == 1
	assert copied_cmd.qubits[0][0].id == qureg0[0].id 
	assert len(copied_cmd.control_qubits) == 1
	assert copied_cmd.control_qubits[0].id == qureg1[0].id
	# Engine should not be deepcopied but a reference:
	assert id(copied_cmd.engine) == id(main_engine) 
	# Test that deepcopy is actually a deepcopy
	cmd.tags = ["ChangedTag"]
	assert copied_cmd.tags == ["MyTestTag"]
	cmd.control_qubits[0].id == 10
	assert copied_cmd.control_qubits[0].id == qureg1[0].id
	cmd.gate = "ChangedGate"
	assert copied_cmd.gate == gate


def test_command_get_inverse(main_engine):
	qubit = main_engine.allocate_qubit()
	ctrl_qubit = main_engine.allocate_qubit()
	cmd = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd.add_control_qubits(ctrl_qubit)
	cmd.tags = [ComputeTag()]
	inverse_cmd = cmd.get_inverse()
	assert inverse_cmd.gate == Rx(-0.5 + 4 * math.pi)
	assert len(cmd.qubits) == len(inverse_cmd.qubits)
	assert cmd.qubits[0][0].id == inverse_cmd.qubits[0][0].id
	assert id(cmd.qubits[0][0]) != id(inverse_cmd.qubits[0][0])
	assert len(cmd.control_qubits) == len(inverse_cmd.control_qubits)
	assert cmd.control_qubits[0].id == inverse_cmd.control_qubits[0].id
	assert id(cmd.control_qubits[0]) != id(inverse_cmd.control_qubits[0])
	assert cmd.tags == inverse_cmd.tags
	assert id(cmd.tags[0]) != id(inverse_cmd.tags[0])
	assert id(cmd.engine) == id(inverse_cmd.engine)


def test_command_get_merged(main_engine):
	qubit = main_engine.allocate_qubit()
	ctrl_qubit = main_engine.allocate_qubit()
	cmd = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd.tags = ["TestTag"]
	cmd.add_control_qubits(ctrl_qubit)
	# Merge two commands
	cmd2 = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd2.add_control_qubits(ctrl_qubit)
	cmd2.tags = ["TestTag"]
	merged_cmd = cmd.get_merged(cmd2)
	expected_cmd = _command.Command(main_engine, Rx(1.0), (qubit,))
	expected_cmd.add_control_qubits(ctrl_qubit)
	expected_cmd.tags = ["TestTag"]
	# Don't merge commands as different control qubits
	cmd3 = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd3.tags = ["TestTag"]
	with pytest.raises(NotMergeable):
		cmd.get_merged(cmd3)
	# Don't merge commands as different tags
	cmd4 = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd4.add_control_qubits(ctrl_qubit)
	with pytest.raises(NotMergeable):
		cmd.get_merged(cmd4)


def test_command_order_qubits(main_engine):
	qubit0 = Qureg([Qubit(main_engine, 0)])
	qubit1 = Qureg([Qubit(main_engine, 1)])
	qubit2 = Qureg([Qubit(main_engine, 2)])
	qubit3 = Qureg([Qubit(main_engine, 3)])
	qubit4 = Qureg([Qubit(main_engine, 4)])
	qubit5 = Qureg([Qubit(main_engine, 5)])
	gate = BasicGate()
	gate.interchangeable_qubit_indices=[[0,4,5],[1,2]]
	input_tuple = (qubit4, qubit5, qubit3, qubit2, qubit1, qubit0)
	expected_tuple = (qubit0, qubit3, qubit5, qubit2, qubit1, qubit4)
	cmd = _command.Command(main_engine, gate, input_tuple)
	for ordered_qubit, expected_qubit in zip(cmd.qubits, expected_tuple):
		assert ordered_qubit[0].id == expected_qubit[0].id

def test_command_interchangeable_qubit_indices(main_engine):
	gate = BasicGate()
	gate.interchangeable_qubit_indices = [[0,4,5],[1,2]]
	qubit0 = Qureg([Qubit(main_engine, 0)])
	qubit1 = Qureg([Qubit(main_engine, 1)])
	qubit2 = Qureg([Qubit(main_engine, 2)])
	qubit3 = Qureg([Qubit(main_engine, 3)])
	qubit4 = Qureg([Qubit(main_engine, 4)])
	qubit5 = Qureg([Qubit(main_engine, 5)])
	input_tuple = (qubit4, qubit5, qubit3, qubit2, qubit1, qubit0)
	cmd = _command.Command(main_engine, gate, input_tuple)
	assert (cmd.interchangeable_qubit_indices == [[0,4,5],[1,2]] or
		cmd.interchangeable_qubit_indices == [[1,2],[0,4,5]])


def test_commmand_add_control_qubits(main_engine):
	qubit0 = Qureg([Qubit(main_engine, 0)])
	qubit1 = Qureg([Qubit(main_engine, 1)])
	qubit2 = Qureg([Qubit(main_engine, 2)])
	cmd = _command.Command(main_engine, Rx(0.5), (qubit0,))
	cmd.add_control_qubits(qubit2 + qubit1)
	assert cmd.control_qubits[0].id == 1
	assert cmd.control_qubits[1].id == 2


def test_command_all_qubits(main_engine):
	qubit0 = Qureg([Qubit(main_engine, 0)])
	qubit1 = Qureg([Qubit(main_engine, 1)])
	cmd = _command.Command(main_engine, Rx(0.5), (qubit0,))
	cmd.add_control_qubits(qubit1)
	all_qubits = cmd.all_qubits
	assert all_qubits[0][0].id == 1
	assert all_qubits[1][0].id == 0

def test_command_engine(main_engine):
	qubit0 = Qureg([Qubit("fake_engine", 0)])
	qubit1 = Qureg([Qubit("fake_engine", 1)])
	cmd = _command.Command("fake_engine", Rx(0.5), (qubit0,))
	cmd.add_control_qubits(qubit1)
	assert cmd.engine == "fake_engine"
	cmd.engine = main_engine
	assert id(cmd.engine) == id(main_engine)
	assert id(cmd.control_qubits[0].engine) == id(main_engine)
	assert id(cmd.qubits[0][0].engine) == id(main_engine)

def test_command_comparison(main_engine):
	qubit = Qureg([Qubit(main_engine, 0)])
	ctrl_qubit = Qureg([Qubit(main_engine, 1)])
	cmd1 = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd1.tags = ["TestTag"]
	cmd1.add_control_qubits(ctrl_qubit)
	# Test equality
	cmd2 = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd2.tags = ["TestTag"]
	cmd2.add_control_qubits(ctrl_qubit)
	assert cmd2 == cmd1
	# Test not equal because of tags
	cmd3 = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd3.tags = ["TestTag", "AdditionalTag"]
	cmd3.add_control_qubits(ctrl_qubit)
	assert not cmd3 == cmd1
	# Test not equal because of control qubit
	cmd4 = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd4.tags = ["TestTag"]
	assert not cmd4 == cmd1
	# Test not equal because of qubit
	qubit2 = Qureg([Qubit(main_engine, 2)])
	cmd5 = _command.Command(main_engine, Rx(0.5), (qubit2,))
	cmd5.tags = ["TestTag"]
	cmd5.add_control_qubits(ctrl_qubit)
	assert cmd5 != cmd1
	# Test not equal because of engine
	cmd6 = _command.Command("FakeEngine", Rx(0.5), (qubit,))
	cmd6.tags = ["TestTag"]
	cmd6.add_control_qubits(ctrl_qubit)
	assert cmd6 != cmd1

def test_command_str():
	qubit = Qureg([Qubit(main_engine, 0)])
	ctrl_qubit = Qureg([Qubit(main_engine, 1)])
	cmd = _command.Command(main_engine, Rx(0.5), (qubit,))
	cmd.tags = ["TestTag"]
	cmd.add_control_qubits(ctrl_qubit)
	assert str(cmd) == "CRx(0.5) | ( Qubit[1], Qubit[0] )"
	cmd2 = _command.Command(main_engine, Rx(0.5), (qubit,))
	assert str(cmd2) == "Rx(0.5) | Qubit[0]"
