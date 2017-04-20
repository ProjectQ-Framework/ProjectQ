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

"""Tests for projectq.cengines._replacer._decomposition_rule.py."""

import pytest

from projectq.ops import BasicRotationGate
from . import DecompositionRule, ThisIsNotAGateClassError


def test_decomposition_rule_wrong_input():
    class WrongInput(BasicRotationGate):
        pass

    with pytest.raises(ThisIsNotAGateClassError):
        _ = DecompositionRule(WrongInput.__class__,
                              lambda cmd: None,
                              lambda cmd: None)

    with pytest.raises(ThisIsNotAGateClassError):
        _ = DecompositionRule(WrongInput(0),
                              lambda cmd: None,
                              lambda cmd: None)
