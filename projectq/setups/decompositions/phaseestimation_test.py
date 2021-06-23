# -*- coding: utf-8 -*-
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

import cmath
import numpy as np
from flaky import flaky
import pytest

from projectq.backends import Simulator
from projectq.cengines import (
    AutoReplacer,
    DecompositionRuleSet,
    MainEngine,
)

from projectq.ops import X, H, All, Measure, Tensor, Ph, CNOT, StatePreparation, QPE

from projectq.setups.decompositions import phaseestimation as pe
from projectq.setups.decompositions import qft2crandhadamard as dqft
import projectq.setups.decompositions.stateprep2cnot as stateprep2cnot
import projectq.setups.decompositions.uniformlycontrolledr2cnot as ucr2cnot


@flaky(max_runs=5, min_passes=2)
def test_simple_test_X_eigenvectors():
    rule_set = DecompositionRuleSet(modules=[pe, dqft])
    eng = MainEngine(
        backend=Simulator(),
        engine_list=[
            AutoReplacer(rule_set),
        ],
    )
    results = np.array([])
    for i in range(150):
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
        phase = faseint / (2.0 ** (len(ancillas)))
        results = np.append(results, phase)
        All(Measure) | autovector
        eng.flush()

    num_phase = (results == 0.5).sum()
    assert num_phase / 100.0 >= 0.35, "Statistics phase calculation are not correct (%f vs. %f)" % (
        num_phase / 100.0,
        0.35,
    )


@flaky(max_runs=5, min_passes=2)
def test_Ph_eigenvectors():
    rule_set = DecompositionRuleSet(modules=[pe, dqft])
    eng = MainEngine(
        backend=Simulator(),
        engine_list=[
            AutoReplacer(rule_set),
        ],
    )
    results = np.array([])
    for i in range(150):
        autovector = eng.allocate_qureg(1)
        theta = cmath.pi * 2.0 * 0.125
        unit = Ph(theta)
        ancillas = eng.allocate_qureg(3)
        QPE(unit) | (ancillas, autovector)
        All(Measure) | ancillas
        fasebinlist = [int(q) for q in ancillas]
        fasebin = ''.join(str(j) for j in fasebinlist)
        faseint = int(fasebin, 2)
        phase = faseint / (2.0 ** (len(ancillas)))
        results = np.append(results, phase)
        All(Measure) | autovector
        eng.flush()

    num_phase = (results == 0.125).sum()
    assert num_phase / 100.0 >= 0.35, "Statistics phase calculation are not correct (%f vs. %f)" % (
        num_phase / 100.0,
        0.35,
    )


def two_qubit_gate(system_q, time):
    CNOT | (system_q[0], system_q[1])
    Ph(2.0 * cmath.pi * (time * 0.125)) | system_q[1]
    CNOT | (system_q[0], system_q[1])


@flaky(max_runs=5, min_passes=2)
def test_2qubitsPh_andfunction_eigenvectors():
    rule_set = DecompositionRuleSet(modules=[pe, dqft])
    eng = MainEngine(
        backend=Simulator(),
        engine_list=[
            AutoReplacer(rule_set),
        ],
    )
    results = np.array([])
    for i in range(150):
        autovector = eng.allocate_qureg(2)
        X | autovector[0]
        ancillas = eng.allocate_qureg(3)
        QPE(two_qubit_gate) | (ancillas, autovector)
        All(Measure) | ancillas
        fasebinlist = [int(q) for q in ancillas]
        fasebin = ''.join(str(j) for j in fasebinlist)
        faseint = int(fasebin, 2)
        phase = faseint / (2.0 ** (len(ancillas)))
        results = np.append(results, phase)
        All(Measure) | autovector
        eng.flush()

    num_phase = (results == 0.125).sum()
    assert num_phase / 100.0 >= 0.34, "Statistics phase calculation are not correct (%f vs. %f)" % (
        num_phase / 100.0,
        0.34,
    )


def test_X_no_eigenvectors():
    rule_set = DecompositionRuleSet(modules=[pe, dqft, stateprep2cnot, ucr2cnot])
    eng = MainEngine(
        backend=Simulator(),
        engine_list=[
            AutoReplacer(rule_set),
        ],
    )
    results = np.array([])
    results_plus = np.array([])
    results_minus = np.array([])
    for i in range(100):
        autovector = eng.allocate_qureg(1)
        amplitude0 = (np.sqrt(2) + np.sqrt(6)) / 4.0
        amplitude1 = (np.sqrt(2) - np.sqrt(6)) / 4.0
        StatePreparation([amplitude0, amplitude1]) | autovector
        unit = X
        ancillas = eng.allocate_qureg(1)
        QPE(unit) | (ancillas, autovector)
        All(Measure) | ancillas
        fasebinlist = [int(q) for q in ancillas]
        fasebin = ''.join(str(j) for j in fasebinlist)
        faseint = int(fasebin, 2)
        phase = faseint / (2.0 ** (len(ancillas)))
        results = np.append(results, phase)
        Tensor(H) | autovector
        if np.allclose(phase, 0.0, rtol=1e-1):
            results_plus = np.append(results_plus, phase)
            All(Measure) | autovector
            autovector_result = int(autovector)
            assert autovector_result == 0
        elif np.allclose(phase, 0.5, rtol=1e-1):
            results_minus = np.append(results_minus, phase)
            All(Measure) | autovector
            autovector_result = int(autovector)
            assert autovector_result == 1
        eng.flush()

    total = len(results_plus) + len(results_minus)
    plus_probability = len(results_plus) / 100.0
    assert total == pytest.approx(100, abs=5)
    assert plus_probability == pytest.approx(
        1.0 / 4.0, abs=1e-1
    ), "Statistics on |+> probability are not correct (%f vs. %f)" % (
        plus_probability,
        1.0 / 4.0,
    )


def test_string():
    unit = X
    gate = QPE(unit)
    assert str(gate) == "QPE(X)"
