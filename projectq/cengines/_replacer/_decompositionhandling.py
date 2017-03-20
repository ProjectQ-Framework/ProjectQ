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


class ThisIsNotAGateClassError(Exception):
    pass


class DecompositionRule:
    def __init__(self, gate_class, gate_decomposer, gate_recognizer=lambda cmd: True):
        """
        The decomposition rule is a Decomposition object (see _decomposition.py) and
        consists of a function which recognizes a command (i.e., determines whether
        it can handle it) and a function which executes the decomposition. The
        gate_class parameter determines the gate class for which the decomposition
        is valid (keeps the number of calls to recognize functions lower).

        Args:
            gate_class: Gate class for which the decomposition should be applicable;
                this parameter is only used to enable binary search on
                `gate_object.__class__`.
                If your class is defined as

                .. code-block:: python

                    class MyGate(BasicGate):
                        pass

                Then you supply gate_class=MyGate
                However, if MyGate is overridden as often is the case when

                .. code-block:: python

                    MyGate = MyGate() # Because it allows the syntax MyGate | qubit

                then gate_class = MyGate.__class__
            gate_decomposer (function): Function which, given the command to
                decompose, applies a sequence of gates corresponding to the high-level
                function of a gate of type gate_class.
            gate_recognizer (function): Optional function which, given the command to
                decompose, returns whether the decomposition supports the given command.
                E.g., rotation gates may be rewritten using one decomposition for some
                angles, and another one for other angles. If no such function is
                provided, the decomposition rule will be valid for all gates of type
                gate_class.
        """

        # Check that gate_class is a gate class and not type
        if gate_class == type.__class__:
            raise ThisIsNotAGateClassError(
                "gate_class is not a valid gate_class.\n" +
                "Did you forget to create an instance and call" +
                " .__class__ in that one?\n" +
                " Rx.__class__ instead of Rx(0.6).__class__?\n")

        self.gate_class = gate_class
        self.gate_decomposer = gate_decomposer
        self.gate_recognizer = gate_recognizer


class DecompositionRuleSet:
    def __init__(self, rules=None, modules=None):
        """
        Args:
            rules list[DecompositionRule]: Initial decomposition rules.
            modules (iterable): A list of things with an
                               "all_defined_decomposition_rules" property to
                               add to the rule set.
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
        if not cls in self.decompositions:
            self.decompositions[cls] = []
        self.decompositions[cls].append(decomp_obj)
