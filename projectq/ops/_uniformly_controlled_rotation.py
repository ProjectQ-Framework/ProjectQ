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

"""Definition of uniformly controlled Ry- and Rz-rotation gates."""

import math

from ._basics import ANGLE_PRECISION, ANGLE_TOLERANCE, BasicGate, NotMergeable


class UniformlyControlledRy(BasicGate):
    """
    Uniformly controlled Ry gate as introduced in arXiv:quant-ph/0312218.

    This is an n-qubit gate. There are n-1 control qubits and one target qubit.  This gate applies Ry(angles(k)) to
    the target qubit if the n-1 control qubits are in the classical state k. As there are 2^(n-1) classical states for
    the control qubits, this gate requires 2^(n-1) (potentially different) angle parameters.

    Example:
        .. code-block:: python

        controls = eng.allocate_qureg(2)
        target = eng.allocate_qubit()
        UniformlyControlledRy(angles=[0.1, 0.2, 0.3, 0.4]) | (controls, target)

    Note:
        The first quantum register contains the control qubits. When converting the classical state k of the control
        qubits to an integer, we define controls[0] to be the least significant (qu)bit. controls can also be an empty
        list in which case the gate corresponds to an Ry.

    Args:
        angles(list[float]): Rotation angles. Ry(angles[k]) is applied conditioned on the control qubits being in
                             state k.
    """

    def __init__(self, angles):
        """Construct a UniformlyControlledRy gate."""
        super().__init__()
        rounded_angles = []
        for angle in angles:
            new_angle = round(float(angle) % (4.0 * math.pi), ANGLE_PRECISION)
            if new_angle > 4 * math.pi - ANGLE_TOLERANCE:
                new_angle = 0.0
            rounded_angles.append(new_angle)
        self.angles = rounded_angles

    def get_inverse(self):
        """Return the inverse of this rotation gate (negate the angles, return new object)."""
        return self.__class__([-1 * angle for angle in self.angles])

    def get_merged(self, other):
        """Return self merged with another gate."""
        if isinstance(other, self.__class__):
            new_angles = [angle1 + angle2 for (angle1, angle2) in zip(self.angles, other.angles)]
            return self.__class__(new_angles)
        raise NotMergeable()

    def __str__(self):
        """Return a string representation of the object."""
        return "UniformlyControlledRy(" + str(self.angles) + ")"

    def __eq__(self, other):
        """Return True if same class, same rotation angles."""
        if isinstance(other, self.__class__):
            return self.angles == other.angles
        return False

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))


class UniformlyControlledRz(BasicGate):
    """
    Uniformly controlled Rz gate as introduced in arXiv:quant-ph/0312218.

    This is an n-qubit gate. There are n-1 control qubits and one target qubit.  This gate applies Rz(angles(k)) to
    the target qubit if the n-1 control qubits are in the classical state k. As there are 2^(n-1) classical states for
    the control qubits, this gate requires 2^(n-1) (potentially different) angle parameters.

    Example:
        .. code-block:: python

        controls = eng.allocate_qureg(2)
        target = eng.allocate_qubit()
        UniformlyControlledRz(angles=[0.1, 0.2, 0.3, 0.4]) | (controls, target)

    Note:
        The first quantum register are the contains qubits. When converting the classical state k of the control
        qubits to an integer, we define controls[0] to be the least significant (qu)bit. controls can also be an empty
        list in which case the gate corresponds to an Rz.

    Args:
        angles(list[float]): Rotation angles. Rz(angles[k]) is applied conditioned on the control qubits being in
                             state k.
    """

    def __init__(self, angles):
        """Construct a UniformlyControlledRz gate."""
        super().__init__()
        rounded_angles = []
        for angle in angles:
            new_angle = round(float(angle) % (4.0 * math.pi), ANGLE_PRECISION)
            if new_angle > 4 * math.pi - ANGLE_TOLERANCE:
                new_angle = 0.0
            rounded_angles.append(new_angle)
        self.angles = rounded_angles

    def get_inverse(self):
        """Return the inverse of this rotation gate (negate the angles, return new object)."""
        return self.__class__([-1 * angle for angle in self.angles])

    def get_merged(self, other):
        """Return self merged with another gate."""
        if isinstance(other, self.__class__):
            new_angles = [angle1 + angle2 for (angle1, angle2) in zip(self.angles, other.angles)]
            return self.__class__(new_angles)
        raise NotMergeable()

    def __str__(self):
        """Return a string representation of the object."""
        return "UniformlyControlledRz(" + str(self.angles) + ")"

    def __eq__(self, other):
        """Return True if same class, same rotation angles."""
        if isinstance(other, self.__class__):
            return self.angles == other.angles
        return False

    def __hash__(self):
        """Compute the hash of the object."""
        return hash(str(self))
