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
"""Tests for projectq.meta._logicalqubit.py."""

from copy import deepcopy

from projectq.meta import ComputeTag, _logicalqubit


def test_logical_qubit_id_tag():
    tag0 = _logicalqubit.LogicalQubitIDTag(10)
    tag1 = _logicalqubit.LogicalQubitIDTag(1)
    tag2 = tag0
    tag3 = deepcopy(tag0)
    tag3.logical_qubit_id = 9
    other_tag = ComputeTag()
    assert tag0 == tag2
    assert tag0 != tag1
    assert not tag0 == tag3
    assert not tag0 == other_tag
