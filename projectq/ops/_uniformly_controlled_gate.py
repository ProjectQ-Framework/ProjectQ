# Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from projectq.ops import get_inverse, BasicGate
from ._basics import BasicGate, NotInvertible, NotMergeable

import numpy as np
import copy
import math
import cmath


class UniformlyControlledGate(BasicGate):
    """
    A set of 2^k single qubit gates controlled on k choice qubits.
    For each state of the choice qubits the corresponding
    gate is applied to the target qubit.

    .. code-block:: python
        gates = [H, Z, T, S]
        U = UniformlyControlledGate(gates)
        U | (choice_qubits, target_qubit)

    Attributes:
        gates: list of 2^k single qubit gates
    """
    def __init__(self, gates, up_to_diagonal=False):
        self._gates = copy.deepcopy(gates)
        self.interchangeable_qubit_indices = []
        self._decomposition = None
        self.up_to_diagonal = up_to_diagonal

    def get_inverse(self):
        if self.up_to_diagonal:
            raise NotInvertible
        else:
            inverted_gates = [get_inverse(gate) for gate in self._gates]
            return UniformlyControlledGate(inverted_gates)

    def get_merged(self, other):
        if self.up_to_diagonal:
            raise NotMergeable("Cannot merge these two gates.")
        if isinstance(other, UniformlyControlledGate):
            from projectq.libs.isometries import _SingleQubitGate
            if len(self.gates) != len(other.gates):
                raise NotMergeable("Cannot merge these two gates.")
            new_gates = [_SingleQubitGate(self.gates[i].matrix *
                                          other.gates[i].matrix)
                         for i in range(len(other.gates))]
            return UniformlyControlledGate(new_gates)
        else:
            raise NotMergeable("Cannot merge these two gates.")

    @property
    def decomposition(self):
        if self._decomposition is None:
            from projectq.libs.isometries import \
                _decompose_uniformly_controlled_gate
            self._decomposition = \
                _decompose_uniformly_controlled_gate(self._gates)
        return self._decomposition

    @property
    def gates(self):
        return self._gates

    def __str__(self):
        return "UCG"

    def __eq__(self, other):
        """ Not implemented as this object is a floating point type."""
        return NotImplemented

    def __ne__(self, other):
        """ Not implemented as this object is a floating point type."""
        return NotImplemented
