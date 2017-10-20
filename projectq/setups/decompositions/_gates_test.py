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

"""
Tests for decompositions rules (using the Simulator).
"""

import pytest

from projectq.cengines import (MainEngine,
                               InstructionFilter,
                               AutoReplacer,
                               DummyEngine,
                               DecompositionRuleSet)
from projectq.backends import Simulator
from projectq.ops import (H,
                          CRz,
                          Rz,
                          T,
                          Tdag,
                          X,
                          Toffoli,
                          Entangle,
                          R,
                          Ph,
                          ClassicalInstructionGate,
                          All,
                          Measure)
from projectq.meta import Control
from projectq.setups.decompositions import (entangle,
                                            globalphase,
                                            r2rzandph,
                                            crz2cxandrz,
                                            toffoli2cnotandtgate,
                                            ph2r)


def low_level_gates(eng, cmd):
    g = cmd.gate
    if isinstance(g, ClassicalInstructionGate):
        return True
    if len(cmd.control_qubits) == 0:
        if (g == T or g == Tdag or g == H or isinstance(g, Rz) or
                isinstance(g, Ph)):
            return True
    else:
        if len(cmd.control_qubits) == 1 and cmd.gate == X:
            return True
    return False


def test_entangle():
    rule_set = DecompositionRuleSet(modules=[entangle])
    sim = Simulator()
    eng = MainEngine(sim,
                     [AutoReplacer(rule_set),
                      InstructionFilter(low_level_gates)])
    qureg = eng.allocate_qureg(4)
    Entangle | qureg

    assert .5 == pytest.approx(abs(sim.cheat()[1][0])**2)
    assert .5 == pytest.approx(abs(sim.cheat()[1][-1])**2)

    Measure | qureg


def low_level_gates_noglobalphase(eng, cmd):
    return (low_level_gates(eng, cmd) and not isinstance(cmd.gate, Ph) and not
            isinstance(cmd.gate, R))


def test_globalphase():
    rule_set = DecompositionRuleSet(modules=[globalphase, r2rzandph])
    dummy = DummyEngine(save_commands=True)
    eng = MainEngine(dummy, [AutoReplacer(rule_set),
                             InstructionFilter(low_level_gates_noglobalphase)])

    qubit = eng.allocate_qubit()
    R(1.2) | qubit

    rz_count = 0
    for cmd in dummy.received_commands:
        assert not isinstance(cmd.gate, R)
        if isinstance(cmd.gate, Rz):
            rz_count += 1
            assert cmd.gate == Rz(1.2)

    assert rz_count == 1


def run_circuit(eng):
    qureg = eng.allocate_qureg(4)
    All(H) | qureg
    CRz(3.0) | (qureg[0], qureg[1])
    Toffoli | (qureg[1], qureg[2], qureg[3])

    with Control(eng, qureg[0:2]):
        Ph(1.43) | qureg[2]
    return qureg


def test_gate_decompositions():
    sim = Simulator()
    eng = MainEngine(sim, [])
    rule_set = DecompositionRuleSet(
        modules=[r2rzandph, crz2cxandrz, toffoli2cnotandtgate, ph2r])

    qureg = run_circuit(eng)

    sim2 = Simulator()
    eng_lowlevel = MainEngine(sim2, [AutoReplacer(rule_set),
                                     InstructionFilter(low_level_gates)])
    qureg2 = run_circuit(eng_lowlevel)

    for i in range(len(sim.cheat()[1])):
        assert sim.cheat()[1][i] == pytest.approx(sim2.cheat()[1][i])

    Measure | qureg
    Measure | qureg2
