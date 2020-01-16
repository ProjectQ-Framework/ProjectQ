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

"Tests for projectq.setups.trapped_ion_decomposer.py."

import math
import projectq
from projectq import MainEngine
from projectq.ops import Rx, Ry, Rz, H, CNOT, Measure, All, X, Rxx
from projectq.meta import Compute, Control, Uncompute
from projectq.cengines import DecompositionRule
from projectq.cengines import (AutoReplacer, DecompositionRuleSet, DummyEngine,
                               InstructionFilter)
import pytest
import projectq.setups.restrictedgateset as restrictedgateset
from projectq.setups.trapped_ion_decomposer import chooser_Ry_reducer

# Without the chooser_Ry_reducer function, i.e. if 
# the restricted gate set just picked the first option in
# each decomposition list, the circuit below would be
# decomposed into 8 single qubit gates and 1 two qubit gate.
# Including the Allocate and Measure commands, this would 
# result in 12 commands. 
# Using the chooser_Rx_reducer you get 9 commands, since you 
# now have 4 single qubit gates and 1 two qubit gate.

def test_chooser_Ry_reducer():
    """  
    Without the chooser_Ry_reducer function, i.e. if 
    the restricted gate set just picked the first option in
    each decomposition list, the circuit below would be
    decomposed into 8 single qubit gates and 1 two qubit gate.
    Including the Allocate and Measure commands, this 
    results in 12 commands. 
    Using the chooser_Rx_reducer you get 9 commands, the 
    decomposotion having resulted in 4 single qubit gates 
    and 1 two qubit gate.
    """
    engine_list = restrictedgateset.get_engine_list(
        one_qubit_gates=(Rx, Ry),
        two_qubit_gates=(Rxx,), compiler_chooser=chooser_Ry_reducer)
    backend = DummyEngine(save_commands=True)
    eng = projectq.MainEngine(backend, engine_list, verbose=True)
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    H | qubit1
    CNOT | (qubit1, qubit2)
    Rz(0.2) | qubit1
    Measure | qubit1
    assert len(backend.received_commands) < 12

