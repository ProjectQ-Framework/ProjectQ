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
Registers decomposition for UnformlyControlledRy and UnformlyControlledRz.
"""

from projectq.cengines import DecompositionRule
from projectq.meta import Compute, Uncompute, CustomUncompute
from projectq.ops import (CNOT, Ry, Rz,
                          UniformlyControlledRy,
                          UniformlyControlledRz)


def _apply_ucr_n(angles, control_qubits, target_qubit, eng, gate_class):
    if len(control_qubits) == 0:
        gate_class(angles[0]) | target_qubit
    else:
        if _apply_ucr_n.rightmost_cnot[len(control_qubits)]:
            angles1 = []
            angles2 = []
            for lower_bits in range(2**(len(control_qubits)-1)):
                leading_0 = angles[lower_bits]
                leading_1 = angles[lower_bits + 2**(len(control_qubits)-1)]
                angles1.append((leading_0 + leading_1)/2.)
                angles2.append((leading_0 - leading_1)/2.)
        else:
            angles1 = []
            angles2 = []
            for lower_bits in range(2**(len(control_qubits)-1)):
                leading_0 = angles[lower_bits]
                leading_1 = angles[lower_bits + 2**(len(control_qubits)-1)]
                angles1.append((leading_0 - leading_1)/2.)
                angles2.append((leading_0 + leading_1)/2.)
        _apply_ucr_n(angles=angles1,
                     control_qubits=control_qubits[:-1],
                     target_qubit=target_qubit,
                     eng=eng,
                     gate_class=gate_class)
        # Very custom usage of Compute/CustomUncompute in the following.
        if _apply_ucr_n.rightmost_cnot[len(control_qubits)]:
            with Compute(eng):
                CNOT | (control_qubits[-1], target_qubit)
        else:
            with CustomUncompute(eng):
                CNOT | (control_qubits[-1], target_qubit)
        _apply_ucr_n(angles=angles2,
                     control_qubits=control_qubits[:-1],
                     target_qubit=target_qubit,
                     eng=eng,
                     gate_class=gate_class)
        # Next iteration on this level do the other cnot placement
        _apply_ucr_n.rightmost_cnot[len(control_qubits)] = (
            not _apply_ucr_n.rightmost_cnot[len(control_qubits)])


def _decompose_ucr(cmd, gate_class):
    """
    Decomposition for an uniformly controlled single qubit rotation gate.

    Follows decomposition in arXiv:quant-ph/0407010 section II and
    arXiv:quant-ph/0410066v2 Fig. 9a.

    For Ry and Rz it uses 2**len(control_qubits) CNOT and also
    2**len(control_qubits) single qubit rotations.

    Args:
        cmd: CommandObject to decompose.
        gate_class: Ry or Rz
    """
    eng = cmd.engine
    if not (len(cmd.qubits) == 2 and len(cmd.qubits[1]) == 1 and
            len(cmd.qubits[0]) > 0):
        raise TypeError("Wrong number of qubits ")
    control_qubits = cmd.qubits[0]
    target_qubit = cmd.qubits[1]
    angles1 = []
    angles2 = []
    for lower_bits in range(2**(len(control_qubits)-1)):
        leading_0 = cmd.gate.angles[lower_bits]
        leading_1 = cmd.gate.angles[lower_bits + 2**(len(control_qubits)-1)]
        angles1.append((leading_0 + leading_1)/2.)
        angles2.append((leading_0 - leading_1)/2.)
    _apply_ucr_n.rightmost_cnot = {}
    for i in range(len(control_qubits) + 1):
        _apply_ucr_n.rightmost_cnot[i] = True
    _apply_ucr_n(angles=angles1,
                 control_qubits=control_qubits[:-1],
                 target_qubit=target_qubit,
                 eng=eng,
                 gate_class=gate_class)
    # Very custom usage of Compute/CustomUncompute in the following.
    with Compute(cmd.engine):
        CNOT | (control_qubits[-1], target_qubit)
    _apply_ucr_n(angles=angles2,
                 control_qubits=control_qubits[:-1],
                 target_qubit=target_qubit,
                 eng=eng,
                 gate_class=gate_class)
    with CustomUncompute(eng):
        CNOT | (control_qubits[-1], target_qubit)


def _decompose_ucry(cmd):
    return _decompose_ucr(cmd, gate_class=Ry)


def _decompose_ucrz(cmd):
    return _decompose_ucr(cmd, gate_class=Rz)


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(UniformlyControlledRy, _decompose_ucry),
    DecompositionRule(UniformlyControlledRz, _decompose_ucrz)
]
