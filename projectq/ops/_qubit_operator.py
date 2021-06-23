# -*- coding: utf-8 -*-
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
"""QubitOperator stores a sum of Pauli operators acting on qubits."""

import cmath
import copy

from ._basics import BasicGate, NotInvertible, NotMergeable
from ._command import apply_command
from ._gates import Ph, X, Y, Z

EQ_TOLERANCE = 1e-12

# Define products of all Pauli operators for symbolic multiplication.
_PAULI_OPERATOR_PRODUCTS = {
    ('I', 'I'): (1.0, 'I'),
    ('I', 'X'): (1.0, 'X'),
    ('X', 'I'): (1.0, 'X'),
    ('I', 'Y'): (1.0, 'Y'),
    ('Y', 'I'): (1.0, 'Y'),
    ('I', 'Z'): (1.0, 'Z'),
    ('Z', 'I'): (1.0, 'Z'),
    ('X', 'X'): (1.0, 'I'),
    ('Y', 'Y'): (1.0, 'I'),
    ('Z', 'Z'): (1.0, 'I'),
    ('X', 'Y'): (1.0j, 'Z'),
    ('X', 'Z'): (-1.0j, 'Y'),
    ('Y', 'X'): (-1.0j, 'Z'),
    ('Y', 'Z'): (1.0j, 'X'),
    ('Z', 'X'): (1.0j, 'Y'),
    ('Z', 'Y'): (-1.0j, 'X'),
}


class QubitOperatorError(Exception):
    """Exception raised when a QubitOperator is instantiated with some invalid data"""


class QubitOperator(BasicGate):
    """
    A sum of terms acting on qubits, e.g., 0.5 * 'X0 X5' + 0.3 * 'Z1 Z2'.

    A term is an operator acting on n qubits and can be represented as:

    coefficent * local_operator[0] x ... x local_operator[n-1]

    where x is the tensor product. A local operator is a Pauli operator ('I', 'X', 'Y', or 'Z') which acts on one
    qubit. In math notation a term is, for example, 0.5 * 'X0 X5', which means that a Pauli X operator acts on qubit 0
    and 5, while the identity operator acts on all other qubits.

    A QubitOperator represents a sum of terms acting on qubits and overloads operations for easy manipulation of these
    objects by the user.

    Note for a QubitOperator to be a Hamiltonian which is a hermitian operator, the coefficients of all terms must be
    real.

    .. code-block:: python

        hamiltonian = 0.5 * QubitOperator('X0 X5') + 0.3 * QubitOperator('Z0')

    Our Simulator takes a hermitian QubitOperator to directly calculate the expectation value (see
    Simulator.get_expectation_value) of this observable.

    A hermitian QubitOperator can also be used as input for the TimeEvolution gate.

    If the QubitOperator is unitary, i.e., it contains only one term with a coefficient, whose absolute value is 1,
    then one can apply it directly to qubits:

    .. code-block:: python

        eng = projectq.MainEngine()
        qureg = eng.allocate_qureg(6)
        QubitOperator('X0 X5', 1.j) | qureg # Applies X to qubit 0 and 5 with an additional global phase of 1.j


    Attributes:
        terms (dict): **key**: A term represented by a tuple containing all non-trivial local Pauli operators ('X',
                      'Y', or 'Z').  A non-trivial local Pauli operator is specified by a tuple with the first element
                      being an integer indicating the qubit on which a non-trivial local operator acts and the second
                      element being a string, either 'X', 'Y', or 'Z', indicating which non-trivial Pauli operator
                      acts on that qubit. Examples: ((1, 'X'),) or ((1, 'X'), (4,'Z')) or the identity ().  The tuples
                      representing the non-trivial local terms are sorted according to the qubit number they act on,
                      starting from 0.  **value**: Coefficient of this term as a (complex) float
    """

    def __init__(self, term=None, coefficient=1.0):  # pylint: disable=too-many-branches
        """
        Inits a QubitOperator.

        The init function only allows to initialize one term. Additional terms have to be added using += (which is
        fast) or using + of two QubitOperator objects:

        Example:
            .. code-block:: python

                ham = ((QubitOperator('X0 Y3', 0.5)
                        + 0.6 * QubitOperator('X0 Y3')))
                # Equivalently
                ham2 = QubitOperator('X0 Y3', 0.5)
                ham2 += 0.6 * QubitOperator('X0 Y3')

        Note:
            Adding terms to QubitOperator is faster using += (as this is done by in-place addition). Specifying the
            coefficient in the __init__ is faster than by multiplying a QubitOperator with a scalar as calls an
            out-of-place multiplication.

        Args:
            coefficient (complex float, optional): The coefficient of the first term of this QubitOperator. Default is
                1.0.
            term (optional, empy tuple, a tuple of tuples, or a string):
                1) Default is None which means there are no terms in the QubitOperator hence it is the "zero" Operator
                2) An empty tuple means there are no non-trivial Pauli operators acting on the qubits hence only
                   identities with a coefficient (which by default is 1.0).
                3) A sorted tuple of tuples. The first element of each tuple is an integer indicating the qubit on
                   which a non-trivial local operator acts, starting from zero. The second element of each tuple is a
                   string, either 'X', 'Y' or 'Z', indicating which local operator acts on that qubit.
                4) A string of the form 'X0 Z2 Y5', indicating an X on qubit 0, Z on qubit 2, and Y on qubit 5. The
                   string should be sorted by the qubit number. '' is the identity.

        Raises:
            QubitOperatorError: Invalid operators provided to QubitOperator.
        """
        BasicGate.__init__(self)
        if not isinstance(coefficient, (int, float, complex)):
            raise ValueError('Coefficient must be a numeric type.')
        self.terms = {}
        if term is None:
            return
        if isinstance(term, tuple):
            if term == ():
                self.terms[()] = coefficient
            else:
                # Test that input is a tuple of tuples and correct action
                for local_operator in term:
                    if not isinstance(local_operator, tuple) or len(local_operator) != 2:
                        raise ValueError("term specified incorrectly.")
                    qubit_num, action = local_operator
                    if not isinstance(action, str) or action not in 'XYZ':
                        raise ValueError("Invalid action provided: must be string 'X', 'Y', or 'Z'.")
                    if not (isinstance(qubit_num, int) and qubit_num >= 0):
                        raise QubitOperatorError(
                            "Invalid qubit number provided to QubitTerm: must be a non-negative int."
                        )
                # Sort and add to self.terms:
                term = list(term)
                term.sort(key=lambda loc_operator: loc_operator[0])
                self.terms[tuple(term)] = coefficient
        elif isinstance(term, str):
            list_ops = []
            for element in term.split():
                if len(element) < 2:
                    raise ValueError('term specified incorrectly.')
                list_ops.append((int(element[1:]), element[0]))
            # Test that list_ops has correct format of tuples
            for local_operator in list_ops:
                qubit_num, action = local_operator
                if not isinstance(action, str) or action not in 'XYZ':
                    raise ValueError("Invalid action provided: must be string 'X', 'Y', or 'Z'.")
                if not (isinstance(qubit_num, int) and qubit_num >= 0):
                    raise QubitOperatorError("Invalid qubit number provided to QubitTerm: must be a non-negative int.")
            # Sort and add to self.terms:
            list_ops.sort(key=lambda loc_operator: loc_operator[0])
            self.terms[tuple(list_ops)] = coefficient
        else:
            raise ValueError('term specified incorrectly.')

    def compress(self, abs_tol=1e-12):
        """
        Eliminates all terms with coefficients close to zero and removes imaginary parts of coefficients that are
        close to zero.

        Args:
            abs_tol(float): Absolute tolerance, must be at least 0.0
        """
        new_terms = {}
        for term in self.terms:
            coeff = self.terms[term]
            if abs(coeff.imag) <= abs_tol:
                coeff = coeff.real
            if abs(coeff) > abs_tol:
                new_terms[term] = coeff
        self.terms = new_terms

    def isclose(self, other, rel_tol=1e-12, abs_tol=1e-12):
        """
        Returns True if other (QubitOperator) is close to self.

        Comparison is done for each term individually. Return True if the difference between each term in self and
        other is less than the relative tolerance w.r.t. either other or self (symmetric test) or if the difference is
        less than the absolute tolerance.

        Args:
            other(QubitOperator): QubitOperator to compare against.
            rel_tol(float): Relative tolerance, must be greater than 0.0
            abs_tol(float): Absolute tolerance, must be at least 0.0
        """
        # terms which are in both:
        for term in set(self.terms).intersection(set(other.terms)):
            left = self.terms[term]
            right = other.terms[term]
            # math.isclose does this in Python >=3.5
            if not abs(left - right) <= max(rel_tol * max(abs(left), abs(right)), abs_tol):
                return False
        # terms only in one (compare to 0.0 so only abs_tol)
        for term in set(self.terms).symmetric_difference(set(other.terms)):
            if term in self.terms:
                if not abs(self.terms[term]) <= abs_tol:
                    return False
            elif not abs(other.terms[term]) <= abs_tol:
                return False
        return True

    def __or__(self, qubits):  # pylint: disable=too-many-locals
        """
        Operator| overload which enables the following syntax:

        .. code-block:: python

            QubitOperator(...) | qureg
            QubitOperator(...) | (qureg,)
            QubitOperator(...) | qubit
            QubitOperator(...) | (qubit,)

        Unlike other gates, this gate is only allowed to be applied to one
        quantum register or one qubit and only if the QubitOperator is
        unitary, i.e., consists of one term with a coefficient whose absolute
        values is 1.

        Example:

        .. code-block:: python

            eng = projectq.MainEngine()
            qureg = eng.allocate_qureg(6)
            QubitOperator('X0 X5', 1.j) | qureg  # Applies X to qubit 0 and 5
                                                 # with an additional global
                                                 # phase of 1.j

        While in the above example the QubitOperator gate is applied to 6
        qubits, it only acts non-trivially on the two qubits qureg[0] and
        qureg[5]. Therefore, the operator| will create a new rescaled
        QubitOperator, i.e, it sends the equivalent of the following new gate
        to the MainEngine:

        .. code-block:: python

            QubitOperator('X0 X1', 1.j) | [qureg[0], qureg[5]]

        which is only a two qubit gate.

        Args:
            qubits: one Qubit object, one list of Qubit objects, one Qureg
                    object, or a tuple of the former three cases.

        Raises:
            TypeError: If QubitOperator is not unitary or applied to more than
                       one quantum register.
            ValueError: If quantum register does not have enough qubits
        """
        # Check that input is only one qureg or one qubit
        qubits = self.make_tuple_of_qureg(qubits)
        if len(qubits) != 1:
            raise TypeError("Only one qubit or qureg allowed.")
        # Check that operator is unitary
        if not len(self.terms) == 1:
            raise TypeError(
                "Too many terms. Only QubitOperators consisting "
                "of a single term (single n-qubit Pauli operator) "
                "with a coefficient of unit length can be applied "
                "to qubits with this function."
            )
        ((term, coefficient),) = self.terms.items()
        phase = cmath.phase(coefficient)
        if abs(coefficient) < 1 - EQ_TOLERANCE or abs(coefficient) > 1 + EQ_TOLERANCE:
            raise TypeError(
                "abs(coefficient) != 1. Only QubitOperators "
                "consisting of a single term (single n-qubit "
                "Pauli operator) with a coefficient of unit "
                "length can be applied to qubits with this "
                "function."
            )
        # Test if we need to apply only Ph
        if term == ():
            Ph(phase) | qubits[0][0]
            return
        # Check that Qureg has enough qubits:
        num_qubits = len(qubits[0])
        non_trivial_qubits = set()
        for index, _ in term:
            non_trivial_qubits.add(index)
        if max(non_trivial_qubits) >= num_qubits:
            raise ValueError("QubitOperator acts on more qubits than the gate is applied to.")
        # Apply X, Y, Z, if QubitOperator acts only on one qubit
        if len(term) == 1:
            if term[0][1] == "X":
                X | qubits[0][term[0][0]]
            elif term[0][1] == "Y":
                Y | qubits[0][term[0][0]]
            elif term[0][1] == "Z":
                Z | qubits[0][term[0][0]]
            Ph(phase) | qubits[0][term[0][0]]
            return
        # Create new QubitOperator gate with rescaled qubit indices in
        # 0,..., len(non_trivial_qubits) - 1
        new_index = dict()
        non_trivial_qubits = sorted(list(non_trivial_qubits))
        for i, qubit in enumerate(non_trivial_qubits):
            new_index[qubit] = i
        new_qubitoperator = QubitOperator()
        new_term = tuple((new_index[index], action) for index, action in term)
        new_qubitoperator.terms[new_term] = coefficient
        new_qubits = [qubits[0][i] for i in non_trivial_qubits]
        # Apply new gate
        cmd = new_qubitoperator.generate_command(new_qubits)
        apply_command(cmd)

    def get_inverse(self):
        """
        Return the inverse gate of a QubitOperator if applied as a gate.

        Raises:
            NotInvertible: Not implemented for QubitOperators which have
                           multiple terms or a coefficient with absolute value
                           not equal to 1.
        """

        if len(self.terms) == 1:
            ((term, coefficient),) = self.terms.items()
            if not abs(coefficient) < 1 - EQ_TOLERANCE and not abs(coefficient) > 1 + EQ_TOLERANCE:
                return QubitOperator(term, coefficient ** (-1))
        raise NotInvertible("BasicGate: No get_inverse() implemented.")

    def get_merged(self, other):
        """
        Return this gate merged with another gate.

        Standard implementation of get_merged:

        Raises:
            NotMergeable: merging is not possible
        """
        if isinstance(other, self.__class__) and len(other.terms) == 1 and len(self.terms) == 1:
            return self * other
        raise NotMergeable()

    def __imul__(self, multiplier):  # pylint: disable=too-many-locals,too-many-branches
        """
        In-place multiply (*=) terms with scalar or QubitOperator.

        Args:
            multiplier(complex float, or QubitOperator): multiplier
        """
        # Handle scalars.
        if isinstance(multiplier, (int, float, complex)):
            for term in self.terms:
                self.terms[term] *= multiplier
            return self

        # Handle QubitOperator.
        if isinstance(multiplier, QubitOperator):  # pylint: disable=too-many-nested-blocks
            result_terms = dict()
            for left_term in self.terms:
                for right_term in multiplier.terms:
                    new_coefficient = self.terms[left_term] * multiplier.terms[right_term]

                    # Loop through local operators and create new sorted list
                    # of representing the product local operator:
                    product_operators = []
                    left_operator_index = 0
                    right_operator_index = 0
                    n_operators_left = len(left_term)
                    n_operators_right = len(right_term)
                    while left_operator_index < n_operators_left and right_operator_index < n_operators_right:
                        (left_qubit, left_loc_op) = left_term[left_operator_index]
                        (right_qubit, right_loc_op) = right_term[right_operator_index]

                        # Multiply local operators acting on the same qubit
                        if left_qubit == right_qubit:
                            left_operator_index += 1
                            right_operator_index += 1
                            (scalar, loc_op) = _PAULI_OPERATOR_PRODUCTS[(left_loc_op, right_loc_op)]

                            # Add new term.
                            if loc_op != 'I':
                                product_operators += [(left_qubit, loc_op)]
                                new_coefficient *= scalar
                            # Note if loc_op == 'I', then scalar == 1.0

                        # If left_qubit > right_qubit, add right_loc_op; else,
                        # add left_loc_op.
                        elif left_qubit > right_qubit:
                            product_operators += [(right_qubit, right_loc_op)]
                            right_operator_index += 1
                        else:
                            product_operators += [(left_qubit, left_loc_op)]
                            left_operator_index += 1

                    # Finish the remainding operators:
                    if left_operator_index == n_operators_left:
                        product_operators += right_term[right_operator_index::]
                    elif right_operator_index == n_operators_right:
                        product_operators += left_term[left_operator_index::]

                    # Add to result dict
                    tmp_key = tuple(product_operators)
                    if tmp_key in result_terms:
                        result_terms[tmp_key] += new_coefficient
                    else:
                        result_terms[tmp_key] = new_coefficient
            self.terms = result_terms
            return self
        raise TypeError('Cannot in-place multiply term of invalid type ' + 'to QubitTerm.')

    def __mul__(self, multiplier):
        """
        Return self * multiplier for a scalar, or a QubitOperator.

        Args:
            multiplier: A scalar, or a QubitOperator.

        Returns:
            product: A QubitOperator.

        Raises:
            TypeError: Invalid type cannot be multiply with QubitOperator.
        """
        if isinstance(multiplier, (int, float, complex, QubitOperator)):
            product = copy.deepcopy(self)
            product *= multiplier
            return product
        raise TypeError('Object of invalid type cannot multiply with QubitOperator.')

    def __rmul__(self, multiplier):
        """
        Return multiplier * self for a scalar.

        We only define __rmul__ for scalars because the left multiply
        exist for  QubitOperator and left multiply
        is also queried as the default behavior.

        Args:
            multiplier: A scalar to multiply by.

        Returns:
            product: A new instance of QubitOperator.

        Raises:
            TypeError: Object of invalid type cannot multiply QubitOperator.
        """
        if not isinstance(multiplier, (int, float, complex)):
            raise TypeError('Object of invalid type cannot multiply with QubitOperator.')
        return self * multiplier

    def __truediv__(self, divisor):
        """
        Return self / divisor for a scalar.

        Note:
            This is always floating point division.

        Args:
            divisor: A scalar to divide by.

        Returns:
            A new instance of QubitOperator.

        Raises:
            TypeError: Cannot divide local operator by non-scalar type.
        """
        if not isinstance(divisor, (int, float, complex)):
            raise TypeError('Cannot divide QubitOperator by non-scalar type.')
        return self * (1.0 / divisor)

    def __itruediv__(self, divisor):
        if not isinstance(divisor, (int, float, complex)):
            raise TypeError('Cannot divide QubitOperator by non-scalar type.')
        self *= 1.0 / divisor
        return self

    def __iadd__(self, addend):
        """
        In-place method for += addition of QubitOperator.

        Args:
            addend: A QubitOperator.

        Raises:
            TypeError: Cannot add invalid type.
        """
        if isinstance(addend, QubitOperator):
            for term in addend.terms:
                if term in self.terms:
                    if abs(addend.terms[term] + self.terms[term]) > 0.0:
                        self.terms[term] += addend.terms[term]
                    else:
                        self.terms.pop(term)
                else:
                    self.terms[term] = addend.terms[term]
        else:
            raise TypeError('Cannot add invalid type to QubitOperator.')
        return self

    def __add__(self, addend):
        """Return self + addend for a QubitOperator."""
        summand = copy.deepcopy(self)
        summand += addend
        return summand

    def __isub__(self, subtrahend):
        """
        In-place method for -= subtraction of QubitOperator.

        Args:
            subtrahend: A QubitOperator.

        Raises:
            TypeError: Cannot subtract invalid type from QubitOperator.
        """
        if isinstance(subtrahend, QubitOperator):
            for term in subtrahend.terms:
                if term in self.terms:
                    if abs(self.terms[term] - subtrahend.terms[term]) > 0.0:
                        self.terms[term] -= subtrahend.terms[term]
                    else:
                        self.terms.pop(term)
                else:
                    self.terms[term] = -subtrahend.terms[term]
        else:
            raise TypeError('Cannot subtract invalid type from QubitOperator.')
        return self

    def __sub__(self, subtrahend):
        """Return self - subtrahend for a QubitOperator."""
        minuend = copy.deepcopy(self)
        minuend -= subtrahend
        return minuend

    def __neg__(self):
        return -1.0 * self

    def __str__(self):
        """Return an easy-to-read string representation."""
        if not self.terms:
            return '0'
        string_rep = ''
        for term in self.terms:
            tmp_string = '{}'.format(self.terms[term])
            if term == ():
                tmp_string += ' I'
            for operator in term:
                if operator[1] == 'X':
                    tmp_string += ' X{}'.format(operator[0])
                elif operator[1] == 'Y':
                    tmp_string += ' Y{}'.format(operator[0])
                elif operator[1] == 'Z':
                    tmp_string += ' Z{}'.format(operator[0])
                else:  # pragma: no cover
                    raise ValueError('Internal compiler error: operator must be one of X, Y, Z!')
            string_rep += '{} +\n'.format(tmp_string)
        return string_rep[:-3]

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))
