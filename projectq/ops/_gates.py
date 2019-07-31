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
Contains definitions of standard gates such as
* Hadamard (H)
* Pauli-X (X / NOT)
* GroundStateGate (|0><0|)
* Pauli-Z (Z)
* T and its inverse (T / Tdagger)
* Swap gate (Swap)
* Phase gate (Ph)
* Rotation-Z (Rz)
* Rotation-Z on two qubits (Rzz)
* Phase-shift (R)
* Measurement (Measure)

and meta gates, i.e.,
* Allocate / Deallocate qubits
* Flush gate (end of circuit)
"""

import math
import cmath
import warnings

import numpy as np
import scipy.linalg as la

from projectq.ops import get_inverse
from ._basics import (BasicGate,
                      MatrixGate,
                      SelfInverseGate,
                      BasicRotationGate,
                      BasicPhaseGate,
                      ClassicalInstructionGate,
                      FastForwardingGate,
                      BasicMathGate)
from ._command import apply_command


class HGate(SelfInverseGate):
    """ Hadamard gate class """
    def __str__(self):
        return "H"

    @property
    def matrix(self):
        return 1. / cmath.sqrt(2.) * np.matrix([[1, 1], [1, -1]])

#: Shortcut (instance of) :class:`projectq.ops.HGate`
H = HGate()


class XGate(SelfInverseGate):
    """ Pauli-X gate class """
    def __str__(self):
        return "X"

    @property
    def matrix(self):
        return np.matrix([[0, 1], [1, 0]])

#: Shortcut (instance of) :class:`projectq.ops.XGate`
X = NOT = XGate()


class GroundStateGate(BasicGate):
    """ Groundstate gate class """
    def __str__(self):
        return "0"

    @property
    def matrix(self):
        return np.matrix([[1, 0], [0, 0]])

#: Shortcut (instance of) :class:`projectq.ops.GroundStateGate`
Zero = GroundStateGate()


class YGate(SelfInverseGate):
    """ Pauli-Y gate class """
    def __str__(self):
        return "Y"

    @property
    def matrix(self):
        return np.matrix([[0, -1j], [1j, 0]])

#: Shortcut (instance of) :class:`projectq.ops.YGate`
Y = YGate()


class ZGate(SelfInverseGate):
    """ Pauli-Z gate class """
    def __str__(self):
        return "Z"

    @property
    def matrix(self):
        return np.matrix([[1, 0], [0, -1]])

#: Shortcut (instance of) :class:`projectq.ops.ZGate`
Z = ZGate()


class XXGate(SelfInverseGate):
    """ Pauli-X gate class on two qubits """
    def __str__(self):
        return "XX"

    @property
    def matrix(self):
        return np.matrix([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]])

#: Shortcut (instance of) :class:`projectq.ops.XXGate`
XX = XXGate()


class YYGate(SelfInverseGate):
    """ Pauli-Y gate class on two qubits """
    def __str__(self):
        return "YY"

    @property
    def matrix(self):
        return np.matrix([[0, 0, 0, -1], [0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0]])

#: Shortcut (instance of) :class:`projectq.ops.YYGate`
YY = YYGate()


class ZZGate(SelfInverseGate):
    """ Pauli-Z gate class on two qubits """
    def __str__(self):
        return "ZZ"

    @property
    def matrix(self):
        return np.matrix([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

#: Shortcut (instance of) :class:`projectq.ops.ZZGate`
ZZ = ZZGate()


class SGate(BasicGate):
    """ S gate class """
    @property
    def matrix(self):
        return np.matrix([[1, 0], [0, 1j]])

    def __str__(self):
        return "S"

#: Shortcut (instance of) :class:`projectq.ops.SGate`
S = SGate()
#: Shortcut (instance of) :class:`projectq.ops.SGate`
Sdag = Sdagger = get_inverse(S)


class TGate(BasicGate):
    """ T gate class """
    @property
    def matrix(self):
        return np.matrix([[1, 0], [0, cmath.exp(1j * cmath.pi / 4)]])

    def __str__(self):
        return "T"

#: Shortcut (instance of) :class:`projectq.ops.TGate`
T = TGate()
#: Shortcut (instance of) :class:`projectq.ops.TGate`
Tdag = Tdagger = get_inverse(T)


class SqrtXGate(BasicGate):
    """ Square-root X gate class """
    @property
    def matrix(self):
        return 0.5 * np.matrix([[1+1j, 1-1j], [1-1j, 1+1j]])

    def tex_str(self):
        return r'$\sqrt{X}$'

    def __str__(self):
        return "SqrtX"

#: Shortcut (instance of) :class:`projectq.ops.SqrtXGate`
SqrtX = SqrtXGate()


class SwapGate(SelfInverseGate, BasicMathGate):
    """ Swap gate class (swaps 2 qubits) """
    def __init__(self):
        BasicMathGate.__init__(self, lambda x, y: (y, x))
        SelfInverseGate.__init__(self)
        self.interchangeable_qubit_indices = [[0, 1]]

    def __str__(self):
        return "Swap"

    @property
    def matrix(self):
        return np.matrix([[1, 0, 0, 0],
                          [0, 0, 1, 0],
                          [0, 1, 0, 0],
                          [0, 0, 0, 1]])

#: Shortcut (instance of) :class:`projectq.ops.SwapGate`
Swap = SwapGate()


class SqrtSwapGate(BasicGate):
    """ Square-root Swap gate class """
    def __init__(self):
        BasicGate.__init__(self)
        self.interchangeable_qubit_indices = [[0, 1]]

    def __str__(self):
        return "SqrtSwap"

    @property
    def matrix(self):
        return np.matrix([[1, 0, 0, 0],
                          [0, 0.5+0.5j, 0.5-0.5j, 0],
                          [0, 0.5-0.5j, 0.5+0.5j, 0],
                          [0, 0, 0, 1]])

#: Shortcut (instance of) :class:`projectq.ops.SqrtSwapGate`
SqrtSwap = SqrtSwapGate()


class EntangleGate(BasicGate):
    """
    Entangle gate (Hadamard on first qubit, followed by CNOTs applied to all
    other qubits).
    """
    def __str__(self):
        return "Entangle"

#: Shortcut (instance of) :class:`projectq.ops.EntangleGate`
Entangle = EntangleGate()


class Ph(BasicPhaseGate):
    """ Phase gate (global phase) """
    @property
    def matrix(self):
        return np.matrix([[cmath.exp(1j * self.angle), 0],
                          [0, cmath.exp(1j * self.angle)]])

    def __str__(self):
        return "Phase"


class Rx(BasicRotationGate):
    """ RotationX gate class """
    @property
    def matrix(self):
        return np.matrix([[math.cos(0.5 * self.angle),
                           -1j * math.sin(0.5 * self.angle)],
                          [-1j * math.sin(0.5 * self.angle),
                           math.cos(0.5 * self.angle)]])


class Ry(BasicRotationGate):
    """ RotationY gate class """
    @property
    def matrix(self):
        return np.matrix([[math.cos(0.5 * self.angle),
                           -math.sin(0.5 * self.angle)],
                          [math.sin(0.5 * self.angle),
                           math.cos(0.5 * self.angle)]])


class Rz(BasicRotationGate):
    """ RotationZ gate class """
    @property
    def matrix(self):
        return np.matrix([[cmath.exp(-.5 * 1j * self.angle), 0],
                          [0, cmath.exp(.5 * 1j * self.angle)]])


class Rxx(BasicRotationGate):
    """ RotationXX gate class """
    @property
    def matrix(self):
        return np.matrix([[cmath.cos(.5 * self.angle), 0, 0, -1j*cmath.sin(.5 * self.angle)],
                          [0, cmath.cos( .5 * self.angle), -1j*cmath.sin(.5 * self.angle), 0],
                          [0, -1j*cmath.sin(.5 * self.angle), cmath.cos( .5 * self.angle), 0],
                          [-1j*cmath.sin(.5 * self.angle), 0, 0, cmath.cos( .5 * self.angle)]])


class Ryy(BasicRotationGate):
    """ RotationYY gate class """
    @property
    def matrix(self):
        return np.matrix([[cmath.cos(.5 * self.angle), 0, 0, 1j*cmath.sin(.5 * self.angle)],
                          [0, cmath.cos( .5 * self.angle), -1j*cmath.sin(.5 * self.angle), 0],
                          [0, -1j*cmath.sin(.5 * self.angle), cmath.cos( .5 * self.angle), 0],
                          [1j*cmath.sin(.5 * self.angle), 0, 0, cmath.cos( .5 * self.angle)]])


class Rzz(BasicRotationGate):
    """ RotationZZ gate class """
    @property
    def matrix(self):
        return np.matrix([[cmath.exp(-.5 * 1j * self.angle), 0, 0, 0],
                          [0, cmath.exp( .5 * 1j * self.angle), 0, 0],
                          [0, 0, cmath.exp( .5 * 1j * self.angle), 0],
                          [0, 0, 0, cmath.exp(-.5 * 1j * self.angle)]])


# Push 1 to projectq end
class Rxy(BasicRotationGate):
    """ RotationXY gate class """
    @property
    def matrix(self):
        c = cmath.cos(.5*self.angle)
        s = cmath.sin(.5*self.angle)
        return np.matrix([[c**2, -c*s, -1j*c*s, 1j*s**2],
                          [s*c, c**2, -1j*s**2, -1j*s*c],
                          [-1j*s*c,1j*s**2,c**2,-s*c],
                          [-1j*s**2,-1j*s*c,s*c,c**2]])

    def __str__(self):
        return "Rxy"

class Ryx(BasicRotationGate):
    """ RotationYX gate class """
    @property
    def matrix(self):
        c = cmath.cos(.5*self.angle)
        s = cmath.sin(.5*self.angle)
        return np.matrix([[c**2, -1j*c*s, -c*s, 1j*s**2],
                          [-1j*s*c, c**2, 1j*s**2, -s*c],
                          [s*c,-1j*s**2,c**2,-1j*s*c],
                          [-1j*s**2,s*c,-1j*s*c,c**2]])

    def __str__(self):
        return "Ryx"

class Rzy(BasicRotationGate):
    """ RotationZY gate class """
    @property
    def matrix(self):
        c = cmath.cos(.5*self.angle)
        s = cmath.sin(.5*self.angle)
        e = cmath.exp(-.5 * 1j * self.angle)
        return np.matrix([[e*c,-e*s,0,0],
                          [e*s,e*c,0,0],
                          [0,0,c/e,-s/e],
                          [0,0,s/e,c/e]])

    def __str__(self):
        return "Rzy"

class Ryz(BasicRotationGate):
    """ RotationYZ gate class """
    @property
    def matrix(self):
        c = cmath.cos(.5*self.angle)
        s = cmath.sin(.5*self.angle)
        e = cmath.exp(-.5 * 1j * self.angle)
        return np.matrix([[e*c,0,-e*s,0],
                          [0,c/e,0,-s/e],
                          [e*s,0,e*c,0],
                          [0,s/e,0,c/e]])

    def __str__(self):
        return "Ryz"

class Rzx(BasicRotationGate):
    """ RotationZX gate class """
    @property
    def matrix(self):
        c = cmath.cos(.5*self.angle)
        s = cmath.sin(.5*self.angle)
        e = cmath.exp(-.5 * 1j * self.angle)
        return np.matrix([[e*c,-1j*e*s,0,0],
                          [-1j*e*s,e*c,0,0],
                          [0,0,c/e,-1j*s/e],
                          [0,0,-1j*s/e,c/e]])

    def __str__(self):
        return "Rzx"

class Rxz(BasicRotationGate):
    """ RotationXZ gate class """
    @property
    def matrix(self):
        c = cmath.cos(.5*self.angle)
        s = cmath.sin(.5*self.angle)
        e = cmath.exp(-.5 * 1j * self.angle)
        return np.matrix([[e*c,0,-1j*e*s,0],
                          [0,c/e,0,-1j*s/e],
                          [-1j*e*s,0,e*c,0],
                          [0,-1j*s/e,0,c/e]])

    def __str__(self):
        return "Rxz"

class Rxxyy(BasicRotationGate):
    """ RotationXXYY gate class """
    @property
    def matrix(self):
        return np.matrix([[1, 0, 0, 0],
                          [0, cmath.cos(self.angle), -1j*cmath.sin(self.angle), 0],
                          [0, -1j*cmath.sin(self.angle), cmath.cos(self.angle), 0],
                          [0, 0, 0, 1]])

    def __str__(self):
        return "Rxxyy"

class Rzzx(BasicRotationGate):
    """ RotationZZX gate class """
    @property
    def matrix(self):
        s1 = cmath.sin(self.angle/2)
        s2 = cmath.sin(cmath.sqrt(5)*self.angle/2)/cmath.sqrt(5)
        c1 = cmath.cos(self.angle/2)
        c2 = cmath.cos(cmath.sqrt(5)*self.angle/2)
        a1 = .5*1j*(s1+s2)
        a2 = .5*1j*(s1-s2)
        a3 = .5*(c1+c2)
        a4 = .5*(c1-c2)
        b = -1j*s2

        return np.matrix([[-a1+a3, b, b, a2-a4],
                         [b, a1+a3, -a2-a4, b],
                         [b, -a2-a4, a1+a3, b],
                         [a2-a4, b, b, -a1+a3]])

    #return la.expm(-.5 * 1j * self.angle * np.array([[1,.5,.5,0],[.5,-1,0,.5],[.5,0,-1,.5],[0,.5,.5,1]]))

    def __str__(self):
        return "Rzzx"


''' This does not work / If it was working, the implementation does not to support a speedup for this
realization of the z-rotation layer.
class allRz(MatrixGate):
    """ Experimental combination of all pairwise z-rotations to give one matrix """

    def __init__(self, angles, ordering):
        mat = np.ones(1)
        for a in angles:
            mat = np.kron(mat, np.array([cmath.exp(-.5* 1j* a), cmath.exp(.5* 1j* a),cmath.exp(.5* 1j* a), cmath.exp(-.5* 1j* a)]))
        mat = mat.reshape([2]*2*len(angles))
        mat = np.transpose( mat, ordering ).reshape(2**(2*len(angles))) 
        MatrixGate.__init__(self, matrix = np.diag(mat))
        self.angles = angles
        self.ordering = ordering

    def get_inverse(self):
        return allRz(-self.angles, self.ordering)
'''


class R(BasicPhaseGate):
    """ Phase-shift gate (equivalent to Rz up to a global phase) """
    @property
    def matrix(self):
        return np.matrix([[1, 0], [0, cmath.exp(1j * self.angle)]])


class FlushGate(FastForwardingGate):
    """
    Flush gate (denotes the end of the circuit).

    Note:
        All compiler engines (cengines) which cache/buffer gates are obligated
        to flush and send all gates to the next compiler engine (followed by
        the flush command).

    Note:
        This gate is sent when calling

        .. code-block:: python

            eng.flush()

        on the MainEngine `eng`.
    """

    def __str__(self):
        return ""


class MeasureGate(FastForwardingGate):
    """ Measurement gate class (for single qubits)."""
    def __str__(self):
        return "Measure"

    def __or__(self, qubits):
        """
        Previously (ProjectQ <= v0.3.6) MeasureGate/Measure was allowed to be
        applied to any number of quantum registers. Now the MeasureGate/Measure
        is strictly a single qubit gate. In the coming releases the backward
        compatibility will be removed!
        """
        num_qubits = 0
        for qureg in self.make_tuple_of_qureg(qubits):
            for qubit in qureg:
                num_qubits += 1
                cmd = self.generate_command(([qubit],))
                apply_command(cmd)
        if num_qubits > 1:
            warnings.warn("Pending syntax change in future versions of "
                          "ProjectQ: \n Measure will be a single qubit gate "
                          "only. Use `All(Measure) | qureg` instead to "
                          "measure multiple qubits.")

#: Shortcut (instance of) :class:`projectq.ops.MeasureGate`
Measure = MeasureGate()


class AllocateQubitGate(ClassicalInstructionGate):
    """ Qubit allocation gate class """
    def __str__(self):
        return "Allocate"

    def get_inverse(self):
        return DeallocateQubitGate()

#: Shortcut (instance of) :class:`projectq.ops.AllocateQubitGate`
Allocate = AllocateQubitGate()


class DeallocateQubitGate(FastForwardingGate):
    """ Qubit deallocation gate class """
    def __str__(self):
        return "Deallocate"

    def get_inverse(self):
        return Allocate

#: Shortcut (instance of) :class:`projectq.ops.DeallocateQubitGate`
Deallocate = DeallocateQubitGate()


class AllocateDirtyQubitGate(ClassicalInstructionGate):
    """ Dirty qubit allocation gate class """
    def __str__(self):
        return "AllocateDirty"

    def get_inverse(self):
        return Deallocate

#: Shortcut (instance of) :class:`projectq.ops.AllocateDirtyQubitGate`
AllocateDirty = AllocateDirtyQubitGate()


class BarrierGate(BasicGate):
    """ Barrier gate class """
    def __str__(self):
        return "Barrier"

    def get_inverse(self):
        return Barrier

#: Shortcut (instance of) :class:`projectq.ops.BarrierGate`
Barrier = BarrierGate()


class FlipBits(SelfInverseGate):
    """ Gate for flipping qubits by means of XGates """
    def __init__(self, bits_to_flip):
        """
        Initialize FlipBits gate.

        Example:
            .. code-block:: python

                qureg = eng.allocate_qureg(2)
                FlipBits([0, 1]) | qureg

        Args:
            bits_to_flip(list[int]|list[bool]|str|int): int or array of 0/1,
               True/False, or string of 0/1 identifying the qubits to flip.
               In case of int, the bits to flip are determined from the
               binary digits, with the least significant bit corresponding
               to qureg[0]. If bits_to_flip is negative, exactly all qubits
               which would not be flipped for the input -bits_to_flip-1 are
               flipped, i.e., bits_to_flip=-1 flips all qubits.
        """
        SelfInverseGate.__init__(self)
        if isinstance(bits_to_flip, int):
            self.bits_to_flip = bits_to_flip
        else:
            self.bits_to_flip = 0
            for i in reversed(list(bits_to_flip)):
                bit = 0b1 if i == '1' or i == 1 or i is True else 0b0
                self.bits_to_flip = (self.bits_to_flip << 1) | bit

    def __str__(self):
        return "FlipBits("+str(self.bits_to_flip)+")"

    def __or__(self, qubits):
        quregs_tuple = self.make_tuple_of_qureg(qubits)
        if len(quregs_tuple) > 1:
            raise ValueError(self.__str__()+' can only be applied to qubits,'
                             'quregs, arrays of qubits, and tuples with one'
                             'individual qubit')
        for qureg in quregs_tuple:
            for i, qubit in enumerate(qureg):
                if (self.bits_to_flip >> i) & 1:
                    XGate() | qubit

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.bits_to_flip == other.bits_to_flip
        return False

    def __hash__(self):
        return hash(self.__str__())
