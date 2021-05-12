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
"""Tests for libs.revkit._phase."""

import pytest

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import DummyEngine
from projectq.ops import All, H, Measure

from projectq.libs.revkit import PhaseOracle

import numpy as np

# run this test only if RevKit Python module can be loaded
revkit = pytest.importorskip('revkit')


def test_phase_majority():
    sim = Simulator()
    main_engine = MainEngine(sim)

    qureg = main_engine.allocate_qureg(3)
    All(H) | qureg
    PhaseOracle(0xE8) | qureg

    main_engine.flush()

    assert np.array_equal(np.sign(sim.cheat()[1]), [1.0, 1.0, 1.0, -1.0, 1.0, -1.0, -1.0, -1.0])
    All(Measure) | qureg


def test_phase_majority_from_python():
    dormouse = pytest.importorskip('dormouse')  # noqa: F841

    def maj(a, b, c):
        return (a and b) or (a and c) or (b and c)  # pragma: no cover

    sim = Simulator()
    main_engine = MainEngine(sim)

    qureg = main_engine.allocate_qureg(3)
    All(H) | qureg
    PhaseOracle(maj) | qureg

    main_engine.flush()

    assert np.array_equal(np.sign(sim.cheat()[1]), [1.0, 1.0, 1.0, -1.0, 1.0, -1.0, -1.0, -1.0])
    All(Measure) | qureg


def test_phase_invalid_function():
    main_engine = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])

    qureg = main_engine.allocate_qureg(3)

    with pytest.raises(AttributeError):
        PhaseOracle(-42) | qureg

    with pytest.raises(AttributeError):
        PhaseOracle(0xCAFE) | qureg

    with pytest.raises(RuntimeError):
        PhaseOracle(0x8E, synth=lambda: revkit.esopbs()) | qureg
