#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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
Defines a setup to compile to qubits placed in 2-D grid.

It provides the `engine_list` for the `MainEngine`. This engine list contains
an AutoReplacer with most of the gate decompositions of ProjectQ, which are
used to decompose a circuit into only two qubit gates and arbitrary single
qubit gates. ProjectQ's GridMapper is then used to introduce the
necessary Swap operations to route interacting qubits next to each other.
This setup allows to choose the final gate set (with some limitations).
"""

import inspect

import projectq
import projectq.libs.math
import projectq.setups.decompositions
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               InstructionFilter, GridMapper,
                               LocalOptimizer, TagRemover)
from projectq.ops import (BasicMathGate, ClassicalInstructionGate, CNOT,
                          ControlledGate, get_inverse, QFT, Swap)


def high_level_gates(eng, cmd):
    """
    Remove any MathGates.
    """
    g = cmd.gate
    if g == QFT or get_inverse(g) == QFT or g == Swap:
        return True
    elif isinstance(g, BasicMathGate):
        return False
    return True


def one_and_two_qubit_gates(eng, cmd):
    all_qubits = [q for qr in cmd.all_qubits for q in qr]
    if isinstance(cmd.gate, ClassicalInstructionGate):
        # This is required to allow Measure, Allocate, Deallocate, Flush
        return True
    elif len(all_qubits) <= 2:
        return True
    else:
        return False


def get_engine_list(num_rows, num_columns, one_qubit_gates="any",
                    two_qubit_gates=(CNOT, Swap)):
    """
    Returns an engine list to compile to a 2-D grid of qubits.

    Note:
        If you choose a new gate set for which the compiler does not yet have
        standard rules, it raises an `NoGateDecompositionError` or a
        `RuntimeError: maximum recursion depth exceeded...`. Also note that
        even the gate sets which work might not yet be optimized. So make sure
        to double check and potentially extend the decomposition rules.
        This implemention currently requires that the one qubit gates must
        contain Rz and at least one of {Ry(best), Rx, H} and the two qubit gate
        must contain CNOT (recommended) or CZ.

    Note:
        Classical instructions gates such as e.g. Flush and Measure are
        automatically allowed.

    Example:
        get_engine_list(num_rows=2, num_columns=3,
                        one_qubit_gates=(Rz, Ry, Rx, H),
                        two_qubit_gates=(CNOT,))

    Args:
        num_rows(int): Number of rows in the grid
        num_columns(int): Number of columns in the grid.
        one_qubit_gates: "any" allows any one qubit gate, otherwise provide
                         a tuple of the allowed gates. If the gates are
                         instances of a class (e.g. X), it allows all gates
                         which are equal to it. If the gate is a class (Rz), it
                         allows all instances of this class. Default is "any"
        two_qubit_gates: "any" allows any two qubit gate, otherwise provide
                         a tuple of the allowed gates. If the gates are
                         instances of a class (e.g. CNOT), it allows all gates
                         which are equal to it. If the gate is a class, it
                         allows all instances of this class.
                         Default is (CNOT, Swap).
    Raises:
        TypeError: If input is for the gates is not "any" or a tuple.

    Returns:
        A list of suitable compiler engines.
    """
    if two_qubit_gates != "any" and not isinstance(two_qubit_gates, tuple):
        raise TypeError("two_qubit_gates parameter must be 'any' or a tuple. "
                        "When supplying only one gate, make sure to correctly "
                        "create the tuple (don't miss the comma), "
                        "e.g. two_qubit_gates=(CNOT,)")
    if one_qubit_gates != "any" and not isinstance(one_qubit_gates, tuple):
        raise TypeError("one_qubit_gates parameter must be 'any' or a tuple.")

    rule_set = DecompositionRuleSet(modules=[projectq.libs.math,
                                             projectq.setups.decompositions])
    allowed_gate_classes = []
    allowed_gate_instances = []
    if one_qubit_gates != "any":
        for gate in one_qubit_gates:
            if inspect.isclass(gate):
                allowed_gate_classes.append(gate)
            else:
                allowed_gate_instances.append((gate, 0))
    if two_qubit_gates != "any":
        for gate in two_qubit_gates:
            if inspect.isclass(gate):
                #  Controlled gate classes don't yet exists and would require
                #  separate treatment
                assert not isinstance(gate, ControlledGate)
                allowed_gate_classes.append(gate)
            else:
                if isinstance(gate, ControlledGate):
                    allowed_gate_instances.append((gate._gate, gate._n))
                else:
                    allowed_gate_instances.append((gate, 0))
    allowed_gate_classes = tuple(allowed_gate_classes)
    allowed_gate_instances = tuple(allowed_gate_instances)

    def low_level_gates(eng, cmd):
        all_qubits = [q for qr in cmd.all_qubits for q in qr]
        assert len(all_qubits) <= 2
        if isinstance(cmd.gate, ClassicalInstructionGate):
            # This is required to allow Measure, Allocate, Deallocate, Flush
            return True
        elif one_qubit_gates == "any" and len(all_qubits) == 1:
            return True
        elif two_qubit_gates == "any" and len(all_qubits) == 2:
            return True
        elif isinstance(cmd.gate, allowed_gate_classes):
            return True
        elif (cmd.gate, len(cmd.control_qubits)) in allowed_gate_instances:
            return True
        else:
            return False

    return [AutoReplacer(rule_set),
            TagRemover(),
            InstructionFilter(high_level_gates),
            LocalOptimizer(5),
            AutoReplacer(rule_set),
            TagRemover(),
            InstructionFilter(one_and_two_qubit_gates),
            LocalOptimizer(5),
            GridMapper(num_rows=num_rows, num_columns=num_columns),
            AutoReplacer(rule_set),
            TagRemover(),
            InstructionFilter(low_level_gates),
            LocalOptimizer(5),
            ]
