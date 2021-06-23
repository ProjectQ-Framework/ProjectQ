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
"""
Defines a setup allowing to compile code for the AWS Braket devices:
->The 11 qubits IonQ device
->The 32 qubits Rigetti device
->The up to 34 qubits SV1 state vector simulator

It provides the `engine_list` for the `MainEngine' based on the requested
device.  Decompose the circuit into the available gate set for each device
that will be used in the backend.
"""

from projectq.setups import restrictedgateset
from projectq.ops import (
    R,
    Swap,
    H,
    Rx,
    Ry,
    Rz,
    S,
    Sdag,
    T,
    Tdag,
    X,
    Y,
    Z,
    SqrtX,
    Barrier,
)
from projectq.backends._awsbraket._awsbraket_boto3_client import show_devices


def get_engine_list(credentials=None, device=None):
    """
    Return the default list of compiler engine for the AWS Braket platform.
    """
    # Access to the hardware properties via show_devices
    # Can also be extended to take into account gate fidelities, new available
    # gate, etc..
    devices = show_devices(credentials)
    if device not in devices:
        raise DeviceOfflineError('Error when configuring engine list: device requested for Backend not available')

    # We left the real device to manage the mapping and optimizacion: "The IonQ
    # and Rigetti devices compile the provided circuit into their respective
    # native gate sets automatically, and they map the abstract qubit indices
    # to physical qubits on the respective QPU."
    # (see: https://docs.aws.amazon.com/braket/latest/developerguide/braket-submit-to-qpu.html)

    # TODO: Investigate if explicit mapping is an advantage

    if device == 'SV1':
        setup = restrictedgateset.get_engine_list(
            one_qubit_gates=(R, H, Rx, Ry, Rz, S, Sdag, T, Tdag, X, Y, Z, SqrtX),
            two_qubit_gates=(Swap,),
            other_gates=(Barrier,),
        )
        return setup
    if device == 'Aspen-8':
        setup = restrictedgateset.get_engine_list(
            one_qubit_gates=(R, H, Rx, Ry, Rz, S, Sdag, T, Tdag, X, Y, Z),
            two_qubit_gates=(Swap,),
            other_gates=(Barrier,),
        )
        return setup
    if device == 'IonQ Device':
        setup = restrictedgateset.get_engine_list(
            one_qubit_gates=(H, Rx, Ry, Rz, S, Sdag, T, Tdag, X, Y, Z, SqrtX),
            two_qubit_gates=(Swap,),
            other_gates=(Barrier,),
        )
        return setup
    raise RuntimeError('Unsupported device type: {}!'.format(device))  # pragma: no cover


class DeviceOfflineError(Exception):
    """Exception raised if a selected device is currently offline"""
