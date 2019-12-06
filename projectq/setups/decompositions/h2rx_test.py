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

"Tests for projectq.setups.decompositions.h2rx.py"

import math

import numpy as np

import pytest

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)
from projectq.meta import Control
from projectq.ops import Measure, Ph, H, HGate

import h2rx

def test_recognize_correct_gates():
    """ Test that recognize_HNoCtrl recognizes ctrl qubits """
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qubit = eng.allocate_qubit()
    eng.flush()
    H | qubit
    with Control(eng, ctrl_qubit):
        H | qubit
    eng.flush(deallocate_qubits=True)
    assert h2rx._recognize_HNoCtrl(saving_backend.received_commands[3])
    assert not h2rx._recognize_HNoCtrl(saving_backend.received_commands[4])


def h_decomp_gates(eng, cmd):
    """ Test that cmd.gate is the gate H """
    g = cmd.gate
    if isinstance(g, HGate): # H is just a shortcut to HGate
        return False
    else:
        return True

# ------------test_decomposition function-------------#
# Creates two engines, correct_eng and test_eng. 
# correct_eng implements H gate. 
# test_eng implements the decomposition of the H gate.
# correct_qb and test_qb represent results of these two
# engines, respectively. 
# The decomposition in this case only produces the 
# same state as H up to a global phase. 
# test_vector and correct_vector represent the final 
# wave states of correct_qb and test_qb. 
# The dot product of correct_vector and test_vector
# should have absolute value 1, if the two vectors are the
# same up to a global phase.

def test_decomposition():
    """ Test that this decomposition of H produces correct amplitudes 
    
        Note that this function tests the first DecompositionRule in 
        h2rx.all_defined_decomposition_rules
    """
    for basis_state in ([1, 0], [0, 1]):
        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(),
                                 engine_list=[correct_dummy_eng])

        rule_set = DecompositionRuleSet(modules=[h2rx])
        test_dummy_eng = DummyEngine(save_commands=True)
        test_eng = MainEngine(backend=Simulator(),
                              engine_list=[AutoReplacer(rule_set),
                                           InstructionFilter(h_decomp_gates),
                                           test_dummy_eng])

        correct_qb = correct_eng.allocate_qubit()
        H | correct_qb
        correct_eng.flush()

        test_qb = test_eng.allocate_qubit()
        H | test_qb
        test_eng.flush()

        assert correct_dummy_eng.received_commands[1].gate == H
        assert test_dummy_eng.received_commands[1].gate != H

        # Create empty vectors for the wave vectors for the correct 
        # and test qubits
        correct_vector = np.zeros((2,1),dtype=np.complex_)
        test_vector = np.zeros((2,1),dtype=np.complex_)

        i=0
        for fstate in ['0', '1']:
            test = test_eng.backend.get_amplitude(fstate, test_qb)
            correct = correct_eng.backend.get_amplitude(fstate, correct_qb)
            correct_vector[i] = correct
            test_vector[i] = test
            i+=1

        # Necessary to transpose vector to use matrix dot product
        test_vector = test_vector.transpose()
        # Remember that transposed vector should come first in product
        vector_dot_product = np.dot(test_vector, correct_vector) 
        
        assert np.absolute(vector_dot_product) == pytest.approx(1, rel=1e-12, abs=1e-12)

        Measure | test_qb
        Measure | correct_qb