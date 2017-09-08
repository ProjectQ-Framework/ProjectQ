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

"Tests for projectq.setups.decompositions.arb1qubit2rzandry.py."

from cmath import exp
import math

import numpy as np
import pytest

from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)
from projectq.ops import (BasicGate, ClassicalInstructionGate, Measure, Ph, R,
                          Rx, Ry, Rz, X)

from . import arb1qubit2rzandry as arb1q


def test_recognize_correct_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    Ph(0.1) | qubit
    R(0.2) | qubit
    Rx(0.3) | qubit
    X | qubit
    eng.flush(deallocate_qubits=True)
    # Don't test initial allocate and trailing deallocate and flush gate.
    for cmd in saving_backend.received_commands[1:-2]:
        assert arb1q._recognize_arb1qubit(cmd)


def test_recognize_incorrect_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    # Does not have matrix attribute:
    BasicGate() | qubit
    # Two qubit gate:
    two_qubit_gate = BasicGate()
    two_qubit_gate.matrix = [[1, 0, 0, 0], [0, 1, 0, 0],
                             [0, 0, 1, 0], [0, 0, 0, 1]]
    two_qubit_gate | qubit
    eng.flush(deallocate_qubits=True)
    for cmd in saving_backend.received_commands:
        assert not arb1q._recognize_arb1qubit(cmd)


def z_y_decomp_gates(eng, cmd):
    g = cmd.gate
    if isinstance(g, ClassicalInstructionGate):
        return True
    if len(cmd.control_qubits) == 0:
        if (isinstance(cmd.gate, Ry) or
                isinstance(cmd.gate, Rz) or
                isinstance(cmd.gate, Ph)):
            return True
    return False


def create_unitary_matrix(a, b, c, d):
    """
    Creates a unitary 2x2 matrix given parameters.

    Any unitary 2x2 matrix can be parametrized by:
    U = exp(ia) [[exp(j*b) * cos(d), exp(j*c) * sin(d)],
                 [-exp(-j*c) * sin(d), exp(-j*b) * cos(d)]]
    with 0 <= d <= pi/2 and 0 <= a,b,c < 2pi. If a==0, then
    det(U) == 1 and hence U is element of SU(2).

    Args:
        a,b,c (float): parameters 0 <= a,b,c < 2pi
        d (float): parameter 0 <= d <= pi/2

    Returns:
        2x2 matrix as nested lists
    """
    ph = exp(1j*a)  # global phase
    return [[ph * exp(1j*b) * math.cos(d), ph * exp(1j*c) * math.sin(d)],
            [ph * -exp(-1j*c) * math.sin(d), ph * exp(-1j*b) * math.cos(d)]]


def create_test_matrices():
    params = [(0.2, 0.3, 0.5, math.pi * 0.4),
              (1e-14, 0.3, 0.5, 0),
              (0.4, 0.0, math.pi * 2, 0.7),
              (0.0, 0.2, math.pi * 1.2, 1.5),  # element of SU(2)
              (0.4, 0.0, math.pi * 1.3, 0.8),
              (0.4, 4.1, math.pi * 1.3, 0),
              (5.1, 1.2, math.pi * 1.5, math.pi/2.),
              (1e-13, 1.2, math.pi * 3.7, math.pi/2.),
              (0, math.pi/2., 0, 0),
              (math.pi/2., -math.pi/2., 0, 0),
              (math.pi/2., math.pi/2., 0.1, 0.4),
              (math.pi*1.5, math.pi/2., 0, 0.4)]
    matrices = []
    for a, b, c, d in params:
        matrices.append(create_unitary_matrix(a, b, c, d))
    return matrices


@pytest.mark.parametrize("gate_matrix", create_test_matrices())
def test_decomposition(gate_matrix):
    for basis_state in ([1, 0], [0, 1]):
        # Create single qubit gate with gate_matrix
        test_gate = BasicGate()
        test_gate.matrix = np.matrix(gate_matrix)

        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(),
                                 engine_list=[correct_dummy_eng])

        rule_set = DecompositionRuleSet(modules=[arb1q])
        test_dummy_eng = DummyEngine(save_commands=True)
        test_eng = MainEngine(backend=Simulator(),
                              engine_list=[AutoReplacer(rule_set),
                                           InstructionFilter(z_y_decomp_gates),
                                           test_dummy_eng])

        correct_qb = correct_eng.allocate_qubit()
        correct_eng.flush()
        test_qb = test_eng.allocate_qubit()
        test_eng.flush()

        correct_eng.backend.set_wavefunction(basis_state, correct_qb)
        test_eng.backend.set_wavefunction(basis_state, test_qb)

        test_gate | test_qb
        test_gate | correct_qb

        test_eng.flush()
        correct_eng.flush()

        assert correct_dummy_eng.received_commands[2].gate == test_gate
        assert test_dummy_eng.received_commands[2].gate != test_gate

        for fstate in ['0', '1']:
            test = test_eng.backend.get_amplitude(fstate, test_qb)
            correct = correct_eng.backend.get_amplitude(fstate, correct_qb)
            assert correct == pytest.approx(test, rel=1e-12, abs=1e-12)

        Measure | test_qb
        Measure | correct_qb


@pytest.mark.parametrize("gate_matrix", [[[2, 0], [0, 4]],
                                         [[0, 2], [4, 0]],
                                         [[1, 2], [4, 0]]])
def test_decomposition_errors(gate_matrix):
    test_gate = BasicGate()
    test_gate.matrix = np.matrix(gate_matrix)
    rule_set = DecompositionRuleSet(modules=[arb1q])
    eng = MainEngine(backend=DummyEngine(),
                     engine_list=[AutoReplacer(rule_set),
                                  InstructionFilter(z_y_decomp_gates)])
    qb = eng.allocate_qubit()
    with pytest.raises(Exception):
        test_gate | qb
