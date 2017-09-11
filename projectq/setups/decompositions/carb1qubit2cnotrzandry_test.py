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

"Tests for projectq.setups.decompositions.carb1qubit2cnotrzandry.py."

import numpy as np
import pytest

from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)
from projectq.meta import Control
from projectq.ops import (BasicGate, ClassicalInstructionGate, Measure,
                          Ph, R, Rx, Ry, Rz, X, XGate)
from projectq.setups.decompositions import arb1qubit2rzandry_test as arb1q_t

from . import carb1qubit2cnotrzandry as carb1q


def test_recognize_correct_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qubit = eng.allocate_qubit()
    eng.flush()
    with Control(eng, ctrl_qubit):
        Ph(0.1) | qubit
        R(0.2) | qubit
        Rx(0.3) | qubit
        X | qubit
    eng.flush(deallocate_qubits=True)
    # Don't test initial two allocate and flush and trailing deallocate
    # and flush gate.
    for cmd in saving_backend.received_commands[3:-3]:
        assert carb1q._recognize_carb1qubit(cmd)


def test_recognize_incorrect_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qubit = eng.allocate_qubit()
    ctrl_qureg = eng.allocate_qureg(2)
    eng.flush()
    with Control(eng, ctrl_qubit):
        # Does not have matrix attribute:
        BasicGate() | qubit
        # Two qubit gate:
        two_qubit_gate = BasicGate()
        two_qubit_gate.matrix = [[1, 0, 0, 0], [0, 1, 0, 0],
                                 [0, 0, 1, 0], [0, 0, 0, 1]]
        two_qubit_gate | qubit
    with Control(eng, ctrl_qureg):
        # Too many Control qubits:
        Rx(0.3) | qubit
    eng.flush(deallocate_qubits=True)
    for cmd in saving_backend.received_commands:
        assert not carb1q._recognize_carb1qubit(cmd)


def _decomp_gates(eng, cmd):
    g = cmd.gate
    if isinstance(g, ClassicalInstructionGate):
        return True
    if len(cmd.control_qubits) == 0:
        if (isinstance(cmd.gate, Ry) or
                isinstance(cmd.gate, Rz) or
                isinstance(cmd.gate, Ph)):
            return True
    if len(cmd.control_qubits) == 1:
        if (isinstance(cmd.gate, XGate) or
                isinstance(cmd.gate, Ph)):
            return True
    return False


@pytest.mark.parametrize("gate_matrix", [[[1, 0], [0, -1]],
                                         [[0, -1j], [1j, 0]]])
def test_recognize_v(gate_matrix):
    assert carb1q._recognize_v(gate_matrix)


@pytest.mark.parametrize("gate_matrix", arb1q_t.create_test_matrices())
def test_decomposition(gate_matrix):
    # Create single qubit gate with gate_matrix
    test_gate = BasicGate()
    test_gate.matrix = np.matrix(gate_matrix)

    for basis_state in ([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0],
                        [0, 0, 0, 1]):
        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(),
                                 engine_list=[correct_dummy_eng])

        rule_set = DecompositionRuleSet(modules=[carb1q])
        test_dummy_eng = DummyEngine(save_commands=True)
        test_eng = MainEngine(backend=Simulator(),
                              engine_list=[AutoReplacer(rule_set),
                                           InstructionFilter(_decomp_gates),
                                           test_dummy_eng])
        test_sim = test_eng.backend
        correct_sim = correct_eng.backend

        correct_qb = correct_eng.allocate_qubit()
        correct_ctrl_qb = correct_eng.allocate_qubit()
        correct_eng.flush()
        test_qb = test_eng.allocate_qubit()
        test_ctrl_qb = test_eng.allocate_qubit()
        test_eng.flush()

        correct_sim.set_wavefunction(basis_state, correct_qb +
                                     correct_ctrl_qb)
        test_sim.set_wavefunction(basis_state, test_qb + test_ctrl_qb)

        with Control(test_eng, test_ctrl_qb):
            test_gate | test_qb
        with Control(correct_eng, correct_ctrl_qb):
            test_gate | correct_qb

        test_eng.flush()
        correct_eng.flush()

        assert correct_dummy_eng.received_commands[3].gate == test_gate
        assert test_dummy_eng.received_commands[3].gate != test_gate

        for fstate in ['00', '01', '10', '11']:
            test = test_sim.get_amplitude(fstate, test_qb + test_ctrl_qb)
            correct = correct_sim.get_amplitude(fstate, correct_qb +
                                                correct_ctrl_qb)
            assert correct == pytest.approx(test, rel=1e-12, abs=1e-12)

        Measure | test_qb + test_ctrl_qb
        Measure | correct_qb + correct_ctrl_qb
        test_eng.flush(deallocate_qubits=True)
        correct_eng.flush(deallocate_qubits=True)
