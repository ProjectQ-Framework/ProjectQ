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

"""Tests for projectq.libs.math_constantmath.py."""

import pytest

from projectq import MainEngine
from projectq.cengines import InstructionFilter, AutoReplacer
from projectq.backends import Simulator
from projectq.ops import X, BasicMathGate, ClassicalInstructionGate, Measure

from projectq.libs.math import (AddConstant,
                                AddConstantModN,
                                MultiplyByConstantModN)


def init(engine, quint, value):
	for i in range(len(quint)):
		if ((value >> i)&1) == 1:
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


def test_adder():
	sim = Simulator()
	eng = MainEngine(sim, [AutoReplacer(),
	                       InstructionFilter(no_math_emulation)])
	qureg = eng.allocate_qureg(4)
	init(eng, qureg, 4)
	
	AddConstant(3) | qureg
	
	assert 1. == pytest.approx(abs(sim.cheat()[1][7]))
	
	init(eng, qureg, 7)  # reset
	init(eng, qureg, 2)
	
	AddConstant(15) | qureg  # check for overflow -> should be 15+2 = 1 (mod 16)
	assert 1. == pytest.approx(abs(sim.cheat()[1][1]))
	
	Measure | qureg


def test_modadder():
	sim = Simulator()
	eng = MainEngine(sim, [AutoReplacer(),
	                       InstructionFilter(no_math_emulation)])
	
	qureg = eng.allocate_qureg(4)
	init(eng, qureg, 4)
	
	AddConstantModN(3, 6) | qureg
	
	assert 1. == pytest.approx(abs(sim.cheat()[1][1]))
	
	init(eng, qureg, 1)  # reset
	init(eng, qureg, 7)
	
	AddConstantModN(10, 13) | qureg
	assert 1. == pytest.approx(abs(sim.cheat()[1][4]))
	
	Measure | qureg


def test_modmultiplier():
	sim = Simulator()
	eng = MainEngine(sim, [AutoReplacer(),
	                       InstructionFilter(no_math_emulation)])
	
	qureg = eng.allocate_qureg(4)
	init(eng, qureg, 4)
	
	MultiplyByConstantModN(3, 7) | qureg
	
	assert 1. == pytest.approx(abs(sim.cheat()[1][5]))
	
	init(eng, qureg, 5)  # reset
	init(eng, qureg, 7)
	
	MultiplyByConstantModN(4, 13) | qureg
	assert 1. == pytest.approx(abs(sim.cheat()[1][2]))
	
	Measure | qureg
