from projectq.ops import get_inverse, BasicGate

import numpy as np
import copy
import math
import cmath

class UniformlyControlledGate(BasicGate):
    """
    A set of 2^k single qubit gates controlled on k qubits.
    For each state of the choice qubits the corresponding
    gate is applied to the target qubit.

    .. code-block:: python

        UniforlmyControlledGate(gates) | (choice, qubit)
    """
    def __init__(self, gates, up_to_diagonal=False):
        self._gates = copy.deepcopy(gates)
        self.interchangeable_qubit_indices = []
        self._decomposed = False
        self._up_to_diagonal = up_to_diagonal;

    # makes problems when using decomposition up to diagonals
    # def get_inverse(self):
    #     inverted_gates = [get_inverse(gate) for gate in self._gates]
    #     return UniformlyControlledGate(inverted_gates)

    def __str__(self):
        return "UCG"

    # makes projectq very unhappy (why?)
    # def __eq__(self, other):
    #     return False

    def decompose(self):
        assert self._decomposed == False
        from projectq.isometries import _DecomposeUCG
        self._decomposed_gates, self._phases =  \
            _DecomposeUCG(self._gates).get_decomposition()
        self._decomposed = True

    @property
    def decomposed(self):
        return self._decomposed

    @property
    def decomposition(self):
        return self._decomposed_gates, self._phases

    @property
    def decomposed_gates(self):
        return self._decomposed_gates

    @property
    def gates(self):
        return self._gates

    @property
    def phases(self):
        return self._phases

    @property
    def up_to_diagonal(self):
        return self._up_to_diagonal
