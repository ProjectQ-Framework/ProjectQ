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
Registers a decomposition rule for the quantum Fourier transform.

Decomposes the QFT gate into Hadamard and controlled phase-shift gates (R).

Warning:
	The final Swaps are not included, as those are simply a re-indexing of
	quantum registers.
"""

import math

from projectq.cengines import register_decomposition
from projectq.ops import H, R, QFT
from projectq.meta import Control


def _decompose_QFT(cmd):
	qb = cmd.qubits[0]
	eng = cmd.engine
	with Control(eng, cmd.control_qubits):
		for i in range(len(qb)):
			H | qb[-1 - i]
			for j in range(len(qb) - 1 - i):
				with Control(eng, qb[-1 - (j + i + 1)]):
					R(math.pi / (1 << (1 + j))) | qb[-1 - i]


register_decomposition(QFT.__class__, _decompose_QFT)
