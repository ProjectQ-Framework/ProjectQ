# -*- coding: utf-8 -*-
#   Copyright 2019 ProjectQ-Framework (www.projectq.ch)
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

"Tests for projectq.setups.decompositions.amplitudeamplification.py."

import math
import pytest

from projectq.backends import Simulator
from projectq.cengines import AutoReplacer, DecompositionRuleSet, MainEngine

from projectq.ops import X, H, Ry, All, Measure
from projectq.meta import Loop, Control, Compute, Uncompute

from projectq.ops import QAA
from projectq.setups.decompositions import amplitudeamplification as aa


def hache_algorithm(eng, qreg):
    All(H) | qreg


def simple_oracle(eng, system_q, control):
    # This oracle selects the state |1010101> as the one marked
    with Compute(eng):
        All(X) | system_q[1::2]
    with Control(eng, system_q):
        X | control
    Uncompute(eng)


def test_simple_grover():
    rule_set = DecompositionRuleSet(modules=[aa])

    eng = MainEngine(
        backend=Simulator(),
        engine_list=[
            AutoReplacer(rule_set),
        ],
    )

    system_qubits = eng.allocate_qureg(7)

    # Prepare the control qubit in the |-> state
    control = eng.allocate_qubit()
    X | control
    H | control

    # Creates the initial state form the Algorithm
    hache_algorithm(eng, system_qubits)

    # Get the amplitude of the marked state before the AA
    # to calculate the number of iterations
    eng.flush()
    prob1010101 = eng.backend.get_probability('1010101', system_qubits)

    total_amp_before = math.sqrt(prob1010101)
    theta_before = math.asin(total_amp_before)

    # Apply Quantum Amplitude Amplification the correct number of times
    # Theta is calculated previously using get_probability
    # We calculate also the theoretical final probability
    # of getting the good state
    num_it = int(math.pi / (4.0 * theta_before) + 1)
    theoretical_prob = math.sin((2 * num_it + 1.0) * theta_before) ** 2
    with Loop(eng, num_it):
        QAA(hache_algorithm, simple_oracle) | (system_qubits, control)

    # Get the probabilty of getting the marked state after the AA
    # to compare with the theoretical probability after teh AA
    eng.flush()
    prob1010101 = eng.backend.get_probability('1010101', system_qubits)
    total_prob_after = prob1010101

    All(Measure) | system_qubits
    H | control
    Measure | control

    eng.flush()

    assert total_prob_after == pytest.approx(
        theoretical_prob, abs=1e-6
    ), "The obtained probability is less than expected %f vs. %f" % (
        total_prob_after,
        theoretical_prob,
    )


def complex_algorithm(eng, qreg):
    All(H) | qreg
    with Control(eng, qreg[0]):
        All(X) | qreg[1:]
    All(Ry(math.pi / 4)) | qreg[1:]
    with Control(eng, qreg[-1]):
        All(X) | qreg[1:-1]


def complex_oracle(eng, system_q, control):
    # This oracle selects the subspace |000000>+|111111> as the good one
    with Compute(eng):
        with Control(eng, system_q[0]):
            All(X) | system_q[1:]
        H | system_q[0]
        All(X) | system_q

    with Control(eng, system_q):
        X | control

    Uncompute(eng)


def test_complex_aa():
    rule_set = DecompositionRuleSet(modules=[aa])

    eng = MainEngine(
        backend=Simulator(),
        engine_list=[
            AutoReplacer(rule_set),
        ],
    )

    system_qubits = eng.allocate_qureg(6)

    # Prepare the control qubit in the |-> state
    control = eng.allocate_qubit()
    X | control
    H | control

    # Creates the initial state form the Algorithm
    complex_algorithm(eng, system_qubits)

    # Get the probabilty of getting the marked state before the AA
    # to calculate the number of iterations
    eng.flush()
    prob000000 = eng.backend.get_probability('000000', system_qubits)
    prob111111 = eng.backend.get_probability('111111', system_qubits)

    total_amp_before = math.sqrt(prob000000 + prob111111)
    theta_before = math.asin(total_amp_before)

    # Apply Quantum Amplitude Amplification the correct number of times
    # Theta is calculated previously using get_probability
    # We calculate also the theoretical final probability
    # of getting the good state
    num_it = int(math.pi / (4.0 * theta_before) + 1)
    theoretical_prob = math.sin((2 * num_it + 1.0) * theta_before) ** 2
    with Loop(eng, num_it):
        QAA(complex_algorithm, complex_oracle) | (system_qubits, control)

    # Get the probabilty of getting the marked state after the AA
    # to compare with the theoretical probability after the AA
    eng.flush()
    prob000000 = eng.backend.get_probability('000000', system_qubits)
    prob111111 = eng.backend.get_probability('111111', system_qubits)
    total_prob_after = prob000000 + prob111111

    All(Measure) | system_qubits
    H | control
    Measure | control

    eng.flush()

    assert total_prob_after == pytest.approx(
        theoretical_prob, abs=1e-2
    ), "The obtained probability is less than expected %f vs. %f" % (
        total_prob_after,
        theoretical_prob,
    )


def test_string_functions():
    algorithm = hache_algorithm
    oracle = simple_oracle
    gate = QAA(algorithm, oracle)
    assert str(gate) == "QAA(Algorithm = hache_algorithm, Oracle = simple_oracle)"
