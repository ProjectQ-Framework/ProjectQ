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

# Note from Daniel Strano of the Qrack simulator team:
#
# This test fails, for the Qrack simulator, unless we check probability instead of amplitude.
# I picked this apart for over a day, and I'm continuing to analyze it. The primary problem
# seems to stem from Qracks' Schmidt decomposition of separable qubits.
#
# Qrack relies on decomposing separable subsystems of qubits, for efficiency. It's desirable
# that all operations can be parallelized as OpenCL kernels. At the intersection of these
# two requirements, we use a parallelizable algorithm that assumes underlying separability,
# for a "cheap" Schmidt decomposition. This algorithm also assumes that a global phase offeset
# is physically arbitrary, for quantum mechanical purposes. There's no way easy way to
# guarantee that the global phase offset introduced here is zero. The Qrack simulator
# reproduces _probability_ within a reasonable tolerance, but not absolute global phase.
#
# Absolute global phase of a separable set of qubits is not physically measurable. Users
# are advised to avoid relying on direct checks of complex amplitudes, for deep but fairly
# obvious physical reasons: measurable physical quantities cannot be square roots of negative
# numbers. Probabilities resulting from the norm of complex amplitudes can be measured, though.
#
# (For a counterpoint to the above paragraph, consider the Aharanov-Bohm effect. That involves
# "potentials" in the absence of "fields," but my point is "there are more things in heaven
# and earth." Qrack is based on the physical non-observability of complex potential observables,
# though, for better or worse--but mostly for speed.)

from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)
from projectq.meta import Control
from projectq.ops import (All, ClassicalInstructionGate, Measure, Ph, QFT, Rx,
                          Ry, X, XGate)

from . import cnu2toffoliandcu

tolerance = 1e-6

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
        with Control(test_eng, test_ctrl_qureg):
            X | test_qb

        with Control(correct_eng, correct_ctrl_qureg[:2]):
            Rx(0.4) | correct_qb
        with Control(correct_eng, correct_ctrl_qureg):
            Ry(0.6) | correct_qb
        with Control(correct_eng, correct_ctrl_qureg):
            X | correct_qb

        test_eng.flush()
        correct_eng.flush()

        assert len(correct_dummy_eng.received_commands) == 9
        assert len(test_dummy_eng.received_commands) == 25

        for fstate in range(16):
            binary_state = format(fstate, '04b')
            test = test_sim.get_probability(binary_state,
                                          test_qb + test_ctrl_qureg)
            correct = correct_sim.get_probability(binary_state, correct_qb +
                                                correct_ctrl_qureg)
            assert correct == pytest.approx(test, rel=tolerance, abs=tolerance)

        All(Measure) | test_qb + test_ctrl_qureg
        All(Measure) | correct_qb + correct_ctrl_qureg
        test_eng.flush(deallocate_qubits=True)
        correct_eng.flush(deallocate_qubits=True)
