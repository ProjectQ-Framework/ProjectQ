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

"Tests for projectq.setups.decompositions.phaseestimation.py."

from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)
from projectq.meta import Control

from projectq.ops import X, All, Measure

from projectq.ops import QPE
from projectq.setups.decompositions import phaseestimation as pe


def test_phaseestimation():
    rule_set = DecompositionRuleSet(modules=[pe])
    eng = MainEngine(backend=Simulator(),
                     engine_list=[AutoReplacer(rule_set),
                                  ])
    system_qubits = eng.allocate_qureg(2)
    qpe_ancillas = eng.allocate_qureg(4)
    eng.flush()
    
    U = X
    
    QPE(U) | (qpe_ancillas, system_qubits)
    

test_phaseestimation()
