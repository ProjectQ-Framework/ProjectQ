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

"""Tests for projectq.cengines._basics.py."""

import types
import pytest
# try:
# 	import mock
# except ImportError:
# 	from unittest import mock

from projectq import MainEngine
from projectq.types import Qubit
from projectq.cengines import DummyEngine, InstructionFilter
from projectq.meta import DirtyQubitTag
from projectq.ops import (AllocateQubitGate, 
                          DeallocateQubitGate,
                          H, FastForwardingGate,
                          ClassicalInstructionGate)

from projectq.cengines import _basics


def test_basic_engine_init():
	eng = _basics.BasicEngine()
	assert eng.main_engine == None
	assert eng.next_engine == None
	assert eng.is_last_engine == False


def test_basic_engine_is_available():
	eng = _basics.BasicEngine()
	with pytest.raises(_basics.LastEngineException):
		eng.is_last_engine = True
		eng.is_available("FakeCommand")
	
	def filter(self, cmd):
		if cmd == "supported":
			return True
		return False
	
	filter_eng = InstructionFilter(filter)
	eng.next_engine = filter_eng
	eng.is_last_engine = False
	assert eng.is_available("supported")
	assert not eng.is_available("something else")


def test_basic_engine_allocate_and_deallocate_qubit_and_qureg():
	eng = _basics.BasicEngine()
	# custom receive function which checks that main_engine does not send
	# any allocate or deallocate gates
	cmd_sent_by_main_engine = []
	def receive(self, cmd_list):
		cmd_sent_by_main_engine.append(cmd_list)
	
	eng.receive = types.MethodType(receive, eng)
	# Create test engines:
	saving_backend = DummyEngine(save_commands=True)
	main_engine = MainEngine(backend=saving_backend,
		engine_list=[eng, DummyEngine()])
	# Allocate and deallocate qubits
	qubit = eng.allocate_qubit()
	# Try to allocate dirty qubit but it should give a non dirty qubit
	not_dirty_qubit = eng.allocate_qubit(dirty=True)
	# Allocate an actual dirty qubit
	def allow_dirty_qubits(self, meta_tag):
		if meta_tag == DirtyQubitTag:
			return True
		return False
	
	saving_backend.is_meta_tag_handler = types.MethodType(allow_dirty_qubits,
		saving_backend)
	dirty_qubit = eng.allocate_qubit(dirty=True)
	qureg = eng.allocate_qureg(2)
	# Test qubit allocation
	assert isinstance(qubit, list)
	assert len(qubit) == 1 and isinstance(qubit[0], Qubit)
	assert qubit[0] in main_engine.active_qubits
	assert id(qubit[0].engine) == id(eng)
	# Test non dirty qubit allocation
	assert isinstance(not_dirty_qubit, list)
	assert len(not_dirty_qubit) == 1 and isinstance(not_dirty_qubit[0], Qubit)
	assert not_dirty_qubit[0] in main_engine.active_qubits
	assert id(not_dirty_qubit[0].engine) == id(eng)
	# Test dirty_qubit allocation
	assert isinstance(dirty_qubit, list)
	assert len(dirty_qubit) == 1 and isinstance(dirty_qubit[0], Qubit)
	assert dirty_qubit[0] in main_engine.active_qubits
	assert dirty_qubit[0].id in main_engine.dirty_qubits
	assert id(dirty_qubit[0].engine) == id(eng)
	# Test qureg allocation
	assert isinstance(qureg, list)
	assert len(qureg) == 2
	for tmp_qubit in qureg:
		assert tmp_qubit in main_engine.active_qubits
		assert id(tmp_qubit.engine) == id(eng)
	# Test uniqueness of ids
	assert len(set([qubit[0].id, not_dirty_qubit[0].id, dirty_qubit[0].id, 
		qureg[0].id, qureg[1].id])) == 5
	# Test allocate gates were sent
	assert len(cmd_sent_by_main_engine) == 0
	assert len(saving_backend.received_commands) == 5
	for cmd in saving_backend.received_commands:
		assert cmd.gate == AllocateQubitGate()
	assert saving_backend.received_commands[2].tags == [DirtyQubitTag()]
	# Test deallocate gates were sent
	eng.deallocate_qubit(qubit[0])
	eng.deallocate_qubit(not_dirty_qubit[0])
	eng.deallocate_qubit(dirty_qubit[0])
	eng.deallocate_qubit(qureg[0])
	eng.deallocate_qubit(qureg[1])
	assert len(cmd_sent_by_main_engine) == 0
	assert len(saving_backend.received_commands) == 10
	for cmd in saving_backend.received_commands[5:]:
		assert cmd.gate == DeallocateQubitGate()
	assert saving_backend.received_commands[7].tags == [DirtyQubitTag()]


def test_basic_engine_is_meta_tag_supported():
	eng = _basics.BasicEngine()
	# BasicEngine needs receive function to function so let's add it:
	def receive(self, cmd_list):
		self.send(cmd_list)
	
	eng.receive = types.MethodType(receive, eng)
	backend = DummyEngine()
	engine0 = DummyEngine()
	engine1 = DummyEngine()
	engine2 = DummyEngine()
	
	def allow_dirty_qubits(self, meta_tag):
		if meta_tag == DirtyQubitTag:
			return True
		return False
	
	engine2.is_meta_tag_handler = types.MethodType(allow_dirty_qubits,
		engine2)
	main_engine = MainEngine(backend=backend,
		engine_list=[engine0, engine1, engine2])
	assert not main_engine.is_meta_tag_supported("NotSupported")
	assert main_engine.is_meta_tag_supported(DirtyQubitTag)


def test_forwarder_engine():
	backend = DummyEngine(save_commands=True)
	engine0 = DummyEngine()
	main_engine = MainEngine(backend=backend,
		engine_list = [engine0])
	def cmd_mod_fun(cmd):
		cmd.tags = "NewTag"
		return cmd
	
	forwarder_eng = _basics.ForwarderEngine(backend, cmd_mod_fun)
	engine0.next_engine = forwarder_eng
	forwarder_eng2 = _basics.ForwarderEngine(engine0)
	main_engine.next_engine = forwarder_eng2
	qubit = main_engine.allocate_qubit()
	H | qubit
	# Test if H gate was sent through forwarder_eng and tag was added
	received_commands = []
	# Remove Allocate and Deallocate gates
	for cmd in backend.received_commands:
		if not (isinstance(cmd.gate, FastForwardingGate) or 
	            isinstance(cmd.gate, ClassicalInstructionGate)):
			received_commands.append(cmd)
	for cmd in received_commands:
		print(cmd)
	assert len(received_commands) == 1
	assert received_commands[0].gate == H
	assert received_commands[0].tags == "NewTag"
