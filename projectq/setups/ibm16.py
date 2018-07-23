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
Defines a setup useful for the IBM QE chip with 16 qubits.

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

Moreover, it contains `LocalOptimizers`.
"""

import projectq
import projectq.libs.math
import projectq.setups.decompositions
from projectq.cengines import (AutoReplacer,
                               DecompositionRuleSet,
                               GridMapper,
                               InstructionFilter,
                               LocalOptimizer,
                               SwapAndCNOTFlipper,
                               TagRemover)
from projectq.setups.grid import high_level_gates


ibmqx5_connections = set([(1, 0), (1, 2), (2, 3), (3, 4), (3, 14), (5, 4),
                          (6, 5), (6, 7), (6, 11), (7, 10), (8, 7), (9, 8),
                          (9, 10), (11, 10), (12, 5), (12, 11), (12, 13),
                          (13, 4), (13, 14), (15, 0), (15, 2), (15, 14)])


grid_to_physical = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 0,
                    9: 15, 10: 14, 11: 13, 12: 12, 13: 11, 14: 10, 15: 9}


def get_engine_list():
    rule_set = DecompositionRuleSet(modules=[projectq.libs.math,
                                             projectq.setups.decompositions])
    return [TagRemover(),
            LocalOptimizer(5),
            AutoReplacer(rule_set),
            InstructionFilter(high_level_gates),
            TagRemover(),
            LocalOptimizer(5),
            AutoReplacer(rule_set),
            TagRemover(),
            GridMapper(2, 8, grid_to_physical),
            LocalOptimizer(5),
            SwapAndCNOTFlipper(ibmqx5_connections),
            LocalOptimizer(5)]
