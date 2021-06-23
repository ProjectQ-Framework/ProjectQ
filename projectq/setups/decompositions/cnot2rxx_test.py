# -*- coding: utf-8 -*-
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

"Tests for projectq.setups.decompositions.cnot2rxx.py."

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
from projectq.ops import All, CNOT, CZ, Measure, X, Z

from . import cnot2rxx


def test_recognize_correct_gates():
    """Test that recognize_cnot recognizes cnot gates."""
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()
    eng.flush()
    # Create a control function in 3 different ways
    CZ | (qubit1, qubit2)
    with Control(eng, qubit2):
        Z | qubit1
        X | qubit1
    with Control(eng, qubit2 + qubit3):
        Z | qubit1
    eng.flush()
    eng.flush(deallocate_qubits=True)
    for cmd in saving_backend.received_commands[4:7]:
        assert cnot2rxx._recognize_cnot2(cmd)
    for cmd in saving_backend.received_commands[7:9]:
        assert not cnot2rxx._recognize_cnot2(cmd)


def _decomp_gates(eng, cmd):
    """Test that the cmd.gate is a gate of class X"""
    if len(cmd.control_qubits) == 1 and isinstance(cmd.gate, X.__class__):
        return False
    return True


# ------------test_decomposition function-------------#
# Creates two engines, correct_eng and test_eng.
# correct_eng implements CNOT gate.
# test_eng implements the decomposition of the CNOT gate.
# correct_qb and test_qb represent results of these two engines, respectively.
#
# The decomposition in this case only produces the same state as CNOT up to a
# global phase.
# test_vector and correct_vector represent the final wave states of correct_qb
# and test_qb.
#
# The dot product of correct_vector and test_vector should have absolute value
# 1, if the two vectors are the same up to a global phase.


def test_decomposition():
    """Test that this decomposition of CNOT produces correct amplitudes

    Function tests each DecompositionRule in
    cnot2rxx.all_defined_decomposition_rules
    """
    decomposition_rule_list = cnot2rxx.all_defined_decomposition_rules
    for rule in decomposition_rule_list:
        for basis_state_index in range(0, 4):
            basis_state = [0] * 4
            basis_state[basis_state_index] = 1.0
            correct_dummy_eng = DummyEngine(save_commands=True)
            correct_eng = MainEngine(backend=Simulator(), engine_list=[correct_dummy_eng])
            rule_set = DecompositionRuleSet(rules=[rule])
            test_dummy_eng = DummyEngine(save_commands=True)
            test_eng = MainEngine(
                backend=Simulator(),
                engine_list=[
                    AutoReplacer(rule_set),
                    InstructionFilter(_decomp_gates),
                    test_dummy_eng,
                ],
            )
            test_sim = test_eng.backend
            correct_sim = correct_eng.backend
            correct_qb = correct_eng.allocate_qubit()
            correct_ctrl_qb = correct_eng.allocate_qubit()
            correct_eng.flush()
            test_qb = test_eng.allocate_qubit()
            test_ctrl_qb = test_eng.allocate_qubit()
            test_eng.flush()

            correct_sim.set_wavefunction(basis_state, correct_qb + correct_ctrl_qb)
            test_sim.set_wavefunction(basis_state, test_qb + test_ctrl_qb)
            CNOT | (test_ctrl_qb, test_qb)
            CNOT | (correct_ctrl_qb, correct_qb)

            test_eng.flush()
            correct_eng.flush()

            assert len(correct_dummy_eng.received_commands) == 5
            assert len(test_dummy_eng.received_commands) == 10

            assert correct_eng.backend.cheat()[1] == pytest.approx(test_eng.backend.cheat()[1], rel=1e-12, abs=1e-12)

            All(Measure) | test_qb + test_ctrl_qb
            All(Measure) | correct_qb + correct_ctrl_qb
            test_eng.flush(deallocate_qubits=True)
            correct_eng.flush(deallocate_qubits=True)
