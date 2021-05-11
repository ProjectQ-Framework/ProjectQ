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
from projectq.meta import has_negative_control
from projectq.cengines import (TagRemover,
                               LocalOptimizer,
                               AutoReplacer,
                               DecompositionRuleSet)
from projectq.setups.decompositions.controlstate import all_defined_decomposition_rules as ctrl_rule

def ctrl_chooser(cmd,decomp_list):
    if has_negative_control(cmd):

        rule_set = DecompositionRuleSet(rules=ctrl_rule).decompositions
        decomps = []
        for gatetype in rule_set:
            decomps.append(rule_set[gatetype])

        return decomps[0][0]
    else:
        return decomp_list[0]
def get_engine_list():
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    return [TagRemover(),
            LocalOptimizer(10),
            AutoReplacer(rule_set,ctrl_chooser),
            TagRemover(),
            LocalOptimizer(10)]
