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
Registers a decomposition rule for the Toffoli gate.

Decomposes the Toffoli gate using Hadamard, T, Tdag, and CNOT gates.
"""

from projectq.cengines import register_decomposition
from projectq.meta import get_control_count
from projectq.ops import NOT, CNOT, T, Tdag, H


def _decompose_toffoli(cmd):
	""" Decompose the Toffoli gate into CNOT, H, T, and Tdagger gates. """
	ctrl = cmd.control_qubits
	eng = cmd.engine
	
	target = cmd.qubits[0]
	c1 = ctrl[0]
	c2 = ctrl[1]
	
	H | target
	CNOT | (c1, target)
	T | c1
	Tdag | target
	CNOT | (c2, target)
	CNOT | (c2, c1)
	Tdag | c1
	T | target
	CNOT | (c2, c1)
	CNOT | (c1, target)
	Tdag | target
	CNOT | (c2, target)
	T | target
	T | c2
	H | target


def _recognize_toffoli(cmd):
	""" Recognize the Toffoli gate. """
	return get_control_count(cmd) == 2


register_decomposition(NOT.__class__, _decompose_toffoli, _recognize_toffoli)
