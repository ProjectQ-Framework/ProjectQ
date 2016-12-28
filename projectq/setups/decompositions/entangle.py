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
Registers a decomposition for the Entangle gate.

Applies a Hadamard gate to the first qubit and then, conditioned on this first
qubit, CNOT gates to all others.
"""

from projectq.cengines import register_decomposition
from projectq.meta import Control, get_control_count
from projectq.ops import X, H, Entangle, All


def _decompose_entangle(cmd):
	""" Decompose the entangle gate. """
	qr = cmd.qubits[0]
	eng = cmd.engine
	
	with Control(eng, cmd.control_qubits):
		H | qr[0]
		with Control(eng, qr[0]):
			All(X) | qr[1:]


register_decomposition(Entangle.__class__, _decompose_entangle)
