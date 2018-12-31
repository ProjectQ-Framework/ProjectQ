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

"Tests for projectq.setups.decompositions.phaseestimation.py."

import copy
import cmath
import numpy as np
import pytest

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)

from projectq.ops import X, H, All, Measure, Tensor, Ph, StatePreparation

from projectq.ops import (BasicGate)

from projectq.ops import QPE
from projectq.setups.decompositions import phaseestimation as pe
from projectq.setups.decompositions import qft2crandhadamard as dqft
import projectq.setups.decompositions.stateprep2cnot as stateprep2cnot
import projectq.setups.decompositions.uniformlycontrolledr2cnot as ucr2cnot


class PhaseX(BasicGate):
    """
    A phase gate on X gate with
    eigenvectors H|0> and HX|0> and
    eivenvalues exp(i2pi theta) and -exp(i2pi theta)
    """

    def __init__(self, phase):
        BasicGate.__init__(self)
        self.phase = phase

    @property
    def matrix(self):
        theta = self.phase

        return np.matrix([[0, cmath.exp(1j * 2.0 * cmath.pi * theta)],
                         [cmath.exp(1j * 2.0 * cmath.pi * theta), 0]])


class PhaseXxX(BasicGate):
    """
    A phase gate on X (x) X : PhX(x)X gate with
    eigenvectors: |+>|+>, |+>|->,|->|+>,|->|->,  and
    eivenvalues exp(i2pi theta) and -exp(i2pi theta)
    """

    def __init__(self, phase):
        BasicGate.__init__(self)
        self.phase = phase

    @property
    def matrix(self):
        theta = self.phase

        return np.matrix([[0, 0, 0, cmath.exp(1j * 2.0 * cmath.pi * theta)],
                         [0, 0, cmath.exp(1j * 2.0 * cmath.pi * theta), 0],
                         [0, cmath.exp(1j * 2.0 * cmath.pi * theta), 0, 0],
                         [cmath.exp(1j * 2.0 * cmath.pi * theta), 0, 0, 0]])


def test_simple_test_X_eigenvectors():
    rule_set = DecompositionRuleSet(modules=[pe, dqft])
    eng = MainEngine(backend=Simulator(),
                     engine_list=[AutoReplacer(rule_set),
                                  ])
    results = np.array([])
    for i in range(10):
        autovector = eng.allocate_qureg(1)
        X | autovector
        H | autovector
        unit = X
        ancillas = eng.allocate_qureg(1)
        QPE(unit) | (ancillas, autovector)
        All(Measure) | ancillas
        fasebinlist = [int(q) for q in ancillas]
        fasebin = ''.join(str(j) for j in fasebinlist)
        faseint = int(fasebin, 2)
        phase = faseint / (2. ** (len(ancillas)))
        results = np.append(results, phase)
        All(Measure) | autovector
        eng.flush()

    perc_95 = np.percentile(results, 95)
    assert perc_95 == 0.5


def test_phaseX_eigenvectors_minus():
    rule_set = DecompositionRuleSet(modules=[pe, dqft])
    eng = MainEngine(backend=Simulator(),
                     engine_list=[AutoReplacer(rule_set),
                                  ])
    results = np.array([])
    for i in range(10):
        autovector = eng.allocate_qureg(1)
        X | autovector
        H | autovector
        theta = .15625
        unit = PhaseX(theta)
        ancillas = eng.allocate_qureg(5)
        QPE(unit) | (ancillas, autovector)
        All(Measure) | ancillas
        fasebinlist = [int(q) for q in ancillas]
        fasebin = ''.join(str(j) for j in fasebinlist)
        faseint = int(fasebin, 2)
        phase = faseint / (2. ** (len(ancillas)))
        results = np.append(results, phase)
        All(Measure) | autovector
        eng.flush()

    perc_75 = np.percentile(results, 75)
    assert perc_75 == pytest.approx(.65625, abs=1e-2), "Percentile 75 not as expected (%f)" % (perc_75)


def test_phaseXxX_eigenvectors_minusplus():
    rule_set = DecompositionRuleSet(modules=[pe, dqft])
    eng = MainEngine(backend=Simulator(),
                     engine_list=[AutoReplacer(rule_set),
                                  ])
    results = np.array([])
    for i in range(10):
        autovector = eng.allocate_qureg(2)
        X | autovector[0]
        Tensor(H) | autovector
        theta = .15625
        unit = PhaseXxX(theta)
        ancillas = eng.allocate_qureg(5)
        QPE(unit) | (ancillas, autovector)
        All(Measure) | ancillas
        fasebinlist = [int(q) for q in ancillas]
        fasebin = ''.join(str(j) for j in fasebinlist)
        faseint = int(fasebin, 2)
        phase = faseint / (2. ** (len(ancillas)))
        results = np.append(results, phase)
        All(Measure) | autovector
        eng.flush()

    perc_75 = np.percentile(results, 75)
    assert perc_75 == pytest.approx(.65625, abs=1e-2), "Percentile 75 not as expected (%f)" % (perc_75)


def test_X_no_eigenvectors():
    rule_set = DecompositionRuleSet(modules=[pe, dqft, stateprep2cnot, ucr2cnot])
    eng = MainEngine(backend=Simulator(),
                     engine_list=[AutoReplacer(rule_set),
                                  ])
    results = np.array([])
    results_plus = np.array([])
    results_minus = np.array([])
    for i in range(100):
        autovector = eng.allocate_qureg(1)
        amplitude0 = (np.sqrt(2) + np.sqrt(6))/4.
        amplitude1 = (np.sqrt(2) - np.sqrt(6))/4.
        StatePreparation([amplitude0, amplitude1]) | autovector
        unit = X
        ancillas = eng.allocate_qureg(1)
        QPE(unit) | (ancillas, autovector)
        All(Measure) | ancillas
        fasebinlist = [int(q) for q in ancillas]
        fasebin = ''.join(str(j) for j in fasebinlist)
        faseint = int(fasebin, 2)
        phase = faseint / (2. ** (len(ancillas)))
        results = np.append(results, phase)
        Tensor(H) | autovector
        if np.allclose(phase, .0, rtol=1e-1):
            results_plus = np.append(results_plus, phase)
            All(Measure) | autovector
            autovector_result = int(autovector)
            assert autovector_result == 0
        elif np.allclose(phase, .5, rtol=1e-1):
            results_minus = np.append(results_minus, phase)
            All(Measure) | autovector
            autovector_result = int(autovector)
            assert autovector_result == 1
        else:
            All(Measure) | autovector
        eng.flush()

    total = len(results_plus) + len(results_minus)
    plus_probability = len(results_plus)/100.
    assert total == pytest.approx(100, abs=5)
    assert plus_probability == pytest.approx(1./4., abs = 1e-1), "Statistics on |+> probability are not correct (%f vs. %f)" % (plus_probability, 1./4.)


def test_string():
    unit = X
    gate = QPE(unit)
    assert (str(gate) == "QPE_X")


def simplefunction(system_q, time):
    Ph(2.0*cmath.pi*(time + .75)) | system_q


def test_simplefunction_eigenvectors():
    rule_set = DecompositionRuleSet(modules=[pe, dqft])
    eng = MainEngine(backend=Simulator(),
                     engine_list=[AutoReplacer(rule_set),
                                  ])
    results = np.array([])
    for i in range(10):
        autovector = eng.allocate_qureg(1)
        ancillas = eng.allocate_qureg(2)
        QPE(simplefunction) | (ancillas, autovector)
        All(Measure) | ancillas
        fasebinlist = [int(q) for q in ancillas]
        fasebin = ''.join(str(j) for j in fasebinlist)
        faseint = int(fasebin, 2)
        phase = faseint / (2. ** (len(ancillas)))
        results = np.append(results, phase)
        All(Measure) | autovector
        eng.flush()

    perc_95 = np.percentile(results, 95)
    assert perc_95 == 0.75
