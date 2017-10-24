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

"""
Defines the BasicGate class, the base class of all gates, the
BasicRotationGate class, the SelfInverseGate, the FastForwardingGate, the
ClassicalInstruction gate, and the BasicMathGate class.

Gates overload the | operator to allow the following syntax:

.. code-block:: python

    Gate | (qureg1, qureg2, qureg2)
    Gate | (qureg, qubit)
    Gate | qureg
    Gate | qubit
    Gate | (qubit,)

This means that for more than one quantum argument (right side of | ), a tuple
needs to be made explicitely, while for one argument it is optional.
"""

import math
from copy import deepcopy

from projectq.types import BasicQubit
from ._command import Command, apply_command


EQ_TOLERANCE = 1e-12


class NotMergeable(Exception):
    """
    Exception thrown when trying to merge two gates which are not mergeable (or
    where it is not    implemented (yet)).
    """
    pass


class NotInvertible(Exception):
    """
    Exception thrown when trying to invert a gate which is not invertable (or
    where the inverse is not  implemented (yet)).
    """
    pass


class BasicGate(object):
    """
    Base class of all gates.
    """
    def __init__(self):
        """
        Initialize a basic gate.

        Note:
            Set interchangeable qubit indices!
            (gate.interchangeable_qubit_indices)

            As an example, consider

            .. code-block:: python

                ExampleGate | (a,b,c,d,e)

            where a and b are interchangeable. Then, call this function as
            follows:

            .. code-block:: python

                self.set_interchangeable_qubit_indices([[0,1]])

            As another example, consider

            .. code-block:: python

                ExampleGate2 | (a,b,c,d,e)

            where a and b are interchangeable and, in addition, c, d, and e
            are interchangeable among themselves. Then, call this function as

            .. code-block:: python

                self.set_interchangeable_qubit_indices([[0,1],[2,3,4]])
        """
        self.interchangeable_qubit_indices = []

    def get_inverse(self):
        """
        Return the inverse gate.

        Standard implementation of get_inverse:

        Raises:
            NotInvertible: inverse is not implemented
        """
        raise NotInvertible("BasicGate: No get_inverse() implemented.")

    def get_merged(self, other):
        """
        Return this gate merged with another gate.

        Standard implementation of get_merged:

        Raises:
            NotMergeable: merging is not implemented
        """
        raise NotMergeable("BasicGate: No get_merged() implemented.")

    @staticmethod
    def make_tuple_of_qureg(qubits):
        """
        Convert quantum input of "gate | quantum input" to internal formatting.

        A Command object only accepts tuples of Quregs (list of Qubit objects)
        as qubits input parameter. However, with this function we allow the
        user to use a more flexible syntax:

            1) Gate | qubit
            2) Gate | [qubit0, qubit1]
            3) Gate | qureg
            4) Gate | (qubit, )
            5) Gate | (qureg, qubit)

        where qubit is a Qubit object and qureg is a Qureg object. This
        function takes the right hand side of | and transforms it to the
        correct input parameter of a Command object which is:

            1) -> Gate | ([qubit], )
            2) -> Gate | ([qubit0, qubit1], )
            3) -> Gate | (qureg, )
            4) -> Gate | ([qubit], )
            5) -> Gate | (qureg, [qubit])

        Args:
            qubits: a Qubit object, a list of Qubit objects, a Qureg object,
                or a tuple of Qubit or Qureg objects (can be mixed).
        Returns:
            Canonical representation (tuple<qureg>): A tuple containing Qureg
            (or list of Qubits) objects.
        """
        if not isinstance(qubits, tuple):
            qubits = (qubits,)

        qubits = list(qubits)

        for i in range(len(qubits)):
            if isinstance(qubits[i], BasicQubit):
                qubits[i] = [qubits[i]]

        return tuple(qubits)

    def generate_command(self, qubits):
        """
        Helper function to generate a command consisting of the gate and
        the qubits being acted upon.

        Args:
            qubits: see BasicGate.make_tuple_of_qureg(qubits)

        Returns:
            A Command object containing the gate and the qubits.
        """
        qubits = self.make_tuple_of_qureg(qubits)

        engines = [q.engine for reg in qubits for q in reg]
        eng = engines[0]
        assert all(e is eng for e in engines)
        return Command(eng, self, qubits)

    def __or__(self, qubits):
        """
        Operator| overload which enables the syntax Gate | qubits.

        Example:
            1) Gate | qubit
            2) Gate | [qubit0, qubit1]
            3) Gate | qureg
            4) Gate | (qubit, )
            5) Gate | (qureg, qubit)

        Args:
            qubits: a Qubit object, a list of Qubit objects, a Qureg object,
                    or a tuple of Qubit or Qureg objects (can be mixed).
        """
        cmd = self.generate_command(qubits)
        apply_command(cmd)

    def __eq__(self, other):
        """ Return True if equal (i.e., instance of same class). """
        return isinstance(other, self.__class__)

    def __ne__(self, other):
        return not self.__eq__(other)


class SelfInverseGate(BasicGate):
    """
    Self-inverse basic gate class.

    Automatic implementation of the get_inverse-member function for self-
    inverse gates.

    Example:
        .. code-block:: python

            # get_inverse(H) == H, it is a self-inverse gate:
            get_inverse(H) | qubit
    """
    def get_inverse(self):
        return deepcopy(self)


class BasicRotationGate(BasicGate):
    """
    Defines a base class of a rotation gate.

    A rotation gate has a continuous parameter (the angle), labeled 'angle' /
    self.angle. Its inverse is the same gate with the negated argument.
    Rotation gates of the same class can be merged by adding the angles.
    The continuous parameter is modulo 4 * pi, self.angle is in the interval
    [0, 4 * pi).
    """
    def __init__(self, angle):
        """
        Initialize a basic rotation gate.

        Args:
            angle (float): Angle of rotation (saved modulo 4 * pi)
        """
        BasicGate.__init__(self)
        self.angle = float(angle) % (4. * math.pi)

    def __str__(self):
        """
        Return the string representation of a BasicRotationGate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE])
        """
        return str(self.__class__.__name__) + "(" + str(self.angle) + ")"

    def tex_str(self):
        """
        Return the Latex string representation of a BasicRotationGate.

        Returns the class name and the angle as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        return str(self.__class__.__name__) + "$_{" + str(self.angle) + "}$"

    def get_inverse(self):
        """
        Return the inverse of this rotation gate (negate the angle, return new
        object).
        """
        if self.angle == 0:
            return self.__class__(0)
        else:
            return self.__class__(-self.angle + 4 * math.pi)

    def get_merged(self, other):
        """
        Return self merged with another gate.

        Default implementation handles rotation gate of the same type, where
        angles are simply added.

        Args:
            other: Rotation gate of same type.

        Raises:
            NotMergeable: For non-rotation gates or rotation gates of
                different type.

        Returns:
            New object representing the merged gates.
        """
        if isinstance(other, self.__class__):
            return self.__class__(self.angle + other.angle)
        raise NotMergeable("Can't merge different types of rotation gates.")

    def __eq__(self, other):
        """ Return True if same class and same rotation angle. """
        tolerance = EQ_TOLERANCE
        if isinstance(other, self.__class__):
            difference = abs(self.angle - other.angle) % (4 * math.pi)
            # Return True if angles are close to each other modulo 4 * pi
            if difference < tolerance or difference > 4 * math.pi - tolerance:
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class BasicPhaseGate(BasicGate):
    """
    Defines a base class of a phase gate.

    A phase gate has a continuous parameter (the angle), labeled 'angle' /
    self.angle. Its inverse is the same gate with the negated argument.
    Phase gates of the same class can be merged by adding the angles.
    The continuous parameter is modulo 2 * pi, self.angle is in the interval
    [0, 2 * pi).
    """
    def __init__(self, angle):
        """
        Initialize a basic rotation gate.

        Args:
            angle (float): Angle of rotation (saved modulo 2 * pi)
        """
        BasicGate.__init__(self)
        self.angle = float(angle) % (2. * math.pi)

    def __str__(self):
        """
        Return the string representation of a BasicRotationGate.

        Returns the class name and the angle as

        .. code-block:: python

            [CLASSNAME]([ANGLE])
        """
        return str(self.__class__.__name__) + "(" + str(self.angle) + ")"

    def tex_str(self):
        """
        Return the Latex string representation of a BasicRotationGate.

        Returns the class name and the angle as a subscript, i.e.

        .. code-block:: latex

            [CLASSNAME]$_[ANGLE]$
        """
        return str(self.__class__.__name__) + "$_{" + str(self.angle) + "}$"

    def get_inverse(self):
        """
        Return the inverse of this rotation gate (negate the angle, return new
        object).
        """
        if self.angle == 0:
            return self.__class__(0)
        else:
            return self.__class__(-self.angle + 2 * math.pi)

    def get_merged(self, other):
        """
        Return self merged with another gate.

        Default implementation handles rotation gate of the same type, where
        angles are simply added.

        Args:
            other: Rotation gate of same type.

        Raises:
            NotMergeable: For non-rotation gates or rotation gates of
                different type.

        Returns:
            New object representing the merged gates.
        """
        if isinstance(other, self.__class__):
            return self.__class__(self.angle + other.angle)
        raise NotMergeable("Can't merge different types of rotation gates.")

    def __eq__(self, other):
        """ Return True if same class and same rotation angle. """
        tolerance = EQ_TOLERANCE
        if isinstance(other, self.__class__):
            difference = abs(self.angle - other.angle) % (2 * math.pi)
            # Return True if angles are close to each other modulo 4 * pi
            if difference < tolerance or difference > 2 * math.pi - tolerance:
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


# Classical instruction gates never have control qubits.
class ClassicalInstructionGate(BasicGate):
    """
    Classical instruction gate.

    Base class for all gates which are not quantum gates in the typical sense,
    e.g., measurement, allocation/deallocation, ...
    """
    pass


class FastForwardingGate(ClassicalInstructionGate):
    """
    Base class for classical instruction gates which require a fast-forward
    through compiler engines that cache / buffer gates. Examples include
    Measure and Deallocate, which both should be executed asap, such
    that Measurement results are available and resources are freed,
    respectively.

    Note:
        The only requirement is that FlushGate commands run the entire
        circuit. FastForwardingGate objects can be used but the user cannot
        expect a measurement result to be available for all back-ends when
        calling only Measure. E.g., for the IBM Quantum Experience back-end,
        sending the circuit for each Measure-gate would be too inefficient,
        which is why a final

        .. code-block: python

            eng.flush()

        is required before the circuit gets sent through the API.
    """
    pass


class BasicMathGate(BasicGate):
    """
    Base class for all math gates.

    It allows efficient emulation by providing a mathematical representation
    which is given by the concrete gate which derives from this base class.
    The AddConstant gate, for example, registers a function of the form

    .. code-block:: python

        def add(x):
            return (x+a,)

    upon initialization. More generally, the function takes integers as
    parameters and returns a tuple / list of outputs, each entry corresponding
    to the function input. As an example, consider out-of-place
    multiplication, which takes two input registers and adds the result into a
    third, i.e., (a,b,c) -> (a,b,c+a*b). The corresponding function then is

    .. code-block:: python

        def multiply(a,b,c)
            return (a,b,c+a*b)
    """
    def __init__(self, math_fun):
        """
        Initialize a BasicMathGate by providing the mathematical function that
        it implements.

        Args:
            math_fun (function): Function which takes as many int values as
                input, as the gate takes registers. For each of these values,
                it then returns the output (i.e., it returns a list/tuple of
                output values).

        Example:
            .. code-block:: python

                def add(a,b):
                    return (a,a+b)
                BasicMathGate.__init__(self, add)

        If the gate acts on, e.g., fixed point numbers, the number of bits per
        register is also required in order to describe the action of such a
        mathematical gate. For this reason, there is

        .. code-block:: python

            BasicMathGate.get_math_function(qubits)

        which can be overwritten by the gate deriving from BasicMathGate.

        Example:
            .. code-block:: python

                def get_math_function(self, qubits):
                    n = len(qubits[0])
                    scal = 2.**n
                    def math_fun(a):
                        return (int(scal * (math.sin(math.pi * a / scal))),)
                    return math_fun

        """
        BasicGate.__init__(self)

        def math_function(x):
            return list(math_fun(*x))
        self._math_function = math_function

    def get_math_function(self, qubits):
        """
        Return the math function which corresponds to the action of this math
        gate, given the input to the gate (a tuple of quantum registers).

        Args:
            qubits (tuple<Qureg>): Qubits to which the math gate is being
                applied.

        Returns:
            math_fun (function): Python function describing the action of this
            gate. (See BasicMathGate.__init__ for an example).
        """
        return self._math_function
