from projectq.ops import get_inverse, BasicGate

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

        UniforlmyControlledGate(gates) | (choice, target_qubit)
    """
    def __init__(self, gates, up_to_diagonal=False):
        self._gates = copy.deepcopy(gates)
        self.interchangeable_qubit_indices = []
        self._decomposition = None
        self.up_to_diagonal = up_to_diagonal;

    # makes problems when using decomposition up to diagonals
    # def get_inverse(self):
    #     if up_to_diagonal:
    #         raise NotInvertible
    #     else:
    #         inverted_gates = [get_inverse(gate) for gate in self._gates]
    #         return UniformlyControlledGate(inverted_gates)

    def __str__(self):
        return "UCG"

    # makes projectq very unhappy (why?)
    # def __eq__(self, other):
    #     return False

    @property
    def decomposition(self):
        if self._decomposition == None:
            from projectq.isometries import _decompose_uniformly_controlled_gate
            self._decomposition = _decompose_uniformly_controlled_gate(self._gates)
        return self._decomposition

    @property
    def gates(self):
        return self._gates
