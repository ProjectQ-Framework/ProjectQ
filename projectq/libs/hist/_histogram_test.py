# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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
import matplotlib
import matplotlib.pyplot as plt  # noqa: F401

from projectq import MainEngine
from projectq.ops import H, C, X, Measure, All, AllocateQubitGate, FlushGate
from projectq.cengines import DummyEngine, BasicEngine
from projectq.backends import Simulator
from projectq.libs.hist import histogram


@pytest.fixture(scope="module")
def matplotlib_setup():
    old_backend = matplotlib.get_backend()
    matplotlib.use('agg')  # avoid showing the histogram plots
    yield
    matplotlib.use(old_backend)


def test_invalid_backend(matplotlib_setup):
    eng = MainEngine(backend=DummyEngine())
    qubit = eng.allocate_qubit()
    eng.flush()

    with pytest.raises(RuntimeError):
        histogram(eng.backend, qubit)


def test_backend_get_probabilities_method(matplotlib_setup):
    class MyBackend(BasicEngine):
        def get_probabilities(self, qureg):
            return {'000': 0.5, '111': 0.5}

        def is_available(self, cmd):
            return True

        def receive(self, command_list):
            for cmd in command_list:
                if not isinstance(cmd.gate, FlushGate):
                    assert isinstance(cmd.gate, AllocateQubitGate)

    eng = MainEngine(backend=MyBackend(), verbose=True)
    qureg = eng.allocate_qureg(3)
    eng.flush()
    _, _, prob = histogram(eng.backend, qureg)
    assert prob['000'] == 0.5
    assert prob['111'] == 0.5

    # NB: avoid throwing exceptions when destroying the MainEngine
    eng.next_engine = DummyEngine()
    eng.next_engine.is_last_engine = True


def test_qubit(matplotlib_setup):
    sim = Simulator()
    eng = MainEngine(sim)
    qubit = eng.allocate_qubit()
    eng.flush()
    _, _, prob = histogram(sim, qubit)
    assert prob["0"] == pytest.approx(1)
    assert prob["1"] == pytest.approx(0)
    H | qubit
    eng.flush()
    _, _, prob = histogram(sim, qubit)
    assert prob["0"] == pytest.approx(0.5)
    Measure | qubit
    eng.flush()
    _, _, prob = histogram(sim, qubit)
    assert prob["0"] == pytest.approx(1) or prob["1"] == pytest.approx(1)


def test_qureg(matplotlib_setup):
    sim = Simulator()
    eng = MainEngine(sim)
    qureg = eng.allocate_qureg(3)
    eng.flush()
    _, _, prob = histogram(sim, qureg)
    assert prob["000"] == pytest.approx(1)
    assert prob["110"] == pytest.approx(0)
    H | qureg[0]
    C(X, 1) | (qureg[0], qureg[1])
    H | qureg[2]
    eng.flush()
    _, _, prob = histogram(sim, qureg)
    assert prob["110"] == pytest.approx(0.25)
    assert prob["100"] == pytest.approx(0)
    All(Measure) | qureg
    eng.flush()
    _, _, prob = histogram(sim, qureg)
    assert (
        prob["000"] == pytest.approx(1)
        or prob["001"] == pytest.approx(1)
        or prob["110"] == pytest.approx(1)
        or prob["111"] == pytest.approx(1)
    )
    assert prob["000"] + prob["001"] + prob["110"] + prob["111"] == pytest.approx(1)


def test_combination(matplotlib_setup):
    sim = Simulator()
    eng = MainEngine(sim)
    qureg = eng.allocate_qureg(2)
    qubit = eng.allocate_qubit()
    eng.flush()
    _, _, prob = histogram(sim, [qureg, qubit])
    assert prob["000"] == pytest.approx(1)
    H | qureg[0]
    C(X, 1) | (qureg[0], qureg[1])
    H | qubit
    Measure | qureg[0]
    eng.flush()
    _, _, prob = histogram(sim, [qureg, qubit])
    assert (prob["000"] == pytest.approx(0.5) and prob["001"] == pytest.approx(0.5)) or (
        prob["110"] == pytest.approx(0.5) and prob["111"] == pytest.approx(0.5)
    )
    assert prob["100"] == pytest.approx(0)
    Measure | qubit


def test_too_many_qubits(matplotlib_setup, capsys):
    sim = Simulator()
    eng = MainEngine(sim)
    qureg = eng.allocate_qureg(6)
    eng.flush()
    l_ref = len(capsys.readouterr().out)
    _, _, prob = histogram(sim, qureg)
    assert len(capsys.readouterr().out) > l_ref
    assert prob["000000"] == pytest.approx(1)
    All(Measure)
