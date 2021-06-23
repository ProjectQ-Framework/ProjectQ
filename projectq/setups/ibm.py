# -*- coding: utf-8 -*-
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
Defines a setup allowing to compile code for the IBM quantum chips:
->Any 5 qubit devices
->the ibmq online simulator
->the melbourne 15 qubit device

It provides the `engine_list` for the `MainEngine' based on the requested
device.  Decompose the circuit into a Rx/Ry/Rz/H/CNOT gate set that will be
translated in the backend in the U1/U2/U3/CX gate set.
"""

from projectq.setups import restrictedgateset
from projectq.ops import Rx, Ry, Rz, H, CNOT, Barrier
from projectq.cengines import (
    LocalOptimizer,
    IBM5QubitMapper,
    SwapAndCNOTFlipper,
    BasicMapperEngine,
    GridMapper,
)
from projectq.backends._ibm._ibm_http_client import show_devices


def get_engine_list(token=None, device=None):
    """
    Return the default list of compiler engine for the IBM QE platform
    """
    # Access to the hardware properties via show_devices
    # Can also be extended to take into account gate fidelities, new available
    # gate, etc..
    devices = show_devices(token)
    ibm_setup = []
    if device not in devices:
        raise DeviceOfflineError('Error when configuring engine list: device requested for Backend not connected')
    if devices[device]['nq'] == 5:
        # The requested device is a 5 qubit processor
        # Obtain the coupling map specific to the device
        coupling_map = devices[device]['coupling_map']
        coupling_map = list2set(coupling_map)
        mapper = IBM5QubitMapper(coupling_map)
        ibm_setup = [mapper, SwapAndCNOTFlipper(coupling_map), LocalOptimizer(10)]
    elif device == 'ibmq_qasm_simulator':
        # The 32 qubit online simulator doesn't need a specific mapping for
        # gates. Can also run wider gateset but this setup keep the
        # restrictedgateset setup for coherence
        mapper = BasicMapperEngine()
        # Note: Manual Mapper doesn't work, because its map is updated only if
        # gates are applied if gates in the register are not used, then it
        # will lead to state errors
        res = dict()
        for i in range(devices[device]['nq']):
            res[i] = i
        mapper.current_mapping = res
        ibm_setup = [mapper]
    elif device == 'ibmq_16_melbourne':
        # Only 15 qubits available on this ibmqx2 unit(in particular qubit 7
        # on the grid), therefore need custom grid mapping
        grid_to_physical = {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
            6: 6,
            7: 15,
            8: 14,
            9: 13,
            10: 12,
            11: 11,
            12: 10,
            13: 9,
            14: 8,
            15: 7,
        }
        coupling_map = devices[device]['coupling_map']
        coupling_map = list2set(coupling_map)
        ibm_setup = [
            GridMapper(2, 8, grid_to_physical),
            LocalOptimizer(5),
            SwapAndCNOTFlipper(coupling_map),
            LocalOptimizer(5),
        ]
    else:
        # If there is an online device not handled into ProjectQ it's not too
        # bad, the engine_list can be constructed manually with the
        # appropriate mapper and the 'coupling_map' parameter
        raise DeviceNotHandledError('Device not yet fully handled by ProjectQ')

    # Most IBM devices accept U1,U2,U3,CX gates.
    # Most gates need to be decomposed into a subset that is manually converted
    # in the backend (until the implementation of the U1,U2,U3)
    # available gates decomposable now for U1,U2,U3: Rx,Ry,Rz and H
    setup = restrictedgateset.get_engine_list(
        one_qubit_gates=(Rx, Ry, Rz, H), two_qubit_gates=(CNOT,), other_gates=(Barrier,)
    )
    setup.extend(ibm_setup)
    return setup


class DeviceOfflineError(Exception):
    """Exception raised if a selected device is currently offline"""


class DeviceNotHandledError(Exception):
    """Exception raised if a selected device is cannot handle the circuit"""


def list2set(coupling_list):
    """
    Convert a list() to a set()
    """
    result = []
    for element in coupling_list:
        result.append(tuple(element))
    return set(result)
