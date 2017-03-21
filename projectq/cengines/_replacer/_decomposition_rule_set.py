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

from ._decomposition import Decomposition


class DecompositionRuleSet:
    """
    A collection of indexed decomposition rules.
    """
    def __init__(self, rules=None, modules=None):
        """
        Args:
            rules list[DecompositionRule]: Initial decomposition rules.
            modules (iterable[ModuleWithDecompositionRuleSet]): A list of
                things with an "all_defined_decomposition_rules" property
                containing decomposition rules to add to the rule set.
        """
        self.decompositions = dict()

        if rules:
            self.add_decomposition_rules(rules)

        if modules:
            self.add_decomposition_rules([
                rule
                for module in modules
                for rule in module.all_defined_decomposition_rules])

    def add_decomposition_rules(self, rules):
        for rule in rules:
            self.add_decomposition_rule(rule)

    def add_decomposition_rule(self, rule):
        """
        Add a decomposition rule to the rule set.

        Args:
            rule (DecompositionRuleGate): The decomposition rule to add.
        """
        decomp_obj = Decomposition(rule.gate_decomposer, rule.gate_recognizer)
        cls = rule.gate_class.__name__
        if cls not in self.decompositions:
            self.decompositions[cls] = []
        self.decompositions[cls].append(decomp_obj)


class ModuleWithDecompositionRuleSet:
    """
    Interface type for explaining one of the parameters that can be given to
    DecompositionRuleSet.
    """
    def __init__(self, all_defined_decomposition_rules):
        """
        Args:
            all_defined_decomposition_rules (list[DecompositionRule]):
                A list of decomposition rules.
        """
        self.all_defined_decomposition_rules = all_defined_decomposition_rules
