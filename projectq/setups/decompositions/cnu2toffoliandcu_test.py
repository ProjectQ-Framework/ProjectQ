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

"Tests for projectq.setups.decompositions.cnu2toffoliandcu."

import pytest

from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)
from projectq.meta import Control
from projectq.ops import (ClassicalInstructionGate, Measure, Ph, QFT, Rx, Ry,
                          X, XGate)

from . import cnu2toffoliandcu


def test_recognize_correct_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qureg = eng.allocate_qureg(2)
    ctrl_qureg2 = eng.allocate_qureg(3)
    eng.flush()
    with Control(eng, ctrl_qureg):
        Ph(0.1) | qubit
        Ry(0.2) | qubit
    with Control(eng, ctrl_qureg2):
        QFT | qubit + ctrl_qureg
        X | qubit
    eng.flush()  # To make sure gates arrive before deallocate gates
    eng.flush(deallocate_qubits=True)
    # Don't test initial 6 allocate and flush and trailing deallocate
    # and two flush gates.
    for cmd in saving_backend.received_commands[7:-8]:
        assert cnu2toffoliandcu._recognize_CnU(cmd)


def test_recognize_incorrect_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qubit = eng.allocate_qubit()
    ctrl_qureg = eng.allocate_qureg(2)
    eng.flush()
    with Control(eng, ctrl_qubit):
        Rx(0.3) | qubit
    X | qubit
    with Control(eng, ctrl_qureg):
        X | qubit
    eng.flush(deallocate_qubits=True)
    for cmd in saving_backend.received_commands:
        assert not cnu2toffoliandcu._recognize_CnU(cmd)


def _decomp_gates(eng, cmd):
    g = cmd.gate
    if isinstance(g, ClassicalInstructionGate):
        return True
    if len(cmd.control_qubits) <= 1:
        return True
    if len(cmd.control_qubits) == 2 and isinstance(cmd.gate, XGate):
        return True
    return False


def test_decomposition():
    for basis_state_index in range(0, 16):
        basis_state = [0] * 16
        basis_state[basis_state_index] = 1.
        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(),
                                 engine_list=[correct_dummy_eng])
        rule_set = DecompositionRuleSet(modules=[cnu2toffoliandcu])
        test_dummy_eng = DummyEngine(save_commands=True)
        test_eng = MainEngine(backend=Simulator(),
                              engine_list=[AutoReplacer(rule_set),
                                           InstructionFilter(_decomp_gates),
                                           test_dummy_eng])
        test_sim = test_eng.backend
        correct_sim = correct_eng.backend
        correct_qb = correct_eng.allocate_qubit()
        correct_ctrl_qureg = correct_eng.allocate_qureg(3)
        correct_eng.flush()
        test_qb = test_eng.allocate_qubit()
        test_ctrl_qureg = test_eng.allocate_qureg(3)
        test_eng.flush()

        correct_sim.set_wavefunction(basis_state, correct_qb +
                                     correct_ctrl_qureg)
        test_sim.set_wavefunction(basis_state, test_qb + test_ctrl_qureg)

        with Control(test_eng, test_ctrl_qureg[:2]):
            Rx(0.4) | test_qb
        with Control(test_eng, test_ctrl_qureg):
            Ry(0.6) | test_qb

        with Control(correct_eng, correct_ctrl_qureg[:2]):
            Rx(0.4) | correct_qb
        with Control(correct_eng, correct_ctrl_qureg):
            Ry(0.6) | correct_qb

        test_eng.flush()
        correct_eng.flush()

        assert len(correct_dummy_eng.received_commands) == 8
        assert len(test_dummy_eng.received_commands) == 20

        for fstate in range(16):
            binary_state = format(fstate, '04b')
            test = test_sim.get_amplitude(binary_state,
                                          test_qb + test_ctrl_qureg)
            correct = correct_sim.get_amplitude(binary_state, correct_qb +
                                                correct_ctrl_qureg)
            assert correct == pytest.approx(test, rel=1e-12, abs=1e-12)

        Measure | test_qb + test_ctrl_qureg
        Measure | correct_qb + correct_ctrl_qureg
        test_eng.flush(deallocate_qubits=True)
        correct_eng.flush(deallocate_qubits=True)
