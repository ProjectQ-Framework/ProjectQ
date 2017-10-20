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

"Tests for projectq.setups.decompositions.ry2rz.py"

import math

import pytest

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)
from projectq.meta import Control
from projectq.ops import Measure, Ph, Ry

from . import ry2rz


def test_recognize_correct_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qubit = eng.allocate_qubit()
    eng.flush()
    Ry(0.3) | qubit
    with Control(eng, ctrl_qubit):
        Ry(0.4) | qubit
    eng.flush(deallocate_qubits=True)
    assert ry2rz._recognize_RyNoCtrl(saving_backend.received_commands[3])
    assert not ry2rz._recognize_RyNoCtrl(saving_backend.received_commands[4])


def ry_decomp_gates(eng, cmd):
    g = cmd.gate
    if isinstance(g, Ry):
        return False
    else:
        return True


@pytest.mark.parametrize("angle", [0, math.pi, 2*math.pi, 4*math.pi, 0.5])
def test_decomposition(angle):
    for basis_state in ([1, 0], [0, 1]):
        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(),
                                 engine_list=[correct_dummy_eng])

        rule_set = DecompositionRuleSet(modules=[ry2rz])
        test_dummy_eng = DummyEngine(save_commands=True)
        test_eng = MainEngine(backend=Simulator(),
                              engine_list=[AutoReplacer(rule_set),
                                           InstructionFilter(ry_decomp_gates),
                                           test_dummy_eng])

        correct_qb = correct_eng.allocate_qubit()
        Ry(angle) | correct_qb
        correct_eng.flush()

        test_qb = test_eng.allocate_qubit()
        Ry(angle) | test_qb
        test_eng.flush()

        assert correct_dummy_eng.received_commands[1].gate == Ry(angle)
        assert test_dummy_eng.received_commands[1].gate != Ry(angle)

        for fstate in ['0', '1']:
            test = test_eng.backend.get_amplitude(fstate, test_qb)
            correct = correct_eng.backend.get_amplitude(fstate, correct_qb)
            assert correct == pytest.approx(test, rel=1e-12, abs=1e-12)

        Measure | test_qb
        Measure | correct_qb
