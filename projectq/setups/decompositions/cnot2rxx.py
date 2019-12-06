#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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
Registers a decomposition to for a CNOT gate in terms of Rxx, Rx and Ry gates.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, get_control_count, Uncompute
from projectq.ops import Rxx,Ry,Rx,Rz,X,Y,Z
import math

def _decompose_cnot2rxx_M(cmd):
    """ Decompose CNOT gates. """
    print("decompose_M called")
    ctrl = cmd.control_qubits
    Ry(math.pi/2) | ctrl[0]
    Rx(-math.pi/2)| ctrl[0]
    Rx(-math.pi/2)| cmd.qubits[0][0]
    Rxx(math.pi/2) | (ctrl[0], cmd.qubits[0][0])
    Ry(-1*math.pi/2)| ctrl[0]

def _decompose_cnot2rxx_P(cmd):
    """ Decompose CNOT gates. """
    print("decompose_P called")
    ctrl = cmd.control_qubits
    Ry(-math.pi/2) | ctrl[0]
    Rx(-math.pi/2)| ctrl[0]
    Rx(math.pi/2)| cmd.qubits[0][0]
    Rxx(math.pi/2) | (ctrl[0], cmd.qubits[0][0])
    Ry(math.pi/2)| ctrl[0]

def _recognize_cnot(cmd):
    print('RECOGNIZE CNOT')
    print(cmd)
    print(get_control_count(cmd))
    return get_control_count(cmd) == 1

#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(X.__class__, _decompose_cnot2rxx_M, _recognize_cnot),
    DecompositionRule(X.__class__, _decompose_cnot2rxx_P, _recognize_cnot)
]
