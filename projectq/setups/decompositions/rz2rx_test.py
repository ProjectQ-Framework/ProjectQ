# -*- coding: utf-8 -*-
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

"Tests for projectq.setups.decompositions.rz2rx.py"

import math
import numpy as np
import pytest

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (
    AutoReplacer,
    DecompositionRuleSet,
    DummyEngine,
    InstructionFilter,
)
from projectq.meta import Control
from projectq.ops import Measure, Rz

from . import rz2rx


def test_recognize_correct_gates():
    """Test that recognize_RzNoCtrl recognizes ctrl qubits"""
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qubit = eng.allocate_qubit()
    eng.flush()
    Rz(0.3) | qubit
    with Control(eng, ctrl_qubit):
        Rz(0.4) | qubit
    eng.flush(deallocate_qubits=True)
    assert rz2rx._recognize_RzNoCtrl(saving_backend.received_commands[3])
    assert not rz2rx._recognize_RzNoCtrl(saving_backend.received_commands[4])


def rz_decomp_gates(eng, cmd):
    """Test that cmd.gate is the gate Rz"""
    g = cmd.gate
    if isinstance(g, Rz):
        return False
    else:
        return True


# ------------test_decomposition function-------------#
# Creates two engines, correct_eng and test_eng.
# correct_eng implements Rz(angle) gate.
# test_eng implements the decomposition of the Rz(angle) gate.
# correct_qb and test_qb represent results of these two engines, respectively.
#
# The decomposition only needs to produce the same state in a qubit up to a
# global phase.
# test_vector and correct_vector represent the final wave states of correct_qb
# and test_qb.
#
# The dot product of correct_vector and test_vector should have absolute value
# 1, if the two vectors are the same up to a global phase.


@pytest.mark.parametrize("angle", [0, math.pi, 2 * math.pi, 4 * math.pi, 0.5])
def test_decomposition(angle):
    """
    Test that this decomposition of Rz produces correct amplitudes

    Note that this function tests each DecompositionRule in
    rz2rx.all_defined_decomposition_rules
    """
    decomposition_rule_list = rz2rx.all_defined_decomposition_rules
    for rule in decomposition_rule_list:
        for basis_state in ([1, 0], [0, 1]):
            correct_dummy_eng = DummyEngine(save_commands=True)
            correct_eng = MainEngine(backend=Simulator(), engine_list=[correct_dummy_eng])

            rule_set = DecompositionRuleSet(rules=[rule])
            test_dummy_eng = DummyEngine(save_commands=True)
            test_eng = MainEngine(
                backend=Simulator(),
                engine_list=[
                    AutoReplacer(rule_set),
                    InstructionFilter(rz_decomp_gates),
                    test_dummy_eng,
                ],
            )

            correct_qb = correct_eng.allocate_qubit()
            Rz(angle) | correct_qb
            correct_eng.flush()

            test_qb = test_eng.allocate_qubit()
            Rz(angle) | test_qb
            test_eng.flush()

            # Create empty vectors for the wave vectors for the correct and
            # test qubits
            correct_vector = np.zeros((2, 1), dtype=np.complex_)
            test_vector = np.zeros((2, 1), dtype=np.complex_)

            i = 0
            for fstate in ['0', '1']:
                test = test_eng.backend.get_amplitude(fstate, test_qb)
                correct = correct_eng.backend.get_amplitude(fstate, correct_qb)
                correct_vector[i] = correct
                test_vector[i] = test
                i += 1

            # Necessary to transpose vector to use matrix dot product
            test_vector = test_vector.transpose()
            # Remember that transposed vector should come first in product
            vector_dot_product = np.dot(test_vector, correct_vector)

            assert np.absolute(vector_dot_product) == pytest.approx(1, rel=1e-12, abs=1e-12)

            Measure | test_qb
            Measure | correct_qb
