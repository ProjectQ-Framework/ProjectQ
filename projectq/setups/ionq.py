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
Defines a setup allowing to compile code for IonQ trapped ion devices:
->The 11 qubit device
->The 29 qubits simulator
"""
from projectq.backends._ionq._ionq_exc import DeviceOfflineError
from projectq.backends._ionq._ionq_http_client import show_devices
from projectq.backends._ionq._ionq_mapper import BoundedQubitMapper
from projectq.ops import (
    Barrier,
    H,
    Rx,
    Rxx,
    Ry,
    Ryy,
    Rz,
    Rzz,
    S,
    Sdag,
    SqrtX,
    Swap,
    T,
    Tdag,
    X,
    Y,
    Z,
)
from projectq.setups import restrictedgateset


def get_engine_list(token=None, device=None):
    """
    Return the default list of compiler engine for the IonQ platform
    """
    devices = show_devices(token)
    if not device or device not in devices:
        raise DeviceOfflineError("Error checking engine list: no '{}' devices available".format(device))

    #
    # Qubit mapper
    #
    mapper = BoundedQubitMapper(devices[device]['nq'])

    #
    # Basis Gates
    #

    # Declare the basis gateset for the IonQ's API.
    engine_list = restrictedgateset.get_engine_list(
        one_qubit_gates=(X, Y, Z, Rx, Ry, Rz, H, S, Sdag, T, Tdag, SqrtX),
        two_qubit_gates=(Swap, Rxx, Ryy, Rzz),
        other_gates=(Barrier,),
    )
    return engine_list + [mapper]


__all__ = ['get_engine_list']
