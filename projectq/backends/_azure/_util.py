# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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

from projectq.meta import get_control_count, has_negative_control
from projectq.ops import get_inverse
from projectq.ops import (
    AllocateQubitGate,
    BarrierGate,
    ControlledGate,
    DeallocateQubitGate,
    DaggeredGate,
    MeasureGate,
    HGate,
    R,
    Rx,
    Rxx,
    Ry,
    Ryy,
    Rz,
    Rzz,
    Sdag,
    SGate,
    SqrtXGate,
    SwapGate,
    Tdag,
    TGate,
    XGate,
    YGate,
    ZGate
)

from .._exceptions import InvalidCommandError


IONQ_PROVIDER_ID = 'ionq'
QUANTINUUM_PROVIDER_ID = 'quantinuum'

# https://docs.ionq.com/#section/Supported-Gates
IONQ_GATE_MAP = {
    HGate: 'h',
    SGate: 's',
    SqrtXGate: 'v',
    SwapGate: 'swap',
    TGate: 't',
    Rx: 'rx',
    Rxx: 'xx',
    Ry: 'ry',
    Ryy: 'yy',
    Rz: 'rz',
    Rzz: 'zz',
    XGate: 'x',
    YGate: 'y',
    ZGate: 'z',
}  # excluding controlled, conjugate-transpose and meta gates

IONQ_SUPPORTED_GATES = tuple(IONQ_GATE_MAP.keys())

QUANTINUUM_GATE_MAP = {
    BarrierGate: 'barrier',
    HGate: 'h',
    Rx: 'rx',
    Rxx: 'rxx',
    Ry: 'ry',
    Ryy: 'ryy',
    Rz: 'rz',
    Rzz: 'rzz',
    SGate: 's',
    TGate: 't',
    XGate: 'x',
    YGate: 'y',
    ZGate: 'z'
}  # excluding controlled, conjugate-transpose and meta gates

QUANTINUUM_SUPPORTED_GATES = tuple(QUANTINUUM_GATE_MAP.keys())

V = SqrtXGate()
Vdag = get_inverse(V)


def is_available_ionq(cmd):
    """
    Test if IonQ backend is available to process the provided command.

    Args:
        cmd (Command): A command to process.

    Returns:
        bool: If this backend can process the command.
    """
    gate = cmd.gate

    if has_negative_control(cmd):
        return False

    if isinstance(gate, ControlledGate):
        num_ctrl_qubits = gate._n  # noqa
    else:
        num_ctrl_qubits = get_control_count(cmd)

    # Get base gate wrapped in ControlledGate classes
    while isinstance(gate, ControlledGate):
        gate = gate._gate  # noqa

    # NOTE: IonQ supports up to 7 control qubits
    if 0 < num_ctrl_qubits <= 7:
        return isinstance(gate, (XGate,))

    # Gates without control bits
    if num_ctrl_qubits == 0:
        supported = isinstance(gate, IONQ_SUPPORTED_GATES)
        supported_meta = isinstance(gate, (MeasureGate, AllocateQubitGate, DeallocateQubitGate))
        supported_transpose = gate in (Sdag, Tdag, Vdag)

        return supported or supported_meta or supported_transpose

    return False


def is_available_quantinuum(cmd):
    """
    Test if Quantinuum backend is available to process the provided command.

    Args:
        cmd (Command): A command to process.

    Returns:
        bool: If this backend can process the command.
    """
    gate = cmd.gate

    if has_negative_control(cmd):
        return False

    if isinstance(gate, ControlledGate):
        num_ctrl_qubits = gate._n  # noqa
    else:
        num_ctrl_qubits = get_control_count(cmd)

    # Get base gate wrapped in ControlledGate classes
    while isinstance(gate, ControlledGate):
        gate = gate._gate  # noqa

    # TODO: NEEDED CONFORMATION- Does Quantinuum support more than 2 control gates?
    if 0 < num_ctrl_qubits <= 2:
        return isinstance(gate, (XGate, ZGate))

    # Gates without control bits.
    if num_ctrl_qubits == 0:
        supported = isinstance(gate, QUANTINUUM_SUPPORTED_GATES)
        supported_meta = isinstance(gate, (MeasureGate, AllocateQubitGate, DeallocateQubitGate, BarrierGate))
        supported_transpose = gate in (Sdag, Tdag)
        return supported or supported_meta or supported_transpose

    return False


def to_json(cmd):
    """
    Convert ProjectQ command to JSON format.

    Args:
        cmd (Command): A command to process.

    Returns:
        dict: JSON format of given command.
    """
    # Invalid command, raise exception
    if not is_available_ionq(cmd):
        raise InvalidCommandError('Invalid command:', str(cmd))

    gate = cmd.gate

    if isinstance(gate, ControlledGate):
        inner_gate = gate._gate  # noqa
        while isinstance(inner_gate, ControlledGate):
            inner_gate = inner_gate._gate  # noqa
        gate_type = type(inner_gate)
    elif isinstance(gate, DaggeredGate):
        gate_type = type(gate.get_inverse())
    else:
        gate_type = type(gate)

    gate_name = IONQ_GATE_MAP.get(gate_type)

    # Daggered gates get special treatment
    if isinstance(gate, DaggeredGate):
        gate_name = gate_name + 'i'

    # Controlled gates get special treatment too
    if isinstance(gate, ControlledGate):
        all_qubits = [qb.id for qureg in cmd.qubits for qb in qureg]
        controls = all_qubits[:gate._n]  # noqa
        targets = all_qubits[gate._n:]  # noqa
    else:
        controls = [qb.id for qb in cmd.control_qubits]
        targets = [qb.id for qureg in cmd.qubits for qb in qureg]

    # Initialize the gate dict
    gate_dict = {
        'gate': gate_name,
        'targets': targets
    }

    # Check if we have a rotation
    if isinstance(gate, (R, Rx, Ry, Rz, Rxx, Ryy, Rzz)):
        gate_dict['rotation'] = gate.angle

    # Set controls
    if len(controls) > 0:
        gate_dict['controls'] = controls

    return gate_dict


def to_qasm(cmd):
    """
    Convert ProjectQ command to QASM format.

    Args:
        cmd (Command): A command to process.

    Returns:
        dict: QASM format of given command.
    """
    # Invalid command, raise exception
    if not is_available_quantinuum(cmd):
        raise InvalidCommandError('Invalid command:', str(cmd))

    gate = cmd.gate

    if isinstance(gate, ControlledGate):
        inner_gate = gate._gate  # noqa
        while isinstance(inner_gate, ControlledGate):
            inner_gate = inner_gate._gate  # noqa
        gate_type = type(inner_gate)
    elif isinstance(gate, DaggeredGate):
        gate_type = type(gate.get_inverse())
    else:
        gate_type = type(gate)

    gate_name = QUANTINUUM_GATE_MAP.get(gate_type)

    # Daggered gates get special treatment
    if isinstance(gate, DaggeredGate):
        gate_name = gate_name + 'dg'

    # Controlled gates get special treatment too
    if isinstance(gate, ControlledGate):
        all_qubits = [qb.id for qureg in cmd.qubits for qb in qureg]
        controls = all_qubits[:gate._n]  # noqa
        targets = all_qubits[gate._n:]  # noqa
    else:
        controls = [qb.id for qb in cmd.control_qubits]
        targets = [qb.id for qureg in cmd.qubits for qb in qureg]

    # Barrier gate
    if isinstance(gate, BarrierGate):
        qb_str = ""
        for pos in targets:
            qb_str += "q[{}], ".format(pos)
        return "{} {};".format(gate_name, qb_str[:-2])

    # Daggered gates
    elif gate in (Sdag, Tdag):
        return "{} q[{}];".format(gate_name, targets[0])

    # Controlled gates
    elif len(controls) > 0:
        # 1-Controlled gates
        if len(controls) == 1:
            gate_name = 'c' + gate_name
            return "{} q[{}], q[{}];".format(gate_name, controls[0], targets[0])

        # 2-Controlled gates
        if len(controls) == 2:
            gate_name = 'cc' + gate_name
            return "{} q[{}], q[{}], q[{}];".format(
                gate_name, controls[0], controls[1], targets[0])

    # Single qubit gates
    elif len(targets) == 1:
        # Standard gates
        if isinstance(gate, (HGate, XGate, YGate, ZGate, SGate, TGate)):
            return "{} q[{}];".format(gate_name, targets[0])

        # Rotational gates
        if isinstance(gate, (Rx, Ry, Rz)):
            return "{}({}) q[{}];".format(gate_name, gate.angle, targets[0])

    # Two qubit gates
    elif len(targets) == 2:
        # Rotational gates
        if isinstance(gate, (Rxx, Ryy, Rzz)):
            return "{}({}) q[{}], q[{}];".format(gate_name, gate.angle, targets[0], targets[1])

    # Invalid command
    else:
        raise InvalidCommandError('Invalid command:', str(cmd))


def rearrange_result(input_result, length):
    """Turn ``input_result`` from an integer into a bit-string.

    Args:
        input_result (int): An integer representation of qubit states.
        length (int): The total number of bits (for padding, if needed).

    Returns:
        str: A bit-string representation of ``input_result``.
    """
    bin_input = list(bin(input_result)[2:].rjust(length, '0'))
    return ''.join(bin_input)[::-1]
