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
"""
A few shortcuts for certain gates.

These include:
* CNOT = C(NOT)
* CRz = C(Rz)
* Toffoli = C(NOT,2) = C(CNOT)
"""

from ._gates import NOT, Rz, Z
from ._metagates import C


def CRz(angle):
    """Shortcut for C(Rz(angle), n_qubits=1)."""
    return C(Rz(angle), n_qubits=1)


CNOT = CX = C(NOT)

CZ = C(Z)

Toffoli = C(CNOT)
