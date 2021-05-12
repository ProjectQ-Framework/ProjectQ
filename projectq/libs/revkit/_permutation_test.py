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
"""Tests for libs.revkit._permutation."""

import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine

from projectq.libs.revkit import PermutationOracle

# run this test only if RevKit Python module can be loaded
revkit = pytest.importorskip('revkit')


def test_basic_permutation():
    saving_backend = DummyEngine(save_commands=True)
    main_engine = MainEngine(backend=saving_backend, engine_list=[DummyEngine()])

    qubit0 = main_engine.allocate_qubit()
    qubit1 = main_engine.allocate_qubit()

    PermutationOracle([0, 2, 1, 3]) | (qubit0, qubit1)

    assert len(saving_backend.received_commands) == 5


def test_invalid_permutation():
    main_engine = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])

    qubit0 = main_engine.allocate_qubit()
    qubit1 = main_engine.allocate_qubit()

    with pytest.raises(AttributeError):
        PermutationOracle([1, 2, 3, 4]) | (qubit0, qubit1)

    with pytest.raises(AttributeError):
        PermutationOracle([0, 2, 3, 4]) | (qubit0, qubit1)

    with pytest.raises(AttributeError):
        PermutationOracle([0, 1, 1, 2]) | (qubit0, qubit1)

    with pytest.raises(AttributeError):
        PermutationOracle([0, 1, 2]) | (qubit0, qubit1)

    with pytest.raises(AttributeError):
        PermutationOracle([0, 1, 2, 3, 4]) | (qubit0, qubit1)


def test_synthesis_with_adjusted_tbs():
    saving_backend = DummyEngine(save_commands=True)
    main_engine = MainEngine(backend=saving_backend, engine_list=[DummyEngine()])

    qubit0 = main_engine.allocate_qubit()
    qubit1 = main_engine.allocate_qubit()

    def synth():
        import revkit

        return revkit.tbs()

    PermutationOracle([0, 2, 1, 3], synth=synth) | (qubit0, qubit1)

    assert len(saving_backend.received_commands) == 5


def test_synthesis_with_synthesis_script():
    saving_backend = DummyEngine(save_commands=True)
    main_engine = MainEngine(backend=saving_backend, engine_list=[DummyEngine()])

    qubit0 = main_engine.allocate_qubit()
    qubit1 = main_engine.allocate_qubit()

    def synth():
        import revkit

        revkit.tbs()

    PermutationOracle([0, 2, 1, 3], synth=synth) | (qubit0, qubit1)

    assert len(saving_backend.received_commands) == 5
