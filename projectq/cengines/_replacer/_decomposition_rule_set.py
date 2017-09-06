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

from projectq.meta import Dagger


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
        decomp_obj = _Decomposition(rule.gate_decomposer, rule.gate_recognizer)
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


class _Decomposition(object):
    """
    The Decomposition class can be used to register a decomposition rule (by
    calling register_decomposition)
    """
    def __init__(self, replacement_fun, recogn_fun):
        """
        Construct the Decomposition object.

        Args:
            replacement_fun: Function that, when called with a `Command`
                object, decomposes this command.
            recogn_fun: Function that, when called with a `Command` object,
                returns True if and only if the replacement rule can handle
                this command.

        Every Decomposition is registered with the gate class. The
        Decomposition rule is then potentially valid for all objects which are
        an instance of that same class
        (i.e., instance of gate_object.__class__). All other parameters have
        to be checked by the recogn_fun, i.e., it has to decide whether the
        decomposition rule can indeed be applied to replace the given Command.

        As an example, consider recognizing the Toffoli gate, which is a
        Pauli-X gate with 2 control qubits. The recognizer function would then
        be:

        .. code-block:: python

            def recogn_toffoli(cmd):
                # can be applied if the gate is an X-gate with 2 controls:
                return len(cmd.control_qubits) == 2

        and, given a replacement function `replace_toffoli`, the decomposition
        rule can be registered as

        .. code-block:: python

            register_decomposition(X.__class__, decompose_toffoli,
                                   recogn_toffoli)

        Note:
            See projectq.setups.decompositions for more example codes.

        """
        self.decompose = replacement_fun
        self.check = recogn_fun

    def get_inverse_decomposition(self):
        """
        Return the Decomposition object which handles the inverse of the
        original command.

        This simulates the user having added a decomposition rule for the
        inverse as well. Since decomposing the inverse of a command can be
        achieved by running the original decomposition inside a
        `with Dagger(engine):` statement, this is not necessary
        (and will be done automatically by the framework).

        Returns:
            Decomposition handling the inverse of the original command.
        """
        def decomp(cmd):
            with Dagger(cmd.engine):
                self.decompose(cmd.get_inverse())

        def recogn(cmd):
            return self.check(cmd.get_inverse())

        return _Decomposition(decomp, recogn)
