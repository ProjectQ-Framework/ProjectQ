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

from projectq.ops import BasicGate


class ThisIsNotAGateClassError(TypeError):
    pass


class DecompositionRule:
    """
    A rule for breaking down specific gates into sequences of simpler gates.
    """

    def __init__(self,
                 gate_class,
                 gate_decomposer,
                 gate_recognizer=lambda cmd: True):
        """
        Args:
            gate_class (type): The type of gate that this rule decomposes.

                The gate class is redundant information used to make lookups
                faster when iterating over a circuit and deciding "which rules
                apply to this gate?" again and again.

                Note that this parameter is a gate type, not a gate instance.
                You supply gate_class=MyGate or gate_class=MyGate().__class__,
                not gate_class=MyGate().

            gate_decomposer (function[projectq.ops.Command]): Function which,
                given the command to decompose, applies a sequence of gates
                corresponding to the high-level function of a gate of type
                gate_class.

            gate_recognizer (function[projectq.ops.Command] : boolean): A
                predicate that determines if the decomposition applies to the
                given command (on top of the filtering by gate_class).

                For example, a decomposition rule may only to apply rotation
                gates that rotate by a specific angle.

                If no gate_recognizer is given, the decomposition applies to
                all gates matching the gate_class.
        """

        # Check for common gate_class type mistakes.
        if isinstance(gate_class, BasicGate):
            raise ThisIsNotAGateClassError(
                "gate_class is a gate instance instead of a type of BasicGate."
                "\nDid you pass in someGate instead of someGate.__class__?")
        if gate_class == type.__class__:
            raise ThisIsNotAGateClassError(
                "gate_class is type.__class__ instead of a type of BasicGate."
                "\nDid you pass in GateType.__class__ instead of GateType?")

        self.gate_class = gate_class
        self.gate_decomposer = gate_decomposer
        self.gate_recognizer = gate_recognizer
