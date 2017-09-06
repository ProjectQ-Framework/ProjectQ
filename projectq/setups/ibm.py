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
Registers a variety of useful gate decompositions, specifically for the IBM
quantum experience backend. Among others it includes:

    * Controlled z-rotations --> Controlled NOTs and single-qubit rotations
    * Toffoli gate --> CNOT and single-qubit gates
    * m-Controlled global phases --> (m-1)-controlled phase-shifts
    * Global phases --> ignore
    * (controlled) Swap gates --> CNOTs and Toffolis
"""

import projectq
import projectq.setups.decompositions
from projectq.cengines import (TagRemover,
                               LocalOptimizer,
                               AutoReplacer,
                               IBMCNOTMapper,
                               DecompositionRuleSet)


def ibm_default_engines():
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    return [TagRemover(),
            LocalOptimizer(10),
            AutoReplacer(rule_set),
            TagRemover(),
            IBMCNOTMapper(),
            LocalOptimizer(10)]


projectq.default_engines = ibm_default_engines
