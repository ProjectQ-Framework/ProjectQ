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

    def __hash__(self):
        return hash(str(self))

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

    def __hash__(self):
        return hash(str(self))

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

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

class AddQuantum(BasicMathGate): 
    """ 
    Add up two quantum numbers represented by quantum registers.
    The numbers are stored from low- to high-bit, i.e., qunum[0] is the LSB.
    Example:
        .. code-block:: python

            qunum_a = eng.allocate_qureg(5)
            qunum_b = eng.allocate_qureg(5)
            carry_bit = eng.allocate_qubit()

            X | qunum_a[2] #qunum_a is now equal to 4 
            X | qunum_b[3] #qunum_b is now equal to 8 
            AddQuantum() | (qunum_a, qunum_b, carry)
            # qunum_a remains 4, qunum_b is now 12 and carry_bit is 0
    """

    def __init__(self):
        """
        Initializes the gate to  its base class, BasicMathGate, with the 
        corresponding function, so it can be emulated efficiently.
        """
        BasicMathGate.__init__(self,AddQuantum.get_math_function)
    
    def get_math_function(self,qubits):      
        n = len(qubits[0])
        def math_fun(a):
            a[1] = a[0] + a[1]
            if len("{0:b}".format(a[1])) > n:
               a[2] = 1
            return (a)
        return math_fun
    
    def __str__(self):
        return "AddQuantum"
    
    def __eq__(self, other):
        return (isinstance(other, AddQuantum))

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

class SubtractQuantum(BasicMathGate):
    """
    Subtract one quantum number represented by a quantum register from 
    another quantum number represented by a quantum register. 

    Example:
    .. code-block:: python
        
            qunum_a = eng.allocate_qureg(5)
            qunum_b = eng.allocate_qureg(5)
            X | qunum_a[2] #qunum_a is now equal to 4 
            X | qunum_b[3] #qunum_b is now equal to 8 
            SubtractQuantum() | (qunum_a, qunum_b)
            # qunum_a remains 4, qunum_b is now 4

    """
    def __init__(self):
        """
        Initializes the gate to  its base class, BasicMathGate, with the 
        corresponding function, so it can be emulated efficiently.
        """
        def subtract(a,b):
            return (a,b-a)
        BasicMathGate.__init__(self, subtract)
        
    def __str__(self):
        return "SubtractQuantum"

    def __eq__(self, other):
        return (isinstance(other, SubtractQuantum))

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)


class Comparator(BasicMathGate):
    """ 
    Add up two quantum numbers represented by quantum registers.
    The numbers are stored from low- to high-bit, i.e., qunum[0] is the LSB.
    Example:
        .. code-block:: python
        
            qunum_a = eng.allocate_qureg(5)
            qunum_b = eng.allocate_qureg(5)
            compare_bit = eng.allocate_qubit()
            X | qunum_a[4] #qunum_a is now equal to 16 
            X | qunum_b[3] #qunum_b is now equal to 8 
            Comparator() | (qunum_a, qunum_b, compare_bit)
            # qunum_a and qunum_b remain 16 and 8, qunum_b is now 12 and 
            compare bit is now 1

    """    
    def __init__(self):
        """
        Initializes the gate and its base class, BasicMathGate, with the
        corresponding function, so it can be emulated efficiently.
        """
        def compare(a,b,c):
            if b<a:
                if c==0:
                    c=1
                else:
                    c=0
            return(a,b,c)
        BasicMathGate.__init__(self, compare)

    def __str__(self):
        return "Comparator"

    def __eq__(self, other):
        return (isinstance(other, Comparator))

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

class QuantumConditionalAdd(BasicMathGate):
    
    def __init__(self):
        def conditionaladd(a,b,c):
            if c == 1:
                return (a,a+b,c)
            else:
                return (a,b,c)
        BasicMathGate.__init__(self,conditionaladd)
    
    def __str__(self):
        return "QuantumConditionalAdd"
    
    def __eq__(self, other):
        return (isinstance(other, QuantumConditionalAdd))

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

class QuantumDivision(BasicMathGate):
    """
    Divides one quantum register from another one quantum number represented by a quantum register from 
    another quantum number represented by a quantum register. 
    Example:
    .. code-block:: python
        
            qunum_a = eng.allocate_qureg(5)
            qunum_b = eng.allocate_qureg(5)
            X | qunum_a[2] #qunum_a is now equal to 4 
            X | qunum_b[3] #qunum_b is now equal to 8 
            SubtractQuantum() | (qunum_a, qunum_b)
            # qunum_a remains 4, qunum_b is now 4
    """
   
    def __init__(self):
        def division(a,b,c):
            if b != 0:
                d = a//b
                c = a&b
                return(d,b,c)
            else:
                return(a,b,c)
        BasicMathGate.__init__(self,division)
    
    def __str__(self):
        return "QuantumDivision"
    
    def __eq__(self,other):
        return (isinstance(other, QuantumDivision))
    
    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

class QuantumConditionalAddCarry(BasicMathGate):
    """
    Takes four inputs in the following order, two quantum register of equal
    size, a control qubit and a quantum register of two qubits. The gate
    works as follows, if the control qubit is |1>, the two quantum qubits
    are added. The first quantum register is not changed, the second 
    quantum register contains the added values, the control qubit is 
    unchanged and the first qubit of the fourth input contains the highest 
    carry of thesum. If the control qubit is |0> the gate does not perform
    an operation and all inputs remain unchanged.   

    Example:
        .. code-block:: python
            qunum_a = eng.allocate_qureg(4) # 4-qubit number
            qunum_b = eng.allocate_qureg(4) # 4-qubit number
            ctrl = eng.allocate_qubit()
            qunum_c = eng.allocate_qureg(2) 
            
            X | qunum_a[1] # qunum is now equal to 2
            All(X) | qunum_b[0:n]  # qunum is now equal to 15
            X | ctrl

            QuantumConditionalAddCarry() | (qunum_a, qunum_b, ctrl, qunum_c)
            #qunum_a and ctrl don't change, qunum_b and qunum_c are now both
            1 so in binary together 10001 (which is 17)
            
    """
    def __init__(self):
        """
        Initializes the gate to  its base class, BasicMathGate, with the
        corresponding function, so it can be emulated efficiently.
        """
        BasicMathGate.__init__(self,QuantumConditionalAddCarry.get_math_function)

    def get_math_function(self,qubits):
        n = len(qubits[0])
        def math_fun(a):
            if a[2] == 1:
                a[1] = a[0] + a[1]
                if len("{0:b}".format(a[1])) > n:
                    a[3] += 1
            return (a)
        return math_fun

    def __str__(self):
        return "QuantumConditionalAddCarry"

    def __eq__(self,other):
        return (isinstance(other, QuantumConditionalAddCarry))

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)

class QuantumMultiplication(BasicMathGate):
    """ 
    Multiplies two quantum numbers represented by a quantum registers. 
    Requires three quantum registers as inputs, the first two are the 
    numbers to be multiplied and should have the same size (n qubits). The 
    third register will hold the product and should be of size 2n+1.    
    The numbers are stored from low- to high-bit, i.e., qunum[0] is the LSB.

    Example:
        .. code-block:: python
        qunum_a = eng.allocate_qureg(4)
        qunum_b = eng.allocate_qureg(4)
        qunum_c = eng.allocate_qureg(9)
        X | qunum_a[2] # qunum_a is now 4
        X | qunum_b[3] # qunum_b is now 8
        QuantumMultiplication() | (qunum_a, qunum_b, qunum_c) 
        # qunum_c is now equal to 32
    """
    def __init__(self):
        """
        Initializes the gate and its base class, BasicMathGate, with the
        corresponding function, so it can be emulated efficiently.
        """
        def multiply(a,b,c):
                return (a,b,a*b)
        BasicMathGate.__init__(self,multiply)

    def __str__(self):
        return "QuantumMultiplication"

    def __eq__(self, other):
        return (isinstance(other, QuantumMultiplication))

    def __hash__(self):
        return hash(str(self))

    def __ne__(self, other):
        return not self.__eq__(other)
