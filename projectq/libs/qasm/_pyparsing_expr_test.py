# -*- coding: utf-8 -*-
#   Copyright 2021 <Huawei Technologies Co., Ltd>
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

import math

import pytest

from ._pyparsing_expr import eval_expr

# ==============================================================================


def test_eval():
    assert eval_expr('1 + 2') == 3
    assert eval_expr('1 + 2^3') == 9
    assert eval_expr('(2.2 + 1) - (2*4 + -1)') == pytest.approx((2.2 + 1) - (2 * 4 + -1))
    assert eval_expr('-1 + PI') == pytest.approx(-1 + math.pi)
    assert eval_expr('-1 + E') == pytest.approx(-1 + math.e)
    assert eval_expr('-1 + 2') == 1
    assert eval_expr('a', {'a': '2'}) == 2
    assert eval_expr('a', {'a': '2.2'}) == 2.2
    assert eval_expr('-1 + a', {'a': 2}) == 1
    assert eval_expr('-1 + a[1]', {'a': [2, 3]}) == 2
    assert eval_expr('-1 + a[1]', {'a': 2}) == 0
    assert eval_expr('-1 + a[1]', {'a': 1}) == -1
    assert eval_expr('sin(1.2)') == pytest.approx(math.sin(1.2))
    assert eval_expr('cos(1.2)') == pytest.approx(math.cos(1.2))
    assert eval_expr('tan(1.2)') == pytest.approx(math.tan(1.2))
    assert eval_expr('exp(1.2)') == pytest.approx(math.exp(1.2))
    assert eval_expr('abs(-1.2)') == pytest.approx(abs(-1.2))


# ==============================================================================
