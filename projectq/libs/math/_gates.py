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
    """
    def __init__(self, a):
        """
        Initializes the gate to the number to add.

        Args:
            a (int): Number to add to a quantum register.

        It also initializes its base class, BasicMathGate, with the
        corresponding function, so it can be emulated efficiently.
        """
        BasicMathGate.__init__(self, lambda x: ((x + a),))
        self.a = a

    def get_inverse(self):
        """
        Return the inverse gate (subtraction of the same constant).
        """
        return SubConstant(self.a)

    def __str__(self):
        return "AddConstant({})".format(self.a)

    def __eq__(self, other):
        return isinstance(other, AddConstant) and self.a == other.a

    def __ne__(self, other):
        return not self.__eq__(other)


def SubConstant(a):
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
        self.a = a
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
        return (isinstance(other, AddConstantModN) and self.a == other.a and
                self.N == other.N)

    def __ne__(self, other):
        return not self.__eq__(other)


def SubConstantModN(a, N):
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
    """
    def __init__(self, a, N):
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
        self.a = a
        self.N = N

    def __str__(self):
        return "MultiplyByConstantModN({}, {})".format(self.a, self.N)

    def __eq__(self, other):
        return (isinstance(other, MultiplyByConstantModN) and
                self.a == other.a and self.N == other.N)

    def __ne__(self, other):
        return not self.__eq__(other)
