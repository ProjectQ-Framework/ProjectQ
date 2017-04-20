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

"""
Registers a decomposition rule for global phases.

Deletes global phase gates (which can be ignored).
"""

from projectq.cengines import DecompositionRule
from projectq.meta import get_control_count
from projectq.ops import Ph


def _decompose_PhNoCtrl(cmd):
    """ Throw out global phases (no controls). """
    pass


def _recognize_PhNoCtrl(cmd):
    """ Recognize global phases (no controls). """
    return get_control_count(cmd) == 0


all_defined_decomposition_rules = [
    DecompositionRule(Ph, _decompose_PhNoCtrl, _recognize_PhNoCtrl)
]
