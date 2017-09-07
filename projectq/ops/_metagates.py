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
Contains meta gates, i.e.,
* DaggeredGate (Represents the inverse of an arbitrary gate)
* ControlledGate (Represents a controlled version of an arbitrary gate)
* Tensor/All (Applies a single qubit gate to all supplied qubits), e.g.,
    Example:
        .. code-block:: python

          Tensor(H) | (qubit1, qubit2) # apply H to qubit #1 and #2

As well as the meta functions
* get_inverse (Tries to access the get_inverse member function of a gate
               and upon failure returns a DaggeredGate)
* C (Creates an n-ary controlled version of an arbitrary gate)
"""

from ._basics import BasicGate, NotInvertible
from ._command import Command, apply_command


class ControlQubitError(Exception):
    """
    Exception thrown when wrong number of control qubits are supplied.
    """
    pass


class DaggeredGate(BasicGate):
    """
    Wrapper class allowing to execute the inverse of a gate, even when it does
    not define one.

    If there is a replacement available, then there is also one for the
    inverse, namely the replacement function run in reverse, while inverting
    all gates. This class enables using this emulation automatically.

    A DaggeredGate is returned automatically when employing the get_inverse-
    function on a gate which does not provide a get_inverse() member function.

    Example:
        .. code-block:: python

            with Dagger(eng):
                MySpecialGate | qubits

    will create a DaggeredGate if MySpecialGate does not implement
    get_inverse. If there is a decomposition function available, an auto-
    replacer engine can automatically replace the inverted gate by a call to
    the decomposition function inside a "with Dagger"-statement.
    """

    def __init__(self, gate):
        """
        Initialize a DaggeredGate representing the inverse of the gate 'gate'.

        Args:
            gate: Any gate object of which to represent the inverse.
        """
        BasicGate.__init__(self)
        self._gate = gate

        try:
            # Hermitian conjugate is inverse matrix
            self.matrix = gate.matrix.getH()
        except AttributeError:
            pass

    def __str__(self):
        """
        Return string representation (str(gate) + \"^\dagger\").
        """
        return str(self._gate) + "^\dagger"

    def tex_str(self):
        """
        Return the Latex string representation of a Daggered gate.
        """
        return str(self._gate) + "$^\dagger$"

    def get_inverse(self):
        """
        Return the inverse gate (the inverse of the inverse of a gate is the
        gate itself).
        """
        return self._gate

    def __eq__(self, other):
        """
        Return True if self is equal to other, i.e., same type and
        representing the inverse of the same gate.
        """
        return isinstance(other, self.__class__) and self._gate == other._gate


def get_inverse(gate):
    """
    Return the inverse of a gate.

    Tries to call gate.get_inverse and, upon failure, creates a DaggeredGate
    instead.

    Args:
        gate: Gate of which to get the inverse

    Example:
        .. code-block:: python

            get_inverse(H) # returns a Hadamard gate (HGate object)
    """
    try:
        return gate.get_inverse()
    except NotInvertible:
        return DaggeredGate(gate)


class ControlledGate(BasicGate):
    """
    Controlled version of a gate.

    Note:
        Use the meta function :func:`C()` to create a controlled gate

    A wrapper class which enables (multi-) controlled gates. It overloads
    the __or__-operator, using the first qubits provided as control qubits.
    The n control-qubits need to be the first n qubits. They can be in
    separate quregs.

    Example:
        .. code-block:: python

            ControlledGate(gate, 2) | (qb0, qb2, qb3) # qb0 & qb2 are controls
            C(gate, 2) | (qb0, qb2, qb3) # This is much nicer.
            C(gate, 2) | ([qb0,qb2], qb3) # Is equivalent

    Note:
        Use :func:`C` rather than ControlledGate, i.e.,

        .. code-block:: python

            C(X, 2) == Toffoli
    """

    def __init__(self, gate, n=1):
        """
        Initialize a ControlledGate object.

        Args:
            gate: Gate to wrap.
            n (int): Number of control qubits.
        """
        BasicGate.__init__(self)
        if isinstance(gate, ControlledGate):
            self._gate = gate._gate
            self._n = gate._n + n
        else:
            self._gate = gate
            self._n = n

    def __str__(self):
        """ Return string representation, i.e., CC...C(gate). """
        return "C" * self._n + str(self._gate)

    def get_inverse(self):
        """
        Return inverse of a controlled gate, which is the controlled inverse
        gate.
        """
        return ControlledGate(get_inverse(self._gate), self._n)

    def __or__(self, qubits):
        """
        Apply the controlled gate to qubits, using the first n qubits as
        controls.

        Note: The control qubits can be split across the first quregs.
            However, the n-th control qubit needs to be the last qubit in a
            qureg. The following quregs belong to the gate.

        Args:
            qubits (tuple of lists of Qubit objects): qubits to which to apply
                the gate.
        """
        qubits = BasicGate.make_tuple_of_qureg(qubits)

        ctrl = []
        gate_quregs = []
        adding_to_controls = True
        for reg in qubits:
            if adding_to_controls:
                ctrl += reg
                adding_to_controls = len(ctrl) < self._n
            else:
                gate_quregs.append(reg)
        # Test that there were enough control quregs and that that
        # the last control qubit was the last qubit in a qureg.
        if len(ctrl) != self._n:
            raise ControlQubitError("Wrong number of control qubits. "
                                    "First qureg(s) need to contain exactly "
                                    "the required number of control quregs.")

        import projectq.meta
        with projectq.meta.Control(gate_quregs[0][0].engine, ctrl):
            self._gate | tuple(gate_quregs)

    def __eq__(self, other):
        """ Compare two ControlledGate objects (return True if equal). """
        return (isinstance(other, self.__class__) and
                self._gate == other._gate and self._n == other._n)

    def __ne__(self, other):
        return not self.__eq__(other)


def C(gate, n=1):
    """
    Return n-controlled version of the provided gate.

    Args:
        gate: Gate to turn into its controlled version
        n: Number of controls (default: 1)

    Example:
        .. code-block:: python

            C(NOT) | (c, q) # equivalent to CNOT | (c, q)
    """
    return ControlledGate(gate, n)


class Tensor(BasicGate):
    """
    Wrapper class allowing to apply a (single-qubit) gate to every qubit in a
    quantum register. Allowed syntax is to supply either a qureg or a tuple
    which contains only one qureg.

    Example:
        .. code-block:: python

            Tensor(H) | x # applies H to every qubit in the list of qubits x
            Tensor(H) | (x,) # alternative to be consistent with other syntax
    """

    def __init__(self, gate):
        """ Initialize a Tensor object for the gate. """
        BasicGate.__init__(self)
        self._gate = gate

    def __str__(self):
        """ Return string representation. """
        return "Tensor(" + str(self._gate) + ")"

    def get_inverse(self):
        """
        Return the inverse of this tensored gate (which is the tensored
        inverse of the gate).
        """
        return Tensor(get_inverse(self._gate))

    def __eq__(self, other):
        return isinstance(other, Tensor) and self._gate == other._gate

    def __ne__(self, other):
        return not self.__eq__(other)

    def __or__(self, qubits):
        """ Applies the gate to every qubit in the quantum register qubits. """
        if isinstance(qubits, tuple):
            assert len(qubits) == 1
            qubits = qubits[0]
        assert isinstance(qubits, list)
        for qubit in qubits:
            self._gate | qubit

All = Tensor
