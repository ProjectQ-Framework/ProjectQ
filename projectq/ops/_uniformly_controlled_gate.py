from ._basics import BasicGate
from ._command import Command
from projectq.ops import get_inverse
from projectq.types import WeakQubitRef

import numpy as np
import copy

class UniformlyControlledGate(BasicGate):
    """
    A set of 2^k single qubit gates controlled on k qubits.
    For each state of the control qubits the corresponding
    gate is applied to the target qubit.

    .. code-block:: python

        UniforlmyControlledGate(choice_qubits, gates) | qubit
    """
    def __init__(self, choice_qubits, gates):
        # use the word 'choice' to avoid overloading the 'control'
        # terminology
        n = len(choice_qubits)
        assert len(gates) == 1 << n
        choice_qubits = [WeakQubitRef(qubit.engine, qubit.id)
                        for qubit in choice_qubits]
        self._gates = copy.deepcopy(gates)
        self._choice_qubits = choice_qubits
        self.interchangeable_qubit_indices = []


    def get_inverse(self):
        inverted_gates = [get_inverse(gate) for gate in self._gates]
        return UniformlyControlledGate(self._choice_qubits, inverted_gates)

    #inherited from BasicGate, need to make sure that the
    #choice qubits are seen by the rest of the compiler
    def generate_command(self, qubits):
        qubits = self.make_tuple_of_qureg(qubits)
        assert len(qubits) == 1
        assert len(qubits[0]) == 1
        target = qubits[0][0]
        eng = target.engine
        return Command(eng, self, ([target],self._choice_qubits))

    @property
    def choice_qubits(self):
        return self._choice_qubits


    @property
    def gates(self):
        return self._gates


    def __str__(self):
        return "Uniformly Controlled Gate"
