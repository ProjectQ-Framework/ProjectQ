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
Tests for projectq.backends._resource.py.
"""

import pytest

from projectq.cengines import MainEngine, DummyEngine
from projectq.ops import H, CNOT, X, Measure

from projectq.backends import ResourceCounter


class MockEngine(object):
	def is_available(self, cmd):
		return False


def test_resource_counter_isavailable():
	resource_counter = ResourceCounter()
	resource_counter.next_engine = MockEngine()
	assert not resource_counter.is_available("test")
	resource_counter.next_engine = None
	resource_counter.is_last_engine = True
	
	assert resource_counter.is_available("test")
	
	
def test_resource_counter():
	resource_counter = ResourceCounter()
	backend = DummyEngine(save_commands=True)
	eng = MainEngine(backend, [resource_counter])
	
	qubit1 = eng.allocate_qubit()
	qubit2 = eng.allocate_qubit()
	H | qubit1
	X | qubit2
	del qubit2
	
	qubit3 = eng.allocate_qubit()
	CNOT | (qubit1, qubit3)
	
	Measure | (qubit1, qubit3)
	
	assert int(qubit1) == int(qubit3)
	assert int(qubit1) == 0
	
	assert resource_counter.max_width == 2
	
	str_repr = str(resource_counter)
	assert str_repr.count("H") == 1
	assert str_repr.count("X") == 2
	assert str_repr.count("CX") == 1
	assert str_repr.count("Allocate : 3") == 1
	assert str_repr.count("Deallocate : 1") == 1
	
	sent_gates = [cmd.gate for cmd in backend.received_commands]
	assert sent_gates.count(H) == 1
	assert sent_gates.count(X) == 2
	assert sent_gates.count(Measure) == 1
	
