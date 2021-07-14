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
"""Tests for projectq.libs.math._gates.py."""

from projectq.libs.math import (
    AddConstant,
    AddConstantModN,
    AddQuantum,
    ComparatorQuantum,
    DivideQuantum,
    MultiplyByConstantModN,
    MultiplyQuantum,
    SubConstant,
    SubConstantModN,
    SubtractQuantum,
)

from ._gates import (
    AddQuantumGate,
    ComparatorQuantumGate,
    DivideQuantumGate,
    MultiplyQuantumGate,
    SubtractQuantumGate,
)


def test_addconstant():
    assert AddConstant(3) == AddConstant(3)
    assert not AddConstant(3) == AddConstant(4)
    assert AddConstant(7) != AddConstant(3)
    assert str(AddConstant(3)) == "AddConstant(3)"


def test_addconstantmodn():
    assert AddConstantModN(3, 4) == AddConstantModN(3, 4)
    assert not AddConstantModN(3, 4) == AddConstantModN(4, 4)
    assert not AddConstantModN(3, 5) == AddConstantModN(3, 4)
    assert AddConstantModN(7, 4) != AddConstantModN(3, 4)
    assert AddConstantModN(3, 5) != AddConstantModN(3, 4)
    assert str(AddConstantModN(3, 4)) == "AddConstantModN(3, 4)"


def test_multiplybyconstmodn():
    assert MultiplyByConstantModN(3, 4) == MultiplyByConstantModN(3, 4)
    assert not MultiplyByConstantModN(3, 4) == MultiplyByConstantModN(4, 4)
    assert not MultiplyByConstantModN(3, 5) == MultiplyByConstantModN(3, 4)
    assert MultiplyByConstantModN(7, 4) != MultiplyByConstantModN(3, 4)
    assert MultiplyByConstantModN(3, 5) != MultiplyByConstantModN(3, 4)
    assert str(MultiplyByConstantModN(3, 4)) == "MultiplyByConstantModN(3, 4)"


def test_AddQuantum():
    assert AddQuantum == AddQuantumGate()
    assert AddQuantum != SubtractQuantum
    assert not AddQuantum == SubtractQuantum
    assert str(AddQuantum) == "AddQuantum"


def test_SubtractQuantum():
    assert SubtractQuantum == SubtractQuantumGate()
    assert SubtractQuantum != AddQuantum
    assert not SubtractQuantum == ComparatorQuantum
    assert str(SubtractQuantum) == "SubtractQuantum"


def test_Comparator():
    assert ComparatorQuantum == ComparatorQuantumGate()
    assert ComparatorQuantum != AddQuantum
    assert not ComparatorQuantum == AddQuantum
    assert str(ComparatorQuantum) == "Comparator"


def test_QuantumDivision():
    assert DivideQuantum == DivideQuantumGate()
    assert DivideQuantum != MultiplyQuantum
    assert not DivideQuantum == MultiplyQuantum
    assert str(DivideQuantum) == "DivideQuantum"


def test_QuantumMultiplication():
    assert MultiplyQuantum == MultiplyQuantumGate()
    assert MultiplyQuantum != DivideQuantum
    assert not MultiplyQuantum == DivideQuantum
    assert str(MultiplyQuantum) == "MultiplyQuantum"


def test_hash_function_implemented():
    assert hash(AddConstant(3)) == hash(str(AddConstant(3)))
    assert hash(SubConstant(-3)) == hash(str(AddConstant(3)))
    assert hash(AddConstantModN(7, 4)) == hash(str(AddConstantModN(7, 4)))
    assert hash(SubConstantModN(7, 4)) == hash(str(AddConstantModN(-3, 4)))
    assert hash(MultiplyByConstantModN(3, 5)) == hash(str(MultiplyByConstantModN(3, 5)))
    assert hash(AddQuantum) == hash(str(AddQuantum))
    assert hash(SubtractQuantum) == hash(str(SubtractQuantum))
    assert hash(ComparatorQuantum) == hash(str(ComparatorQuantum))
    assert hash(DivideQuantum) == hash(str(DivideQuantum))
    assert hash(MultiplyQuantum) == hash(str(MultiplyQuantum))
