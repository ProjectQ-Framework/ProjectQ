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
"""Tests for projectq.setups.decompositions.sqrtswap2cnot."""

import pytest

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (
    AutoReplacer,
    DecompositionRuleSet,
    DummyEngine,
    InstructionFilter,
)
from projectq.ops import All, Measure, SqrtSwap, Command
from projectq.types import WeakQubitRef

import projectq.setups.decompositions.sqrtswap2cnot as sqrtswap2cnot


def _decomp_gates(eng, cmd):
    if isinstance(cmd.gate, SqrtSwap.__class__):
        return False
    return True


def test_sqrtswap_invalid():
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)

    with pytest.raises(ValueError):
        sqrtswap2cnot._decompose_sqrtswap(Command(None, SqrtSwap, ([qb0], [qb1], [qb2])))

    with pytest.raises(ValueError):
        sqrtswap2cnot._decompose_sqrtswap(Command(None, SqrtSwap, ([qb0], [qb1, qb2])))


def test_sqrtswap():
    for basis_state in ([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]):
        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(), engine_list=[correct_dummy_eng])
        rule_set = DecompositionRuleSet(modules=[sqrtswap2cnot])
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
        correct_qureg = correct_eng.allocate_qureg(2)
        correct_eng.flush()
        test_qureg = test_eng.allocate_qureg(2)
        test_eng.flush()

        correct_sim.set_wavefunction(basis_state, correct_qureg)
        test_sim.set_wavefunction(basis_state, test_qureg)

        SqrtSwap | (test_qureg[0], test_qureg[1])
        test_eng.flush()
        SqrtSwap | (correct_qureg[0], correct_qureg[1])
        correct_eng.flush()

        assert len(test_dummy_eng.received_commands) != len(correct_dummy_eng.received_commands)
        for fstate in range(4):
            binary_state = format(fstate, '02b')
            test = test_sim.get_amplitude(binary_state, test_qureg)
            correct = correct_sim.get_amplitude(binary_state, correct_qureg)
            assert correct == pytest.approx(test, rel=1e-10, abs=1e-10)

        All(Measure) | test_qureg
        All(Measure) | correct_qureg
        test_eng.flush(deallocate_qubits=True)
        correct_eng.flush(deallocate_qubits=True)
