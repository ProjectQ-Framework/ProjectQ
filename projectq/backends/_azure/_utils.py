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
    Allocate,
    Barrier,
    Deallocate,
    HGate,
    Measure,
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


IONQ_PROVIDER_ID = 'ionq'
HONEYWELL_PROVIDER_ID = 'honeywell'

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
}

IONQ_SUPPORTED_GATES = tuple(IONQ_GATE_MAP.keys())

HONEYWELL_GATE_MAP = {
    HGate: 'h',
    Measure: 'measure',
    Rx: 'rx',
    Ry: 'ry',
    Rz: 'rz',
    Sdag: 'sdg',
    SGate: 's',
    Tdag: 'tdg',
    TGate: 't',
    XGate: 'x',
    YGate: 'y',
    ZGate: 'z'
}

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
        supported_transpose = gate in (Sdag, Tdag)
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
        return isinstance(gate, (XGate,))

    # Gates without control bits.
    if num_ctrl_qubits == 0:
        supported = isinstance(gate, HONEYWELL_SUPPORTED_GATES)
        supported_transpose = gate in (Sdag, Tdag)
        return supported or supported_transpose

    return False


def is_available(provider_id, cmd):
    gate = cmd.gate

    # Metagates.
    if gate in (Measure, Allocate, Deallocate, Barrier):
        return True

    if provider_id == IONQ_PROVIDER_ID:
        return _is_available_ionq(cmd)
    elif provider_id == HONEYWELL_PROVIDER_ID:
        return _is_available_honeywell(cmd)

    return False


def _convert_ionq_json(cmd):
    pass


def _convert_qasm(cmd):
    pass


def convert(provider_id, cmd):
    if provider_id == IONQ_PROVIDER_ID:
        return _convert_ionq_json(cmd)
    elif provider_id == HONEYWELL_PROVIDER_ID:
        return _convert_qasm(cmd)
