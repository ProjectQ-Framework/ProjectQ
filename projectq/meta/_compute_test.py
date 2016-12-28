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

"""Tests for projectq.meta._compute.py"""

import pytest
import types
import weakref

from projectq import MainEngine
from projectq.cengines import DummyEngine, CompareEngine
from projectq.ops import H, Rx, Ry, Deallocate, Allocate, CNOT, NOT, FlushGate
from projectq.types import WeakQubitRef
from projectq.meta import DirtyQubitTag

from projectq.meta import _compute


def test_compute_tag():
	tag0 = _compute.ComputeTag()
	tag1 = _compute.ComputeTag()
	
	class MyTag(object):
		pass
	
	assert not tag0 == MyTag()
	assert not tag0 != tag1
	assert tag0 == tag1


def test_uncompute_tag():
	tag0 = _compute.UncomputeTag()
	tag1 = _compute.UncomputeTag()
	
	class MyTag(object):
		pass
	
	assert not tag0 == MyTag()
	assert not tag0 != tag1
	assert tag0 == tag1


def test_compute_engine():
	backend = DummyEngine(save_commands=True)
	compute_engine = _compute.ComputeEngine()
	eng = MainEngine(backend=backend, engine_list=[compute_engine])
	ancilla = eng.allocate_qubit() # Ancilla
	H | ancilla
	Rx(0.6) | ancilla
	ancilla[0].__del__()
	# Test that adding later a new tag to one of the previous commands
	# does not add this tags to cmds saved in compute_engine because
	# this one does need to make a deepcopy and not store a reference.
	assert backend.received_commands[1].gate == H
	backend.received_commands[1].tags.append("TagAddedLater")
	assert backend.received_commands[1].tags[-1] == "TagAddedLater"
	compute_engine.end_compute()
	new_qubit = eng.allocate_qubit()
	Ry(0.5) | new_qubit
	compute_engine.run_uncompute()
	eng.flush()
	assert backend.received_commands[0].gate == Allocate
	assert backend.received_commands[0].tags == [_compute.ComputeTag()]
	assert backend.received_commands[1].gate == H
	assert backend.received_commands[1].tags == [_compute.ComputeTag(),
	                                             "TagAddedLater"]
	assert backend.received_commands[2].gate == Rx(0.6)
	assert backend.received_commands[2].tags == [_compute.ComputeTag()]
	assert backend.received_commands[3].gate == Deallocate
	assert backend.received_commands[3].tags == [_compute.ComputeTag()]
	assert backend.received_commands[4].gate == Allocate
	assert backend.received_commands[4].tags == []
	assert backend.received_commands[5].gate == Ry(0.5)
	assert backend.received_commands[5].tags == []
	assert backend.received_commands[6].gate == Allocate
	assert backend.received_commands[6].tags == [_compute.UncomputeTag()]
	assert backend.received_commands[7].gate == Rx(-0.6)
	assert backend.received_commands[7].tags == [_compute.UncomputeTag()]
	assert backend.received_commands[8].gate == H
	assert backend.received_commands[8].tags == [_compute.UncomputeTag()]
	assert backend.received_commands[9].gate == Deallocate
	assert backend.received_commands[9].tags == [_compute.UncomputeTag()]


def test_uncompute_engine():
	backend = DummyEngine(save_commands=True)
	uncompute_engine = _compute.UncomputeEngine()
	eng = MainEngine(backend=backend, engine_list=[uncompute_engine])
	qubit = eng.allocate_qubit()
	H | qubit
	assert backend.received_commands[0].gate == Allocate
	assert backend.received_commands[0].tags == [_compute.UncomputeTag()]
	assert backend.received_commands[1].gate == H
	assert backend.received_commands[1].tags == [_compute.UncomputeTag()]

def test_outside_qubit_deallocated_in_compute():
	# Test that there is an error if a qubit is deallocated which has
	# not been allocated within the with Compute(eng) context
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	qubit = eng.allocate_qubit()
	with pytest.raises(_compute.QubitManagementError):
		with _compute.Compute(eng):
			qubit[0].__del__()


def test_deallocation_using_custom_uncompute():
	# Test that qubits allocated within Compute and Uncompute
	# section have all been deallocated
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	# Allowed versions:
	with _compute.Compute(eng):
		ancilla = eng.allocate_qubit()
		ancilla[0].__del__()
	with _compute.CustomUncompute(eng):
		ancilla2 = eng.allocate_qubit()
		ancilla2[0].__del__()
	with _compute.Compute(eng):
		ancilla3 = eng.allocate_qubit()
	with _compute.CustomUncompute(eng):
		ancilla3[0].__del__()


def test_deallocation_using_custom_uncompute2():
	# Test not allowed version:
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	with _compute.Compute(eng):
		ancilla = eng.allocate_qubit()
	with pytest.raises(_compute.QubitManagementError):
		with _compute.CustomUncompute(eng):
			pass
	H | ancilla


def test_deallocation_using_custom_uncompute3():
	# Test not allowed version:
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	with _compute.Compute(eng):
		pass
	with pytest.raises(_compute.QubitManagementError):
		with _compute.CustomUncompute(eng):
			ancilla = eng.allocate_qubit()
	H | ancilla


def test_automatic_deallocation_of_qubit_in_uncompute():
	# Test that automatic uncomputation deallocates qubit
	# which was created during compute context.
	backend = DummyEngine(save_commands=True)
	eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
	with _compute.Compute(eng):
		ancilla = eng.allocate_qubit()
		assert ancilla[0].id != -1
		Rx(0.6) | ancilla
	# Test that ancilla qubit has been register in MainEngine.active_qubits
	assert ancilla[0] in eng.active_qubits
	_compute.Uncompute(eng)
	# Test that ancilla id has been set to -1
	assert ancilla[0].id == -1
	# Test that ancilla is not anymore in active qubits
	assert not ancilla[0] in eng.active_qubits
	assert backend.received_commands[1].gate == Rx(0.6)
	assert backend.received_commands[2].gate == Rx(-0.6)

 
def test_compute_uncompute_no_additional_qubits():
	# No ancilla qubit created in compute section
	backend0 = DummyEngine(save_commands=True)
	compare_engine0 = CompareEngine()
	eng0 = MainEngine(backend=backend0, engine_list=[compare_engine0])
	qubit = eng0.allocate_qubit()
	with _compute.Compute(eng0):
		Rx(0.5) | qubit
	H | qubit
	_compute.Uncompute(eng0)
	eng0.flush(deallocate_qubits=True)
	assert backend0.received_commands[0].gate == Allocate
	assert backend0.received_commands[1].gate == Rx(0.5)
	assert backend0.received_commands[2].gate == H
	assert backend0.received_commands[3].gate == Rx(-0.5)
	assert backend0.received_commands[4].gate == Deallocate
	assert backend0.received_commands[0].tags == []
	assert backend0.received_commands[1].tags == [_compute.ComputeTag()]
	assert backend0.received_commands[2].tags == []
	assert backend0.received_commands[3].tags == [_compute.UncomputeTag()]
	assert backend0.received_commands[4].tags == []
	# Same using CustomUncompute and test using CompareEngine
	backend1 = DummyEngine(save_commands = True)
	compare_engine1 = CompareEngine()
	eng1 = MainEngine(backend=backend1, engine_list=[compare_engine1])
	qubit = eng1.allocate_qubit()
	with _compute.Compute(eng1):
		Rx(0.5) | qubit
	H | qubit
	with _compute.CustomUncompute(eng1):
		Rx(-0.5) | qubit
	eng1.flush(deallocate_qubits=True)
	assert compare_engine0 == compare_engine1


def test_compute_uncompute_with_statement():
	# Allocating and deallocating qubit within Compute
	backend = DummyEngine(save_commands=True)
	compare_engine0 = CompareEngine()
	# Allow dirty qubits
	dummy_cengine = DummyEngine()
	def allow_dirty_qubits(self, meta_tag):
		return meta_tag == DirtyQubitTag
	dummy_cengine.is_meta_tag_handler = types.MethodType(allow_dirty_qubits,
	                                                     dummy_cengine)
	eng = MainEngine(backend=backend, 
	                 engine_list=[compare_engine0, dummy_cengine])
	qubit = eng.allocate_qubit()
	with _compute.Compute(eng):
		Rx(0.9) | qubit
		ancilla = eng.allocate_qubit(dirty=True)
		ancilla2 = eng.allocate_qubit() # will be deallocated in Uncompute section
		# Test that ancilla is registered in MainEngine.active_qubits:
		assert ancilla[0] in eng.active_qubits
		H | qubit
		Rx(0.5) | ancilla
		CNOT | (ancilla, qubit)
		Rx(0.7) | qubit
		Rx(-0.5) | ancilla
		ancilla[0].__del__()
	H | qubit
	_compute.Uncompute(eng)
	eng.flush(deallocate_qubits=True)
	assert len(backend.received_commands) == 22
	# Test each Command has correct gate
	assert backend.received_commands[0].gate == Allocate
	assert backend.received_commands[1].gate == Rx(0.9)
	assert backend.received_commands[2].gate == Allocate
	assert backend.received_commands[3].gate == Allocate
	assert backend.received_commands[4].gate == H
	assert backend.received_commands[5].gate == Rx(0.5)
	assert backend.received_commands[6].gate == NOT
	assert backend.received_commands[7].gate == Rx(0.7)
	assert backend.received_commands[8].gate == Rx(-0.5)
	assert backend.received_commands[9].gate == Deallocate
	assert backend.received_commands[10].gate == H
	assert backend.received_commands[11].gate == Allocate
	assert backend.received_commands[12].gate == Rx(0.5)
	assert backend.received_commands[13].gate == Rx(-0.7)
	assert backend.received_commands[14].gate == NOT
	assert backend.received_commands[15].gate == Rx(-0.5)
	assert backend.received_commands[16].gate == H
	assert backend.received_commands[17].gate == Deallocate	
	assert backend.received_commands[18].gate == Deallocate
	assert backend.received_commands[19].gate == Rx(-0.9)
	assert backend.received_commands[20].gate == Deallocate
	assert backend.received_commands[21].gate == FlushGate()
	# Test that each command has correct tags
	assert backend.received_commands[0].tags == []
	assert backend.received_commands[1].tags == [_compute.ComputeTag()]	
	assert backend.received_commands[2].tags == [DirtyQubitTag(),
	                                             _compute.ComputeTag()]
	for cmd in backend.received_commands[3:9]:
		assert cmd.tags == [_compute.ComputeTag()]
	assert backend.received_commands[9].tags == [DirtyQubitTag(),
	                                             _compute.ComputeTag()]
	assert backend.received_commands[10].tags == []
	assert backend.received_commands[11].tags == [DirtyQubitTag(),
	                                              _compute.UncomputeTag()]
	for cmd in backend.received_commands[12:18]:
		assert cmd.tags == [_compute.UncomputeTag()]
	assert backend.received_commands[18].tags == [DirtyQubitTag(),
	                                              _compute.UncomputeTag()]
	assert backend.received_commands[19].tags == [_compute.UncomputeTag()]
	assert backend.received_commands[20].tags == []
	assert backend.received_commands[21].tags == []
	# Test that each command has correct qubits
	# Note that ancilla qubit in compute should be
	# different from ancilla qubit in uncompute section
	qubit_id = backend.received_commands[0].qubits[0][0].id
	ancilla_compt_id = backend.received_commands[2].qubits[0][0].id
	ancilla_uncompt_id = backend.received_commands[11].qubits[0][0].id
	ancilla2_id = backend.received_commands[3].qubits[0][0].id
	assert backend.received_commands[1].qubits[0][0].id == qubit_id
	assert backend.received_commands[4].qubits[0][0].id == qubit_id
	assert backend.received_commands[5].qubits[0][0].id == ancilla_compt_id
	assert backend.received_commands[6].qubits[0][0].id == qubit_id
	assert backend.received_commands[6].control_qubits[0].id == ancilla_compt_id
	assert backend.received_commands[7].qubits[0][0].id == qubit_id
	assert backend.received_commands[8].qubits[0][0].id == ancilla_compt_id
	assert backend.received_commands[9].qubits[0][0].id == ancilla_compt_id
	assert backend.received_commands[10].qubits[0][0].id == qubit_id
	assert backend.received_commands[12].qubits[0][0].id == ancilla_uncompt_id
	assert backend.received_commands[13].qubits[0][0].id == qubit_id
	assert backend.received_commands[14].qubits[0][0].id == qubit_id
	assert (backend.received_commands[14].control_qubits[0].id
	        == ancilla_uncompt_id)
	assert backend.received_commands[15].qubits[0][0].id == ancilla_uncompt_id
	assert backend.received_commands[16].qubits[0][0].id == qubit_id
	assert backend.received_commands[17].qubits[0][0].id == ancilla2_id
	assert backend.received_commands[18].qubits[0][0].id == ancilla_uncompt_id
	assert backend.received_commands[19].qubits[0][0].id == qubit_id
	assert backend.received_commands[20].qubits[0][0].id == qubit_id
	# Test that ancilla qubits should have seperate ids
	assert ancilla_uncompt_id != ancilla_compt_id

	# Do the same thing with CustomUncompute and compare using the CompareEngine:
	backend1 = DummyEngine(save_commands=True)
	compare_engine1 = CompareEngine()
	# Allow dirty qubits
	dummy_cengine1 = DummyEngine()
	def allow_dirty_qubits(self, meta_tag):
		return meta_tag == DirtyQubitTag
	dummy_cengine1.is_meta_tag_handler = types.MethodType(allow_dirty_qubits,
	                                                      dummy_cengine1)
	eng1 = MainEngine(backend=backend1, 
	                 engine_list=[compare_engine1, dummy_cengine1])
	qubit = eng1.allocate_qubit()
	with _compute.Compute(eng1):
		Rx(0.9) | qubit
		ancilla = eng1.allocate_qubit(dirty=True)
		ancilla2 = eng1.allocate_qubit() # will be deallocated in Uncompute section
		# Test that ancilla is registered in MainEngine.active_qubits:
		assert ancilla[0] in eng1.active_qubits
		H | qubit
		Rx(0.5) | ancilla
		CNOT | (ancilla, qubit)
		Rx(0.7) | qubit
		Rx(-0.5) | ancilla
		ancilla[0].__del__()
	H | qubit
	with _compute.CustomUncompute(eng1):
		ancilla = eng1.allocate_qubit(dirty=True)
		Rx(0.5) | ancilla
		Rx(-0.7) | qubit
		CNOT | (ancilla, qubit)
		Rx(-0.5) | ancilla
		H | qubit
		assert ancilla[0] in eng1.active_qubits
		ancilla2[0].__del__()
		ancilla[0].__del__()
		Rx(-0.9) | qubit
	eng1.flush(deallocate_qubits=True)
	assert compare_engine0 == compare_engine1


def test_exception_if_no_compute_but_uncompute():
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	with pytest.raises(_compute.NoComputeSectionError):
		with _compute.CustomUncompute(eng):
			pass


def test_exception_if_no_compute_but_uncompute2():
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	with pytest.raises(_compute.NoComputeSectionError):
		_compute.Uncompute(eng)


def test_qubit_management_error():
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	with _compute.Compute(eng):
		ancilla = eng.allocate_qubit()
	eng.active_qubits = weakref.WeakSet()
	with pytest.raises(_compute.QubitManagementError):
		_compute.Uncompute(eng)


def test_qubit_management_error2():
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	with _compute.Compute(eng):
		ancilla = eng.allocate_qubit()
		local_ancilla = eng.allocate_qubit()
		local_ancilla[0].__del__()
	eng.active_qubits = weakref.WeakSet()
	with pytest.raises(_compute.QubitManagementError):
		_compute.Uncompute(eng)
