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
"""Tests for projectq.ops._state_prep."""

from projectq.ops import _state_prep, X


def test_equality_and_hash():
    gate1 = _state_prep.StatePreparation([0.5, -0.5, 0.5, -0.5])
    gate2 = _state_prep.StatePreparation([0.5, -0.5, 0.5, -0.5])
    gate3 = _state_prep.StatePreparation([0.5, -0.5, 0.5, 0.5])
    assert gate1 == gate2
    assert hash(gate1) == hash(gate2)
    assert gate1 != gate3
    assert gate1 != X


def test_str():
    gate1 = _state_prep.StatePreparation([0, 1])
    assert str(gate1) == "StatePreparation"
