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

"Tests for projectq.setups.trapped_ion_decomposer.py."

import projectq
from projectq.ops import Rx, Ry, Rz, H, X, CNOT, Measure, Rxx, ClassicalInstructionGate
from projectq.cengines import (
    MainEngine,
    DummyEngine,
    AutoReplacer,
    TagRemover,
    InstructionFilter,
    DecompositionRuleSet,
    DecompositionRule,
)
from projectq.meta import get_control_count

from . import restrictedgateset
from .trapped_ion_decomposer import chooser_Ry_reducer, get_engine_list


def filter_gates(eng, cmd):
    if isinstance(cmd.gate, ClassicalInstructionGate):
        return True
    if (cmd.gate == X and get_control_count(cmd) == 1) or cmd.gate == H or isinstance(cmd.gate, Rz):
        return False
    return True


def test_chooser_Ry_reducer_synthetic():
    backend = DummyEngine(save_commands=True)
    rule_set = DecompositionRuleSet(modules=[projectq.libs.math, projectq.setups.decompositions])

    engine_list = [
        AutoReplacer(rule_set, chooser_Ry_reducer),
        TagRemover(),
        InstructionFilter(filter_gates),
    ]

    eng = MainEngine(backend=backend, engine_list=engine_list)
    control = eng.allocate_qubit()
    target = eng.allocate_qubit()
    CNOT | (control, target)
    CNOT | (control, target)
    eng.flush()
    idx0 = len(backend.received_commands) - 2
    idx1 = len(backend.received_commands)
    CNOT | (control, target)
    eng.flush()

    assert isinstance(backend.received_commands[idx0].gate, Ry)
    assert isinstance(backend.received_commands[idx1].gate, Ry)
    assert backend.received_commands[idx0].gate.get_inverse() == backend.received_commands[idx1].gate

    eng = MainEngine(backend=backend, engine_list=engine_list)
    control = eng.allocate_qubit()
    target = eng.allocate_qubit()
    H | target
    eng.flush()
    idx0 = len(backend.received_commands) - 2
    idx1 = len(backend.received_commands)
    H | target
    eng.flush()

    assert isinstance(backend.received_commands[idx0].gate, Ry)
    assert isinstance(backend.received_commands[idx1].gate, Ry)
    assert backend.received_commands[idx0].gate.get_inverse() == backend.received_commands[idx1].gate

    eng = MainEngine(backend=backend, engine_list=engine_list)
    control = eng.allocate_qubit()
    target = eng.allocate_qubit()
    Rz(1.23456) | target
    eng.flush()
    idx0 = len(backend.received_commands) - 2
    idx1 = len(backend.received_commands)
    Rz(1.23456) | target
    eng.flush()

    assert isinstance(backend.received_commands[idx0].gate, Ry)
    assert isinstance(backend.received_commands[idx1].gate, Ry)
    assert backend.received_commands[idx0].gate.get_inverse() == backend.received_commands[idx1].gate


def _dummy_h2nothing_A(cmd):
    qubit = cmd.qubits[0]
    Ry(1.23456) | qubit


def test_chooser_Ry_reducer_unsupported_gate():
    backend = DummyEngine(save_commands=True)
    rule_set = DecompositionRuleSet(rules=[DecompositionRule(H.__class__, _dummy_h2nothing_A)])

    engine_list = [
        AutoReplacer(rule_set, chooser_Ry_reducer),
        TagRemover(),
        InstructionFilter(filter_gates),
    ]

    eng = MainEngine(backend=backend, engine_list=engine_list)
    qubit = eng.allocate_qubit()
    H | qubit
    eng.flush()

    for cmd in backend.received_commands:
        print(cmd)

    assert isinstance(backend.received_commands[1].gate, Ry)


def test_chooser_Ry_reducer():
    # Without the chooser_Ry_reducer function, i.e. if the restricted gate set
    # just picked the first option in each decomposition list, the circuit
    # below would be decomposed into 8 single qubit gates and 1 two qubit
    # gate.
    #
    # Including the Allocate, Measure and Flush commands, this would result in
    # 13 commands.
    #
    # Using the chooser_Rx_reducer you get 10 commands, since you now have 4
    # single qubit gates and 1 two qubit gate.

    for engine_list, count in [
        (
            restrictedgateset.get_engine_list(one_qubit_gates=(Rx, Ry), two_qubit_gates=(Rxx,)),
            13,
        ),
        (get_engine_list(), 11),
    ]:

        backend = DummyEngine(save_commands=True)
        eng = projectq.MainEngine(backend, engine_list, verbose=True)
        qubit1 = eng.allocate_qubit()
        qubit2 = eng.allocate_qubit()
        H | qubit1
        CNOT | (qubit1, qubit2)
        Rz(0.2) | qubit1
        Measure | qubit1
        eng.flush()

        assert len(backend.received_commands) == count
