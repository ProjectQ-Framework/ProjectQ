# -*- coding: utf-8 -*-
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
Defines a setup to compile to qubits placed in a linear chain or a circle.

It provides the `engine_list` for the `MainEngine`. This engine list contains an AutoReplacer with most of the gate
decompositions of ProjectQ, which are used to decompose a circuit into only two qubit gates and arbitrary single qubit
gates. ProjectQ's LinearMapper is then used to introduce the necessary Swap operations to route interacting qubits
next to each other. This setup allows to choose the final gate set (with some limitations).
"""

from projectq.cengines import LinearMapper
from projectq.ops import CNOT, Swap

from ._utils import get_engine_list_linear_grid_base


def get_engine_list(num_qubits, cyclic=False, one_qubit_gates="any", two_qubit_gates=(CNOT, Swap)):
    """
    Returns an engine list to compile to a linear chain of qubits.

    Note:
        If you choose a new gate set for which the compiler does not yet have standard rules, it raises an
        `NoGateDecompositionError` or a `RuntimeError: maximum recursion depth exceeded...`. Also note that even the
        gate sets which work might not yet be optimized. So make sure to double check and potentially extend the
        decomposition rules.  This implemention currently requires that the one qubit gates must contain Rz and at
        least one of {Ry(best), Rx, H} and the two qubit gate must contain CNOT (recommended) or CZ.

    Note:
        Classical instructions gates such as e.g. Flush and Measure are automatically allowed.

    Example:
        get_engine_list(num_qubits=10, cyclic=False,
                        one_qubit_gates=(Rz, Ry, Rx, H),
                        two_qubit_gates=(CNOT,))

    Args:
        num_qubits(int): Number of qubits in the chain
        cyclic(bool): If a circle or not. Default is False
        one_qubit_gates: "any" allows any one qubit gate, otherwise provide a tuple of the allowed gates. If the gates
                         are instances of a class (e.g. X), it allows all gates which are equal to it. If the gate is
                         a class (Rz), it allows all instances of this class. Default is "any"
        two_qubit_gates: "any" allows any two qubit gate, otherwise provide a tuple of the allowed gates. If the gates
                         are instances of a class (e.g. CNOT), it allows all gates which are equal to it. If the gate
                         is a class, it allows all instances of this class.  Default is (CNOT, Swap).
    Raises:
        TypeError: If input is for the gates is not "any" or a tuple.

    Returns:
        A list of suitable compiler engines.
    """
    return get_engine_list_linear_grid_base(
        LinearMapper(num_qubits=num_qubits, cyclic=cyclic), one_qubit_gates, two_qubit_gates
    )
