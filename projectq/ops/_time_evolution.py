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

import copy

from projectq.ops import Ph

from ._basics import BasicGate, NotMergeable
from ._qubit_operator import QubitOperator
from ._command import apply_command


class NotHermitianOperatorError(Exception):
    pass


class TimeEvolution(BasicGate):
    """
    Gate for time evolution under a Hamiltonian (QubitOperator object).

    This gate is the unitary time evolution propagator:
    exp(-i * H * t),
    where H is the Hamiltonian of the system and t is the time. Note that -i
    factor is stored implicitely.

    Example:
        .. code-block:: python

            wavefunction = eng.allocate_qureg(5)
            hamiltonian = 0.5 * QubitOperator("X0 Z1 Y5")
            # Apply exp(-i * H * t) to the wavefunction:
            TimeEvolution(time=2.0, hamiltonian=hamiltonian) | wavefunction

    Attributes:
        time(float, int): time t
        hamiltonian(QubitOperator): hamiltonaian H

    """
    def __init__(self, time, hamiltonian):
        """
        Initialize time evolution gate.

        Note:
            The hamiltonian must be hermitian and therefore only terms with
            real coefficients are allowed.
            Coefficients are internally converted to float.

        Args:
            time (float, or int): time to evolve under (can be negative).
            hamiltonian (QubitOperator): hamiltonian to evolve under.

        Raises:
            TypeError: If time is not a numeric type and hamiltonian is not a
                       QubitOperator.
            NotHermitianOperatorError: If the input hamiltonian is not
                                       hermitian (only real coefficients).
        """
        BasicGate.__init__(self)
        if not isinstance(time, (float, int)):
            raise TypeError("time needs to be a (real) numeric type.")
        if not isinstance(hamiltonian, QubitOperator):
            raise TypeError("hamiltonian needs to be QubitOperator object.")
        self.time = time
        self.hamiltonian = copy.deepcopy(hamiltonian)
        for term in hamiltonian.terms:
            if self.hamiltonian.terms[term].imag == 0:
                self.hamiltonian.terms[term] = float(
                    self.hamiltonian.terms[term].real)
            else:
                raise NotHermitianOperatorError("hamiltonian must be "
                                                "hermitian and hence only "
                                                "have real coefficients.")

    def get_inverse(self):
        """
        Return the inverse gate.
        """
        return TimeEvolution(self.time * -1.0, self.hamiltonian)

    def get_merged(self, other):
        """
        Return self merged with another TimeEvolution gate if possible.

        Two TimeEvolution gates are merged if:
            1) both have the same terms
            2) the proportionality factor for each of the terms
               must have relative error <= 1e-9 compared to the
               proportionality factors of the other terms.

        Note:
            While one could merge gates for which both hamiltonians commute,
            we are not doing this as in general the resulting gate would have
            to be decomposed again.

        Note:
            We are not comparing if terms are proportional to each other with
            an absolute tolerance. It is up to the user to remove terms close
            to zero because we cannot choose a suitable absolute error which
            works for everyone. Use, e.g., a decomposition rule for that.

        Args:
            other: TimeEvolution gate

        Raises:
            NotMergeable: If the other gate is not a TimeEvolution gate or
                          hamiltonians are not suitable for merging.

        Returns:
            New TimeEvolution gate equivalent to the two merged gates.
        """
        rel_tol = 1e-9
        if (isinstance(other, TimeEvolution) and
                set(self.hamiltonian.terms) == set(other.hamiltonian.terms)):
            factor = None
            for term in self.hamiltonian.terms:
                if factor is None:
                    factor = (self.hamiltonian.terms[term] /
                              float(other.hamiltonian.terms[term]))
                else:
                    tmp = (self.hamiltonian.terms[term] /
                           float(other.hamiltonian.terms[term]))
                    if not abs(factor - tmp) <= (
                            rel_tol * max(abs(factor), abs(tmp))):
                        raise NotMergeable("Cannot merge these two gates.")
            # Terms are proportional to each other
            new_time = self.time + other.time / factor
            return TimeEvolution(time=new_time, hamiltonian=self.hamiltonian)
        else:
            raise NotMergeable("Cannot merge these two gates.")

    def __or__(self, qubits):
        """
        Operator| overload which enables the following syntax:

        .. code-block:: python

            TimeEvolution(...) | qureg
            TimeEvolution(...) | (qureg,)
            TimeEvolution(...) | qubit
            TimeEvolution(...) | (qubit,)

        Unlike other gates, this gate is only allowed to be applied to one
        quantum register or one qubit.

        Example:

        .. code-block:: python

            wavefunction = eng.allocate_qureg(5)
            hamiltonian = QubitOperator("X1 Y3", 0.5)
            TimeEvolution(time=2.0, hamiltonian=hamiltonian) | wavefunction

        While in the above example the TimeEvolution gate is applied to 5
        qubits, the hamiltonian of this TimeEvolution gate acts only
        non-trivially on the two qubits wavefunction[1] and wavefunction[3].
        Therefore, the operator| will rescale the indices in the hamiltonian
        and sends the equivalent of the following new gate to the MainEngine:

        .. code-block:: python

            h = QubitOperator("X0 Y1", 0.5)
            TimeEvolution(2.0, h) | [wavefunction[1], wavefunction[3]]

        which is only a two qubit gate.

        Args:
            qubits: one Qubit object, one list of Qubit objects, one Qureg
                    object, or a tuple of the former three cases.
        """
        # Check that input is only one qureg or one qubit
        qubits = self.make_tuple_of_qureg(qubits)
        if len(qubits) != 1:
            raise TypeError("Only one qubit or qureg allowed.")
        # Check that if hamiltonian has only an identity term,
        # apply a global phase:
        if len(self.hamiltonian.terms) == 1 and () in self.hamiltonian.terms:
            Ph(-1 * self.time * self.hamiltonian.terms[()]) | qubits[0][0]
            return
        num_qubits = len(qubits[0])
        non_trivial_qubits = set()
        for term in self.hamiltonian.terms:
            for index, action in term:
                non_trivial_qubits.add(index)
        if max(non_trivial_qubits) >= num_qubits:
            raise ValueError("hamiltonian acts on more qubits than the gate "
                             "is applied to.")
        # create new TimeEvolution gate with rescaled qubit indices in
        # self.hamiltonian which are ordered from
        # 0,...,len(non_trivial_qubits) - 1
        new_index = dict()
        non_trivial_qubits = sorted(list(non_trivial_qubits))
        for i in range(len(non_trivial_qubits)):
            new_index[non_trivial_qubits[i]] = i
        new_hamiltonian = QubitOperator()
        assert len(new_hamiltonian.terms) == 0
        for term in self.hamiltonian.terms:
            new_term = tuple([(new_index[index], action)
                             for index, action in term])
            new_hamiltonian.terms[new_term] = self.hamiltonian.terms[term]
        new_gate = TimeEvolution(time=self.time, hamiltonian=new_hamiltonian)
        new_qubits = [qubits[0][i] for i in non_trivial_qubits]
        # Apply new gate
        cmd = new_gate.generate_command(new_qubits)
        apply_command(cmd)

    def __eq__(self, other):
        """ Not implemented as this object is a floating point type."""
        return NotImplemented

    def __ne__(self, other):
        """ Not implemented as this object is a floating point type."""
        return NotImplemented

    def __str__(self):
        return "exp({0} * ({1}))".format(-1j * self.time, self.hamiltonian)
