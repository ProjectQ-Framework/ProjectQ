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
"""Tests for libs.revkit._control_function."""

import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine

from projectq.libs.revkit import ControlFunctionOracle

# run this test only if RevKit Python module can be loaded
revkit = pytest.importorskip('revkit')


def test_control_function_majority():
    saving_backend = DummyEngine(save_commands=True)
    main_engine = MainEngine(backend=saving_backend, engine_list=[DummyEngine()])

    qubit0 = main_engine.allocate_qubit()
    qubit1 = main_engine.allocate_qubit()
    qubit2 = main_engine.allocate_qubit()
    qubit3 = main_engine.allocate_qubit()

    ControlFunctionOracle(0xE8) | (qubit0, qubit1, qubit2, qubit3)

    assert len(saving_backend.received_commands) == 7


def test_control_function_majority_from_python():
    dormouse = pytest.importorskip('dormouse')  # noqa: F841

    def maj(a, b, c):
        return (a and b) or (a and c) or (b and c)  # pragma: no cover

    saving_backend = DummyEngine(save_commands=True)
    main_engine = MainEngine(backend=saving_backend, engine_list=[DummyEngine()])

    qubit0 = main_engine.allocate_qubit()
    qubit1 = main_engine.allocate_qubit()
    qubit2 = main_engine.allocate_qubit()
    qubit3 = main_engine.allocate_qubit()

    ControlFunctionOracle(maj) | (qubit0, qubit1, qubit2, qubit3)


def test_control_function_invalid_function():
    main_engine = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])

    qureg = main_engine.allocate_qureg(3)

    with pytest.raises(AttributeError):
        ControlFunctionOracle(-42) | qureg

    with pytest.raises(AttributeError):
        ControlFunctionOracle(0x8E) | qureg

    with pytest.raises(RuntimeError):
        ControlFunctionOracle(0x8, synth=revkit.esopps) | qureg
