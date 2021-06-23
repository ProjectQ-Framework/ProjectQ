# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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
"""Math gates for ProjectQ"""

from projectq.ops import BasicMathGate


class AddConstant(BasicMathGate):
    """
    Add a constant to a quantum number represented by a quantum register,
    stored from low- to high-bit.

    Example:
        .. code-block:: python

            qunum = eng.allocate_qureg(5) # 5-qubit number
            X | qunum[1] # qunum is now equal to 2
            AddConstant(3) | qunum # qunum is now equal to 5

    Important: if you run with conditional and carry, carry needs to
    be a quantum register for the compiler/decomposition to work.
    """

    def __init__(self, a):  # pylint: disable=invalid-name
        """
        Initializes the gate to the number to add.

        Args:
            a (int): Number to add to a quantum register.

        It also initializes its base class, BasicMathGate, with the
        corresponding function, so it can be emulated efficiently.
        """
        BasicMathGate.__init__(self, lambda x: ((x + a),))
        self.a = a  # pylint: disable=invalid-name

    def get_inverse(self):
        """
        Return the inverse gate (subtraction of the same constant).
        """
        return SubConstant(self.a)

    def __str__(self):
        return "AddConstant({})".format(self.a)

    def __eq__(self, other):
        return isinstance(other, AddConstant) and self.a == other.a

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)


def SubConstant(a):  # pylint: disable=invalid-name
    """
    Subtract a constant from a quantum number represented by a quantum
    register, stored from low- to high-bit.

    Args:
        a (int): Constant to subtract

    Example:
        .. code-block:: python

            qunum = eng.allocate_qureg(5) # 5-qubit number
            X | qunum[2] # qunum is now equal to 4
            SubConstant(3) | qunum # qunum is now equal to 1
    """
    return AddConstant(-a)


class AddConstantModN(BasicMathGate):
    """
    Add a constant to a quantum number represented by a quantum register
    modulo N.

    The number is stored from low- to high-bit, i.e., qunum[0] is the LSB.

    Example:
        .. code-block:: python

            qunum = eng.allocate_qureg(5) # 5-qubit number
            X | qunum[1] # qunum is now equal to 2
            AddConstantModN(3, 4) | qunum # qunum is now equal to 1

    .. note::

      Pre-conditions:

      * c < N
      * c >= 0
      * The value stored in the quantum register must be lower than N
    """

    def __init__(self, a, N):
        """
        Initializes the gate to the number to add modulo N.

        Args:
            a (int): Number to add to a quantum register (0 <= a < N).
            N (int): Number modulo which the addition is carried out.

        It also initializes its base class, BasicMathGate, with the
        corresponding function, so it can be emulated efficiently.
        """
        BasicMathGate.__init__(self, lambda x: ((x + a) % N,))
        self.a = a  # pylint: disable=invalid-name
        self.N = N

    def __str__(self):
        return "AddConstantModN({}, {})".format(self.a, self.N)

    def get_inverse(self):
        """
        Return the inverse gate (subtraction of the same number a modulo the
        same number N).
        """
        return SubConstantModN(self.a, self.N)

    def __eq__(self, other):
        return isinstance(other, AddConstantModN) and self.a == other.a and self.N == other.N

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)


def SubConstantModN(a, N):  # pylint: disable=invalid-name
    """
    Subtract a constant from a quantum number represented by a quantum
    register modulo N.

    The number is stored from low- to high-bit, i.e., qunum[0] is the LSB.

    Args:
        a (int): Constant to add
        N (int): Constant modulo which the addition of a should be carried
            out.

    Example:
        .. code-block:: python

            qunum = eng.allocate_qureg(3) # 3-qubit number
            X | qunum[1] # qunum is now equal to 2
            SubConstantModN(4,5) | qunum # qunum is now -2 = 6 = 1 (mod 5)

    .. note::

      Pre-conditions:

      * c < N
      * c >= 0
      * The value stored in the quantum register must be lower than N
    """
    return AddConstantModN(N - a, N)


class MultiplyByConstantModN(BasicMathGate):
    """
    Multiply a quantum number represented by a quantum register by a constant
    modulo N.

    The number is stored from low- to high-bit, i.e., qunum[0] is the LSB.

    Example:
        .. code-block:: python

            qunum = eng.allocate_qureg(5) # 5-qubit number
            X | qunum[2] # qunum is now equal to 4
            MultiplyByConstantModN(3,5) | qunum # qunum is now 2.

    .. note::

      Pre-conditions:

      * c < N
      * c >= 0
      * gcd(c, N) == 1
      * The value stored in the quantum register must be lower than N
    """

    def __init__(self, a, N):  # pylint: disable=invalid-name
        """
        Initializes the gate to the number to multiply with modulo N.

        Args:
            a (int): Number by which to multiply a quantum register
                (0 <= a < N).
            N (int): Number modulo which the multiplication is carried out.

        It also initializes its base class, BasicMathGate, with the
        corresponding function, so it can be emulated efficiently.
        """
        BasicMathGate.__init__(self, lambda x: ((a * x) % N,))
        self.a = a  # pylint: disable=invalid-name
        self.N = N

    def __str__(self):
        return "MultiplyByConstantModN({}, {})".format(self.a, self.N)

    def __eq__(self, other):
        return isinstance(other, MultiplyByConstantModN) and self.a == other.a and self.N == other.N

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)


class AddQuantumGate(BasicMathGate):
    """
    Adds up two quantum numbers represented by quantum registers.
    The numbers are stored from low- to high-bit, i.e., qunum[0] is the LSB.

    Example:
        .. code-block:: python

            qunum_a = eng.allocate_qureg(5) # 5-qubit number
            qunum_b = eng.allocate_qureg(5) # 5-qubit number
            carry_bit = eng.allocate_qubit()

            X | qunum_a[2] #qunum_a is now equal to 4
            X | qunum_b[3] #qunum_b is now equal to 8
            AddQuantum | (qunum_a, qunum_b, carry)
            # qunum_a remains 4, qunum_b is now 12 and carry_bit is 0
    """

    def __init__(self):
        BasicMathGate.__init__(self, None)

    def __str__(self):
        return "AddQuantum"

    def __eq__(self, other):
        return isinstance(other, AddQuantumGate)

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_math_function(self, qubits):
        n_qubits = len(qubits[0])

        def math_fun(a):  # pylint: disable=invalid-name
            a[1] = a[0] + a[1]
            if len(bin(a[1])[2:]) > n_qubits:
                a[1] = a[1] % (2 ** n_qubits)

                if len(a) == 3:
                    # Flip the last bit of the carry register
                    a[2] ^= 1
            return a

        return math_fun

    def get_inverse(self):
        """
        Return the inverse gate (subtraction of the same number a modulo the
        same number N).
        """
        return _InverseAddQuantumGate()


AddQuantum = AddQuantumGate()


class _InverseAddQuantumGate(BasicMathGate):
    """
    Internal gate glass to support emulation for inverse
    addition.
    """

    def __init__(self):
        BasicMathGate.__init__(self, None)

    def __str__(self):
        return "_InverseAddQuantum"

    def get_math_function(self, qubits):
        def math_fun(a):  # pylint: disable=invalid-name
            if len(a) == 3:
                # Flip the last bit of the carry register
                a[2] ^= 1

            a[1] -= a[0]
            return a

        return math_fun


class SubtractQuantumGate(BasicMathGate):
    """
    Subtract one quantum number represented by a quantum register from
    another quantum number represented by a quantum register.

    Example:
    .. code-block:: python

            qunum_a = eng.allocate_qureg(5) # 5-qubit number
            qunum_b = eng.allocate_qureg(5) # 5-qubit number
            X | qunum_a[2] #qunum_a is now equal to 4
            X | qunum_b[3] #qunum_b is now equal to 8
            SubtractQuantum | (qunum_a, qunum_b)
            # qunum_a remains 4, qunum_b is now 4

    """

    def __init__(self):
        """
        Initializes the gate to its base class, BasicMathGate, with the corresponding function, so it can be emulated
        efficiently.
        """

        def subtract(a, b):  # pylint: disable=invalid-name
            return (a, b - a)

        BasicMathGate.__init__(self, subtract)

    def __str__(self):
        return "SubtractQuantum"

    def __eq__(self, other):
        return isinstance(other, SubtractQuantumGate)

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_inverse(self):
        """
        Return the inverse gate (subtraction of the same number a modulo the same number N).
        """
        return AddQuantum


SubtractQuantum = SubtractQuantumGate()


class ComparatorQuantumGate(BasicMathGate):
    """
    Flips a compare qubit if the binary value of first imput is higher than the second input.
    The numbers are stored from low- to high-bit, i.e., qunum[0] is the LSB.
    Example:
        .. code-block:: python

            qunum_a = eng.allocate_qureg(5) # 5-qubit number
            qunum_b = eng.allocate_qureg(5) # 5-qubit number
            compare_bit = eng.allocate_qubit()
            X | qunum_a[4] #qunum_a is now equal to 16
            X | qunum_b[3] #qunum_b is now equal to 8
            ComparatorQuantum | (qunum_a, qunum_b, compare_bit)
            # qunum_a and qunum_b remain 16 and 8, qunum_b is now 12 and
            compare bit is now 1

    """

    def __init__(self):
        """
        Initializes the gate and its base class, BasicMathGate, with the corresponding function, so it can be emulated
        efficiently.
        """

        def compare(a, b, c):  # pylint: disable=invalid-name
            # pylint: disable=invalid-name
            if b < a:
                if c == 0:
                    c = 1
                else:
                    c = 0
            return (a, b, c)

        BasicMathGate.__init__(self, compare)

    def __str__(self):
        return "Comparator"

    def __eq__(self, other):
        return isinstance(other, ComparatorQuantumGate)

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_inverse(self):
        """
        Return the inverse gate
        """
        return AddQuantum


ComparatorQuantum = ComparatorQuantumGate()


class DivideQuantumGate(BasicMathGate):
    """
    Divides one quantum number from another. Takes three inputs which should be quantum registers of equal size; a
    dividend, a remainder and a divisor. The remainder should be in the state |0...0> and the dividend should be
    bigger than the divisor.The gate returns (in this order): the remainder, the quotient and the divisor.

    The numbers are stored from low- to high-bit, i.e., qunum[0] is the LSB.

    Example:
    .. code-block:: python

            qunum_a = eng.allocate_qureg(5) # 5-qubit number
            qunum_b = eng.allocate_qureg(5) # 5-qubit number
            qunum_c = eng.allocate_qureg(5) # 5-qubit number

            All(X) | [qunum_a[0],qunum_a[3]] #qunum_a is now equal to 9
            X | qunum_c[2] #qunum_c is now equal to 4

            DivideQuantum | (qunum_a, qunum_b,qunum_c)
            # qunum_a is now equal to 1 (remainder), qunum_b is now
            # equal to 2 (quotient) and qunum_c remains 4 (divisor)

            |dividend>|remainder>|divisor> -> |remainder>|quotient>|divisor>
    """

    def __init__(self):
        """
        Initializes the gate and its base class, BasicMathGate, with the corresponding function, so it can be emulated
        efficiently.
        """

        def division(dividend, remainder, divisor):
            if divisor == 0 or divisor > dividend:
                return (remainder, dividend, divisor)

            quotient = remainder + dividend // divisor
            return ((dividend - (quotient * divisor)), quotient, divisor)

        BasicMathGate.__init__(self, division)

    def get_inverse(self):
        return _InverseDivideQuantumGate()

    def __str__(self):
        return "DivideQuantum"

    def __eq__(self, other):
        return isinstance(other, DivideQuantumGate)

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)


DivideQuantum = DivideQuantumGate()


class _InverseDivideQuantumGate(BasicMathGate):
    """
    Internal gate glass to support emulation for inverse division.
    """

    def __init__(self):
        def inverse_division(remainder, quotient, divisor):
            if divisor == 0:
                return (quotient, remainder, divisor)

            dividend = remainder + quotient * divisor
            remainder = 0
            return (dividend, remainder, divisor)

        BasicMathGate.__init__(self, inverse_division)

    def __str__(self):
        return "_InverseDivideQuantum"


class MultiplyQuantumGate(BasicMathGate):
    """
    Multiplies two quantum numbers represented by a quantum registers.  Requires three quantum registers as inputs,
    the first two are the numbers to be multiplied and should have the same size (n qubits). The third register will
    hold the product and should be of size 2n+1.  The numbers are stored from low- to high-bit, i.e., qunum[0] is the
    LSB.

    Example:
        .. code-block:: python

        qunum_a = eng.allocate_qureg(4)
        qunum_b = eng.allocate_qureg(4)
        qunum_c = eng.allocate_qureg(9)
        X | qunum_a[2] # qunum_a is now 4
        X | qunum_b[3] # qunum_b is now 8
        MultiplyQuantum() | (qunum_a, qunum_b, qunum_c)
        # qunum_a remains 4 and qunum_b remains 8, qunum_c is now equal to 32
    """

    def __init__(self):
        """
        Initializes the gate and its base class, BasicMathGate, with the corresponding function, so it can be emulated
        efficiently.
        """

        def multiply(a, b, c):  # pylint: disable=invalid-name
            return (a, b, c + a * b)

        BasicMathGate.__init__(self, multiply)

    def __str__(self):
        return "MultiplyQuantum"

    def __eq__(self, other):
        return isinstance(other, MultiplyQuantumGate)

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_inverse(self):
        return _InverseMultiplyQuantumGate()


MultiplyQuantum = MultiplyQuantumGate()


class _InverseMultiplyQuantumGate(BasicMathGate):
    """
    Internal gate glass to support emulation for inverse multiplication.
    """

    def __init__(self):
        def inverse_multiplication(a, b, c):  # pylint: disable=invalid-name
            return (a, b, c - a * b)

        BasicMathGate.__init__(self, inverse_multiplication)

    def __str__(self):
        return "_InverseMultiplyQuantum"
