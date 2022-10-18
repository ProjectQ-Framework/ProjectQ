#   Copyright 2022 ProjectQ-Framework (www.projectq.ch)
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

"""Tests for projectq._utils.py."""

import pytest

from ._utils import _rearrange_result


@pytest.mark.parametrize(
    "input_result, length, expected_result",
    [
        (5, 3, '101'),
        (5, 4, '1010'),
        (5, 5, '10100'),
        (16, 5, '00001'),
        (16, 6, '000010'),
        (63, 6, '111111'),
        (63, 7, '1111110'),
    ],
)
def test_rearrange_result(input_result, length, expected_result):
    assert expected_result == _rearrange_result(input_result, length)
