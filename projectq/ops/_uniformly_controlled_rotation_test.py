# -*- coding: utf-8 -*-
#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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
"""Tests for projectq.ops._uniformly_controlled_rotation."""
import math

import pytest

from projectq.ops import Rx
from ._basics import NotMergeable

from projectq.ops import _uniformly_controlled_rotation as ucr


@pytest.mark.parametrize("gate_class", [ucr.UniformlyControlledRy, ucr.UniformlyControlledRz])
def test_init_rounding(gate_class):
    gate = gate_class([0.1 + 4 * math.pi, -1e-14])
    assert gate.angles == [0.1, 0.0]


@pytest.mark.parametrize("gate_class", [ucr.UniformlyControlledRy, ucr.UniformlyControlledRz])
def test_get_inverse(gate_class):
    gate = gate_class([0.1, 0.2, 0.3, 0.4])
    inverse = gate.get_inverse()
    assert inverse == gate_class([-0.1, -0.2, -0.3, -0.4])


@pytest.mark.parametrize("gate_class", [ucr.UniformlyControlledRy, ucr.UniformlyControlledRz])
def test_get_merged(gate_class):
    gate1 = gate_class([0.1, 0.2, 0.3, 0.4])
    gate2 = gate_class([0.1, 0.2, 0.3, 0.4])
    merged_gate = gate1.get_merged(gate2)
    assert merged_gate == gate_class([0.2, 0.4, 0.6, 0.8])
    with pytest.raises(NotMergeable):
        gate1.get_merged(Rx(0.1))


def test_str_and_hash():
    gate1 = ucr.UniformlyControlledRy([0.1, 0.2, 0.3, 0.4])
    gate2 = ucr.UniformlyControlledRz([0.1, 0.2, 0.3, 0.4])
    assert str(gate1) == "UniformlyControlledRy([0.1, 0.2, 0.3, 0.4])"
    assert str(gate2) == "UniformlyControlledRz([0.1, 0.2, 0.3, 0.4])"
    assert hash(gate1) == hash("UniformlyControlledRy([0.1, 0.2, 0.3, 0.4])")
    assert hash(gate2) == hash("UniformlyControlledRz([0.1, 0.2, 0.3, 0.4])")


@pytest.mark.parametrize("gate_class", [ucr.UniformlyControlledRy, ucr.UniformlyControlledRz])
def test_equality(gate_class):
    gate1 = gate_class([0.1, 0.2])
    gate2 = gate_class([0.1, 0.2 + 1e-14])
    assert gate1 == gate2
    gate3 = gate_class([0.1, 0.2, 0.1, 0.2])
    assert gate2 != gate3
    gate4 = ucr.UniformlyControlledRz([0.1, 0.2])
    gate5 = ucr.UniformlyControlledRy([0.1, 0.2])
    assert gate4 != gate5
    assert not gate5 == gate4
