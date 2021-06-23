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
"""Tests for projectq.cengines._swapandcnotflipper.py."""

import pytest

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import All, H, CNOT, X, Swap, Command
from projectq.meta import Control, Compute, Uncompute, ComputeTag, UncomputeTag
from projectq.types import WeakQubitRef

from . import _swapandcnotflipper


def test_swapandcnotflipper_missing_connection():
    flipper = _swapandcnotflipper.SwapAndCNOTFlipper(set())
    eng = MainEngine(DummyEngine(save_commands=True), [flipper])
    qubit1, qubit2 = eng.allocate_qureg(2)
    with pytest.raises(RuntimeError):
        Swap | (qubit1, qubit2)


def test_swapandcnotflipper_invalid_swap():
    flipper = _swapandcnotflipper.SwapAndCNOTFlipper(set())

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    with pytest.raises(RuntimeError):
        flipper.receive([Command(engine=None, gate=Swap, qubits=([qb0, qb1], [qb2]))])


def test_swapandcnotflipper_is_available():
    flipper = _swapandcnotflipper.SwapAndCNOTFlipper(set())
    dummy = DummyEngine()
    dummy.is_available = lambda x: False
    flipper.next_engine = dummy
    eng = MainEngine(DummyEngine(save_commands=True), [])
    qubit1, qubit2 = eng.allocate_qureg(2)
    Swap | (qubit1, qubit2)
    swap_count = 0
    for cmd in eng.backend.received_commands:
        if cmd.gate == Swap:
            swap_count += 1
            assert flipper.is_available(cmd)
    assert swap_count == 1

    eng = MainEngine(DummyEngine(save_commands=True), [])
    qubit1, qubit2, qubit3 = eng.allocate_qureg(3)
    with Control(eng, qubit3):
        Swap | (qubit1, qubit2)
    swap_count = 0
    for cmd in eng.backend.received_commands:
        if cmd.gate == Swap:
            swap_count += 1
            assert not flipper.is_available(cmd)
    assert swap_count == 1


def test_swapandcnotflipper_flips_cnot():
    backend = DummyEngine(save_commands=True)
    connectivity = set([(0, 1)])
    flipper = _swapandcnotflipper.SwapAndCNOTFlipper(connectivity)
    eng = MainEngine(backend=backend, engine_list=[flipper])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    CNOT | (qb0, qb1)
    CNOT | (qb1, qb0)
    hgates = 0
    for cmd in backend.received_commands:
        if cmd.gate == H:
            hgates += 1
        if cmd.gate == X:
            assert cmd.qubits[0][0].id == 1
            assert cmd.control_qubits[0].id == 0
    assert hgates == 4


def test_swapandcnotflipper_invalid_circuit():
    backend = DummyEngine(save_commands=True)
    connectivity = set([(0, 2)])
    flipper = _swapandcnotflipper.SwapAndCNOTFlipper(connectivity)
    eng = MainEngine(backend=backend, engine_list=[flipper])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    qb2 = eng.allocate_qubit()
    CNOT | (qb0, qb2)
    CNOT | (qb2, qb0)
    with pytest.raises(RuntimeError):
        CNOT | (qb0, qb1)
    with pytest.raises(RuntimeError):
        Swap | (qb0, qb1)


def test_swapandcnotflipper_optimize_swaps():
    backend = DummyEngine(save_commands=True)
    connectivity = set([(1, 0)])
    flipper = _swapandcnotflipper.SwapAndCNOTFlipper(connectivity)
    eng = MainEngine(backend=backend, engine_list=[flipper])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Swap | (qb0, qb1)
    hgates = 0
    for cmd in backend.received_commands:
        if cmd.gate == H:
            hgates += 1
        if cmd.gate == X:
            assert cmd.qubits[0][0].id == 0
            assert cmd.control_qubits[0].id == 1
    assert hgates == 4

    backend = DummyEngine(save_commands=True)
    connectivity = set([(0, 1)])
    flipper = _swapandcnotflipper.SwapAndCNOTFlipper(connectivity)
    eng = MainEngine(backend=backend, engine_list=[flipper])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    Swap | (qb0, qb1)
    hgates = 0
    for cmd in backend.received_commands:
        if cmd.gate == H:
            hgates += 1
        if cmd.gate == X:
            assert cmd.qubits[0][0].id == 1
            assert cmd.control_qubits[0].id == 0
    assert hgates == 4


def test_swapandcnotflipper_keeps_tags():
    backend = DummyEngine(save_commands=True)
    connectivity = set([(1, 0)])
    flipper = _swapandcnotflipper.SwapAndCNOTFlipper(connectivity)
    eng = MainEngine(backend=backend, engine_list=[flipper])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    with Compute(eng):
        All(H) | (qb0 + qb1)
        CNOT | (qb0, qb1)
        CNOT | (qb1, qb0)
        Swap | (qb0, qb1)
    Uncompute(eng)
    hgates = 0
    for cmd in backend.received_commands:
        if cmd.gate == H:
            for t in cmd.tags:
                if isinstance(t, (ComputeTag, UncomputeTag)):
                    hgates += 1
                    break
    assert hgates == 20
