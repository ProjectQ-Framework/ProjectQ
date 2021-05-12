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

"Tests for projectq.setups.decompositions.cnot2cz.py."

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

from projectq.setups.decompositions import cnot2cz


def test_recognize_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, verbose=True)
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()
    eng.flush()
    CZ | (qubit1, qubit2)
    with Control(eng, qubit2):
        Z | qubit1
        X | qubit1
    with Control(eng, qubit2 + qubit3):
        Z | qubit1
    eng.flush()  # To make sure gates arrive before deallocate gates
    eng.flush(deallocate_qubits=True)
    # Don't test initial 4 allocate and flush
    for cmd in saving_backend.received_commands[5:7]:
        assert cnot2cz._recognize_cnot(cmd)
    for cmd in saving_backend.received_commands[7:9]:
        assert not cnot2cz._recognize_cnot(cmd)


def _decomp_gates(eng, cmd):
    if len(cmd.control_qubits) == 1 and isinstance(cmd.gate, X.__class__):
        return False
    return True


def test_cnot_decomposition():
    for basis_state_index in range(0, 4):
        basis_state = [0] * 4
        basis_state[basis_state_index] = 1.0
        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(), engine_list=[correct_dummy_eng])
        rule_set = DecompositionRuleSet(modules=[cnot2cz])
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
        assert len(test_dummy_eng.received_commands) == 7

        for fstate in range(4):
            binary_state = format(fstate, '02b')
            test = test_sim.get_amplitude(binary_state, test_qb + test_ctrl_qb)
            correct = correct_sim.get_amplitude(binary_state, correct_qb + correct_ctrl_qb)
            assert correct == pytest.approx(test, rel=1e-12, abs=1e-12)

        All(Measure) | test_qb + test_ctrl_qb
        All(Measure) | correct_qb + correct_ctrl_qb
        test_eng.flush(deallocate_qubits=True)
        correct_eng.flush(deallocate_qubits=True)
