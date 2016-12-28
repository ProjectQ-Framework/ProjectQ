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

"""
Tests for projectq.backends._sim._simulator.py, using both the Python
and the C++ simulator as backends.
"""

import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import (H,
                          X,
                          CNOT,
                          Toffoli,
                          Measure,
                          BasicGate,
                          BasicMathGate)
from projectq.meta import Control

from projectq.backends import Simulator


@pytest.fixture(params=["cpp_simulator","py_simulator"])
def sim(request):
	if request.param == "cpp_simulator":
		from projectq.backends._sim._cppsim import Simulator as CppSim
		sim = Simulator(gate_fusion=True)
		sim._simulator = CppSim(1)
		# If an ImportError occurs, the C++ simulator was either not installed
		# or compiled for a different Python version.
		return sim
	if request.param == "py_simulator":
		from projectq.backends._sim._pysim import Simulator as PySim
		sim = Simulator()
		sim._simulator = PySim(1)
		return sim


class Mock1QubitGate(BasicGate):
		def __init__(self):
			BasicGate.__init__(self)
			self.cnt = 0
		
		@property
		def matrix(self):
			self.cnt += 1
			return [[0,1],[1,0]]


class Mock2QubitGate(BasicGate):
		def __init__(self):
			BasicGate.__init__(self)
			self.cnt = 0
		
		@property
		def matrix(self):
			self.cnt += 1
			return [[0,1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]]


class MockNoMatrixGate(BasicGate):
		def __init__(self):
			BasicGate.__init__(self)
			self.cnt = 0
		
		@property
		def matrix(self):
			self.cnt += 1
			raise AttributeError


def test_simulator_is_available(sim):
	backend = DummyEngine(save_commands=True)
	eng = MainEngine(backend, [])
	qubit = eng.allocate_qubit()
	Measure | qubit
	BasicMathGate(lambda x:x) | qubit
	del qubit
	assert len(backend.received_commands) == 4
	
	# Test that allocate, measure, basic math, and deallocate are available.
	for cmd in backend.received_commands:
		assert sim.is_available(cmd)
	
	new_cmd = backend.received_commands[-1]
	
	new_cmd.gate = Mock1QubitGate()
	assert sim.is_available(new_cmd)
	assert new_cmd.gate.cnt == 1
	
	new_cmd.gate = Mock2QubitGate()
	assert not sim.is_available(new_cmd)
	assert new_cmd.gate.cnt == 1
	
	new_cmd.gate = MockNoMatrixGate()
	assert not sim.is_available(new_cmd)
	assert new_cmd.gate.cnt == 1
	
	eng = MainEngine(sim, [])
	qubit1 = eng.allocate_qubit()
	qubit2 = eng.allocate_qubit()
	with pytest.raises(Exception):
		Mock2QubitGate() | (qubit1, qubit2)


def test_simulator_cheat(sim):
	# cheat function should return a tuple
	assert isinstance(sim.cheat(), tuple)
	# first entry is the qubit mapping.
	# should be empty:
	assert len(sim.cheat()[0]) == 0
	# state vector should only have 1 entry:
	assert len(sim.cheat()[1]) == 1
	
	eng = MainEngine(sim, [])
	qubit = eng.allocate_qubit()
	
	# one qubit has been allocated
	assert len(sim.cheat()[0]) == 1
	assert sim.cheat()[0][0] == 0
	assert len(sim.cheat()[1]) == 2
	assert 1. == pytest.approx(abs(sim.cheat()[1][0]))
	
	del qubit
	# should be empty:
	assert len(sim.cheat()[0]) == 0
	# state vector should only have 1 entry:
	assert len(sim.cheat()[1]) == 1


def test_simulator_functional_measurement(sim):
	eng = MainEngine(sim, [])
	qubits = eng.allocate_qureg(5)
	# entangle all qubits:
	H | qubits[0]
	for qb in qubits[1:]:
		CNOT | (qubits[0], qb)
	
	Measure | qubits
	
	bit_value_sum = sum([int(qubit) for qubit in qubits])
	assert bit_value_sum == 0 or bit_value_sum == 5


class Plus2Gate(BasicMathGate):
	def __init__(self):
		BasicMathGate.__init__(self, lambda x : (x+2,))


def test_simulator_emulation(sim):
	eng = MainEngine(sim, [])
	qubit1 = eng.allocate_qubit()
	qubit2 = eng.allocate_qubit()
	qubit3 = eng.allocate_qubit()
	
	with Control(eng, qubit3):
		Plus2Gate() | (qubit1 + qubit2)
	
	assert 1. == pytest.approx(sim.cheat()[1][0])
	
	X | qubit3
	with Control(eng, qubit3):
		Plus2Gate() | (qubit1 + qubit2)
	assert 1. == pytest.approx(sim.cheat()[1][6])
	
	Measure | (qubit1 + qubit2 + qubit3)


def test_simulator_no_uncompute_exception(sim):
	eng = MainEngine(sim, [])
	qubit = eng.allocate_qubit()
	H | qubit
	with pytest.raises(RuntimeError):
		qubit[0].__del__()
	Measure | qubit

class MockSimulatorBackend(object):
	def __init__(self):
		self.run_cnt = 0
	
	def run(self):
		self.run_cnt += 1


def test_simulator_flush():
	sim = Simulator()
	sim._simulator = MockSimulatorBackend()
	
	eng = MainEngine(sim)
	eng.flush()
	
	assert sim._simulator.run_cnt == 1


def test_simulator_send():
	sim = Simulator()
	backend = DummyEngine(save_commands=True)
	
	eng = MainEngine(backend, [sim])
	
	qubit = eng.allocate_qubit()
	H | qubit
	Measure | qubit
	del qubit
	eng.flush()
	
	assert len(backend.received_commands) == 5


def test_simulator_functional_entangle(sim):
	eng = MainEngine(sim, [])
	qubits = eng.allocate_qureg(5)
	# entangle all qubits:
	H | qubits[0]
	for qb in qubits[1:]:
		CNOT | (qubits[0], qb)
	
	# check the state vector:
	assert .5 == pytest.approx(abs(sim.cheat()[1][0])**2)
	assert .5 == pytest.approx(abs(sim.cheat()[1][31])**2)
	for i in range(1, 31):
		assert 0. == pytest.approx(abs(sim.cheat()[1][i]))
	
	# unentangle all except the first 2
	for qb in qubits[2:]:
		CNOT | (qubits[0], qb)
	
	# entangle using Toffolis
	for qb in qubits[2:]:
		Toffoli | (qubits[0], qubits[1], qb)
	
	# check the state vector:
	assert .5 == pytest.approx(abs(sim.cheat()[1][0])**2)
	assert .5 == pytest.approx(abs(sim.cheat()[1][31])**2)
	for i in range(1, 31):
		assert 0. == pytest.approx(abs(sim.cheat()[1][i]))
	
	# uncompute using multi-controlled NOTs
	with Control(eng, qubits[0:-1]):
		X | qubits[-1]
	with Control(eng, qubits[0:-2]):
		X | qubits[-2]
	with Control(eng, qubits[0:-3]):
		X | qubits[-3]
	CNOT | (qubits[0], qubits[1])
	H | qubits[0]
	
	# check the state vector:
	assert 1. == pytest.approx(abs(sim.cheat()[1][0])**2)
	for i in range(1, 32):
		assert 0. == pytest.approx(abs(sim.cheat()[1][i]))
	
	Measure | qubits
