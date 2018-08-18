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

from projectq.ops import H, Tensor, C
from ._basics import BasicGate

class PhaseEstimation(BasicGate):
    """
    Gate for phase estimation for a unitary operation U.

    This gate executes teh algorith of phase estimation up to just before the
    inverse QFT on the ancillas
    
    (reference https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm)
    
    This allows to use externally to the gate any QFT schema as a semi-classical one.
    
    The gate is applied to a qureg of ancillas and a qureg of system qubits and use
    as a parameter the unitary operator U.
    
    After Phase Estimation gate is applied the ancillas are prepared to inverse QFT
    for phase (eigenvalue) extraction and the system quibits end in the corresponding
    eigenvector.
    

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
    def __init__(self, unitary):
        """
        Initialize Phase Estimation gate.

        Note:
            The unitary must by an unitary operation

        Args:
            unitary (BasicGate): unitary operation for which we want to obtain
	    the eigenvalues and eigenvectors

        Raises:
            TypeError: If unitary is not a BasicGate
        """
        BasicGate.__init__(self)
        self.unitary = unitary


    def __or__(self, qubits):
        """	
	Apply Tensor(H) to the qpe_ancillas
	
	Apply the controlled-unitary gate to system_qubits in powers depending on the
	numeral of the ancilla qubit (see the reference)
        Args:
            qpe_ancillas (qureg object): ancillas of the algorithm
	    system_qubits (qureg object): qubits on which the unitary is applied and which
	    	are eigenvector of U or combination of eigenvectors of U
        """

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
           for j in range(ipower):
              C(operator) | (qpe_ancillas[i],system_qubits)

    def __str__(self):
        return "PhaseEstimation"
