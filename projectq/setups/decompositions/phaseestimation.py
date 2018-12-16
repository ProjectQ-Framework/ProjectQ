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
Registers a decomposition for phase estimation.
    
(reference https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm)

The decomposition uses as ancillas the control qubits (qpe_ancillas) in the Command
and as system qubits (qubits) the qubits.

The unitary operator for which the phase estimation is estimated (unitary) is teh gate
in Command

Example:
    .. code-block:: python

       n_qpe_ancillas = 5
       qpe_ancillas = eng.allocate_qureg(n_qpe_ancillas)
       system_qubits = eng.allocate_qureg(2)
       U = unitary_specfic_to_the_problem()

       # Apply Quantum Phase Estimation
       PhaseEstimation(unitary = U) | (qpe_ancillas, system_qubits)

       # Apply an inverse QFT and measure to the ancillas
       get_inverse(QFT) | qpe_ancillas
       All(Measure) | qpe_ancillas
       # Compute the phase from the ancilla measurement (https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm)
       phasebinlist = [int(q) for q in qpe_ancillas]
       phase_in_bin = ''.join(str(j) for j in phasebinlist)
       phase_int = int(phase_in_bin,2)
       phase = phase_int / (2 ** n_qpe_ancillas)

Attributes:
    unitary (BasicGate): Unitary Operation U

"""

import numpy as np

from projectq.cengines import DecompositionRule
from projectq.meta import Control, get_control_count
from projectq.ops import H, Tensor, All

from projectq.ops import QPE

def _decompose_QPE(cmd):
    """ Decompose the Quantum Phase Estimation gate. """
    eng = cmd.engine
    qpe_ancillas = cmd.qubits[0]
    system_qubits = cmd.qubits[1]
    unitary = cmd.gate
    matrix = cmd.gate.unitary.matrix
    
    print (type(qpe_ancillas), len(qpe_ancillas))
    print (type(system_qubits), len(system_qubits))
    print (type(unitary))
    print (matrix)


    """
    Initialize Phase Estimation gate.

    Apply Tensor(H) to the qpe_ancillas

    Apply the controlled-unitary gate to system_qubits in powers depending on the
    numeral of the ancilla qubit (see the reference)

    Note:
        The unitary must by an unitary operation

    Args:
        unitary (BasicGate): unitary operation for which we want to obtain
            the eigenvalues and eigenvectors

    Raises:
        TypeError: If unitary is not a BasicGate
    """

    """
    BasicGate.__init__(self)
    self.unitary = unitary

    qubits = self.make_tuple_of_qureg(qubits)
    if len(qubits) != 2:
        raise TypeError("Only two qubit or qureg are allowed.")

    # Ancillas is the first qubit/qureg. System-qubit is the second qubit/qureg

    qpe_ancillas = qubits[0]
    system_qubits = qubits[1]

    # Hadamard on the ancillas
    Tensor(H) | qpe_ancillas

    # Control U on the eigenvector
    operator = self.unitary

    for i in range(len(qpe_ancillas)):
        ipower = int(2**i)
    
    #for i in range(len(qpe_ancillas)):
    #	 ipower = int(2**i)
    #	 for j in range(ipower):
    #	     C(operator) | (qpe_ancillas[i], system_qubits)
    """

#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(QPE, _decompose_QPE)
]


