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
from projectq.ops import (
    AllocateQubitGate,
    BarrierGate,
    DaggeredGate,
    DeallocateQubitGate,
    HGate,
    MeasureGate,
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
HONEYWELL_PROVIDER_ID = 'honeywell'

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
}  # excluding controlled and conjugate-transpose gates

IONQ_SUPPORTED_GATES = tuple(IONQ_GATE_MAP.keys())

HONEYWELL_GATE_MAP = {
    HGate: 'h',
    Rx: 'rx',
    Rxx: 'xx',
    Ry: 'ry',
    Ryy: 'yy',
    Rz: 'rz',
    Rzz: 'zz',
    SGate: 's',
    TGate: 't',
    XGate: 'x',
    YGate: 'y',
    ZGate: 'z'
}  # excluding controlled and conjugate-transpose gates

HONEYWELL_SUPPORTED_GATES = tuple(HONEYWELL_GATE_MAP.keys())


def _is_available_ionq(cmd):
    gate = cmd.gate

    if has_negative_control(cmd):
        return False

    num_ctrl_qubits = get_control_count(cmd)

    # NOTE: IonQ supports up to 7 control qubits
    if 0 < num_ctrl_qubits <= 7:
        return isinstance(gate, (XGate,))

    # Gates without control bits.
    if num_ctrl_qubits == 0:
        supported = isinstance(gate, IONQ_SUPPORTED_GATES)
        supported_transpose = gate in (Sdag, Tdag)  # TODO: Add support for transpose of square-root-of-not (vi) gate
        return supported or supported_transpose

    return False


def _is_available_honeywell(cmd):
    gate = cmd.gate

    # TODO: NEEDED CONFORMATION- Does Honeywell support negatively controlled qubits?
    if has_negative_control(cmd):
        return False

    num_ctrl_qubits = get_control_count(cmd)

    # TODO: NEEDED CONFORMATION- How many control qubits Honeywell supports?
    if 0 < num_ctrl_qubits <= 2:
        return isinstance(gate, (XGate, ZGate))  # TODO: NEEDED CONFORMATION- Any control count difference CX and CZ?

    # Gates without control bits.
    if num_ctrl_qubits == 0:
        supported = isinstance(gate, HONEYWELL_SUPPORTED_GATES)
        supported_transpose = gate in (Sdag, Tdag)  # TODO: Add support for transpose of square-root-of-not (vi) gate
        return supported or supported_transpose

    return False


def is_available(provider_id, cmd):
    gate = cmd.gate

    # Metagates.
    if isinstance(gate, (MeasureGate, AllocateQubitGate, DeallocateQubitGate, BarrierGate)):
        return True

    if provider_id == IONQ_PROVIDER_ID:
        return _is_available_ionq(cmd)
    elif provider_id == HONEYWELL_PROVIDER_ID:
        return _is_available_honeywell(cmd)

    return False


def convert_cmd_to_ionq_format(cmd):
    gate = cmd.gate

    # No-op/Meta gates.
    if isinstance(gate, BarrierGate):
        return  # TODO: Handle return type `None`

    # Process the Command's gate type
    gate_type = type(gate)
    gate_name = IONQ_GATE_MAP.get(gate_type)

    # Daggered gates get special treatment.
    if isinstance(gate, DaggeredGate):
        gate_name = gate_name + 'i'

    # Unable to determine a gate mapping here, so raise out.
    if gate_name is None:
        raise InvalidCommandError(
            'Command not authorized. You should run the circuit with the appropriate Azure Quantum setup.'
        )

    # Now make sure there are no existing measurements on qubits involved
    #   in this operation.
    targets = [qb.id for qureg in cmd.qubits for qb in qureg]
    controls = [qb.id for qb in cmd.control_qubits]

    # Initialize the gate dict:
    gate_dict = {
        'gate': gate_name,
        'targets': targets,
    }

    # Check if we have a rotation
    if isinstance(gate, (R, Rx, Ry, Rz, Rxx, Ryy, Rzz)):
        gate_dict['rotation'] = gate.angle

    # Set controls
    if len(controls) > 0:
        gate_dict['controls'] = controls

    return gate_dict


def convert_cmd_to_qasm_format(cmd):
    gate = cmd.gate

    if isinstance(gate, BarrierGate):
        qb_pos = [qb.id for qr in cmd.qubits for qb in qr]
        qb_str = ""
        for pos in qb_pos:
            qb_str += "q[{}], ".format(pos)
        return "barrier " + qb_str[:-2] + ";"
    elif isinstance(gate, XGate) and get_control_count(cmd) == 1:
        ctrl_pos = cmd.control_qubits[0].id
        qb_pos = cmd.qubits[0][0].id
        return "cx q[{}], q[{}];".format(ctrl_pos, qb_pos)
    elif isinstance(gate, (Rx, Ry, Rz)):
        qb_pos = cmd.qubits[0][0].id
        u_strs = {'Rx': 'u3({}, -pi/2, pi/2)', 'Ry': 'u3({}, 0, 0)', 'Rz': 'u1({})'}
        gate_qasm = u_strs[str(gate)[0:2]].format(gate.angle)
        return "{} q[{}];".format(gate_qasm, qb_pos)
    elif isinstance(gate, HGate):
        qb_pos = cmd.qubits[0][0].id
        return "h q[{}];".format(qb_pos)
    else:
        raise InvalidCommandError(
            'Command not authorized. You should run the circuit with the appropriate Azure Quantum setup.'
        )
