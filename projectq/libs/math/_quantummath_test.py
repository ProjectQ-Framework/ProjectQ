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

import pytest

from projectq import MainEngine
from projectq.cengines import (InstructionFilter,
                               AutoReplacer,
                               DecompositionRuleSet)
from projectq.backends import Simulator
from projectq.ops import (All, BasicMathGate, ClassicalInstructionGate,
                          Measure, X)

import projectq.libs.math
from projectq.setups.decompositions import qft2crandhadamard, swap2cnot
from projectq.libs.math import (AddQuantum,
                                SubtractQuantum,)

def init(engine, quint, value):
    for i in range(len(quint)):
        if ((value >> i) & 1) == 1:
            X | quint[i]

def no_math_emulation(eng, cmd):
    if isinstance(cmd.gate, BasicMathGate):
        return False
    if isinstance(cmd.gate, ClassicalInstructionGate):
        return True
    try:
        return len(cmd.gate.matrix) == 2
    except:
        return False

rule_set = DecompositionRuleSet(modules=[projectq.libs.math, swap2cnot])

def test_quantum_adder():
    sim = Simulator()
    eng = MainEngine(sim, [AutoReplacer(rule_set),
                           InstructionFilter(no_math_emulation)])

    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    c = eng.allocate_qubit()
    init(eng, qureg_a, 2)
    init(eng, qureg_b, 1)
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0],qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([1,0,0,0],qureg_b))

    AddQuantum() | (qureg_a, qureg_b, c) 
    
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0],qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([1,1,0,0],qureg_b))

    init(eng, qureg_a, 2) #reset
    init(eng, qureg_b, 3) #reset
    
    init(eng,qureg_a, 15)
    init(eng,qureg_b, 15)

    AddQuantum() | (qureg_a, qureg_b, c)
    
    assert 1. == pytest.approx(eng.backend.get_probability([1,1,1,1],qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,1,1],qureg_b))
    assert 1. == pytest.approx(eng.backend.get_probability([1],c))

    All(Measure) | qureg_a
    All(Measure) | qureg_b
    Measure | c

def test_quantum_adder():
    sim = Simulator()
    eng = MainEngine(sim, [AutoReplacer(rule_set),
                           InstructionFilter(no_math_emulation)])
    qureg_a = eng.allocate_qureg(4)
    qureg_b = eng.allocate_qureg(4)
    c = eng.allocate_qubit()
    init(eng, qureg_a, 2)
    init(eng, qureg_b, 1)
    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0],qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([1,0,0,0],qureg_b))

    AddQuantum() | (qureg_a, qureg_b, c)

    assert 1. == pytest.approx(eng.backend.get_probability([0,1,0,0],qureg_a))
    assert 1. == pytest.approx(eng.backend.get_probability([1,1,0,0],qureg_b))
