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

"""
Defines the default setup which provides an `engine_list` for the `MainEngine`

It contains `LocalOptimizers` and an `AutoReplacer` which uses most of the
decompositions rules defined in projectq.setups.decompositions
"""

import projectq
import projectq.setups.decompositions
from projectq.cengines import (TagRemover,
                               LocalOptimizer,
                               AutoReplacer,
                               DecompositionRuleSet)


def get_engine_list():
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    return [TagRemover(),
            LocalOptimizer(10),
            AutoReplacer(rule_set),
            TagRemover(),
            LocalOptimizer(10)]
