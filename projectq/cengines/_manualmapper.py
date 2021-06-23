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
Contains a compiler engine to add mapping information
"""
from ._basicmapper import BasicMapperEngine


class ManualMapper(BasicMapperEngine):
    """
    Manual Mapper which adds QubitPlacementTags to Allocate gate commands according to a user-specified mapping.

    Attributes:
        map (function): The function which maps a given qubit id to its location. It gets set when initializing the
            mapper.
    """

    def __init__(self, map_fun=lambda x: x):
        """
        Initialize the mapper to a given mapping. If no mapping function is provided, the qubit id is used as the
        location.

        Args:
            map_fun (function): Function which, given the qubit id, returns an integer describing the physical
                location (must be constant).
        """
        super().__init__()
        self.map = map_fun
        self.current_mapping = dict()

    def receive(self, command_list):
        """
        Receives a command list and passes it to the next engine, adding qubit placement tags to allocate gates.

        Args:
            command_list (list of Command objects): list of commands to receive.
        """
        for cmd in command_list:
            ids = [qb.id for qr in cmd.qubits for qb in qr]
            ids += [qb.id for qb in cmd.control_qubits]
            for qubit_id in ids:
                if qubit_id not in self.current_mapping:
                    self._current_mapping[qubit_id] = self.map(qubit_id)
            self._send_cmd_with_mapped_ids(cmd)
