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
Registers a decomposition for phase estimation.

(reference https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm)

The Quantum Phase Estimation (QPE) executes the algorithm up to the inverse
QFT included. The following steps measuring the ancillas and computing the
phase should be executed outside of the QPE.

The decomposition uses as ancillas (qpe_ancillas) the first qubit/qureg in
the Command and as system qubits teh second qubit/qureg in the Command.

The unitary operator for which the phase estimation is estimated (unitary)
is the gate in Command

Example:
    .. code-block:: python

       # Example using a ProjectQ gate

       n_qpe_ancillas = 3
       qpe_ancillas = eng.allocate_qureg(n_qpe_ancillas)
       system_qubits = eng.allocate_qureg(1)
       angle = cmath.pi*2.*0.125
       U = Ph(angle) # unitary_specfic_to_the_problem()

       # Apply Quantum Phase Estimation
       QPE(U) | (qpe_ancillas, system_qubits)

       All(Measure) | qpe_ancillas
       # Compute the phase from the ancilla measurement
       #(https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm)
       phasebinlist = [int(q) for q in qpe_ancillas]
       phase_in_bin = ''.join(str(j) for j in phasebinlist)
       phase_int = int(phase_in_bin,2)
       phase = phase_int / (2 ** n_qpe_ancillas)
       print (phase)

       # Example using a function (two_qubit_gate).
       # Instead of applying QPE on a gate U one could provide a function

       def two_qubit_gate(system_q, time):
           CNOT | (system_q[0], system_q[1])
           Ph(2.0*cmath.pi*(time * 0.125)) | system_q[1]
           CNOT | (system_q[0], system_q[1])

       n_qpe_ancillas = 3
       qpe_ancillas = eng.allocate_qureg(n_qpe_ancillas)
       system_qubits = eng.allocate_qureg(2)
       X | system_qubits[0]

       # Apply Quantum Phase Estimation
       QPE(two_qubit_gate) | (qpe_ancillas, system_qubits)

       All(Measure) | qpe_ancillas
       # Compute the phase from the ancilla measurement
       #(https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm)
       phasebinlist = [int(q) for q in qpe_ancillas]
       phase_in_bin = ''.join(str(j) for j in phasebinlist)
       phase_int = int(phase_in_bin,2)
       phase = phase_int / (2 ** n_qpe_ancillas)
       print (phase)

Attributes:
    unitary (BasicGate): Unitary Operation either a ProjectQ gate or a function f.
    Calling the function with the parameters system_qubits(Qureg) and time (integer),
    i.e. f(system_qubits, time), applies to the system qubits a unitary defined in f
    with parameter time.


"""

from projectq.cengines import DecompositionRule
from projectq.meta import Control, Loop
from projectq.ops import H, Tensor, get_inverse, QFT

from projectq.ops import QPE


def _decompose_QPE(cmd):  # pylint: disable=invalid-name
    """Decompose the Quantum Phase Estimation gate."""
    eng = cmd.engine

    # Ancillas is the first qubit/qureg. System-qubit is the second qubit/qureg
    qpe_ancillas = cmd.qubits[0]
    system_qubits = cmd.qubits[1]

    # Hadamard on the ancillas
    Tensor(H) | qpe_ancillas

    # The Unitary Operator
    unitary = cmd.gate.unitary

    # Control U on the system_qubits
    if callable(unitary):
        # If U is a function
        for i, ancilla in enumerate(qpe_ancillas):
            with Control(eng, ancilla):
                unitary(system_qubits, time=2 ** i)
    else:
        for i, ancilla in enumerate(qpe_ancillas):
            ipower = int(2 ** i)
            with Loop(eng, ipower):
                with Control(eng, ancilla):
                    unitary | system_qubits

    # Inverse QFT on the ancillas
    get_inverse(QFT) | qpe_ancillas


#: Decomposition rules
all_defined_decomposition_rules = [DecompositionRule(QPE, _decompose_QPE)]
