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
Defines a setup useful for the IBM QE chip with 5 qubits.

It provides the `engine_list` for the `MainEngine`, and contains an
AutoReplacer with most of the gate decompositions of ProjectQ, among others
it includes:

    * Controlled z-rotations --> Controlled NOTs and single-qubit rotations
    * Toffoli gate --> CNOT and single-qubit gates
    * m-Controlled global phases --> (m-1)-controlled phase-shifts
    * Global phases --> ignore
    * (controlled) Swap gates --> CNOTs and Toffolis
    * Arbitrary single qubit gates --> Rz and Ry
    * Controlled arbitrary single qubit gates --> Rz, Ry, and CNOT gates

Moreover, it contains `LocalOptimizers` and a custom mapper for the CNOT
gates.

"""

import projectq
import projectq.setups.decompositions
from projectq.cengines import (TagRemover,
                               LocalOptimizer,
                               AutoReplacer,
                               IBM5QubitMapper,
                               SwapAndCNOTFlipper,
                               DecompositionRuleSet)


ibmqx4_connections = set([(2, 1), (4, 2), (2, 0), (3, 2), (3, 4), (1, 0)])


def get_engine_list():
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    return [TagRemover(),
            LocalOptimizer(10),
            AutoReplacer(rule_set),
            TagRemover(),
            IBM5QubitMapper(),
            SwapAndCNOTFlipper(ibmqx4_connections),
            LocalOptimizer(10)]
