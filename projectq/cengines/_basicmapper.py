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
"""
Defines the parent class from which all mappers should be derived.

There is only one engine currently allowed to be derived from BasicMapperEngine. This allows the simulator to
automatically translate logical qubit ids to mapped ids.
"""
from copy import deepcopy

from projectq.meta import drop_engine_after, insert_engine, LogicalQubitIDTag
from projectq.ops import MeasureGate

from ._basics import BasicEngine
from ._cmdmodifier import CommandModifier


class BasicMapperEngine(BasicEngine):
    """
    Parent class for all Mappers.

    Attributes:
        self.current_mapping (dict): Keys are the logical qubit ids and values are the mapped qubit ids.

    """

    def __init__(self):
        super().__init__()
        self._current_mapping = None

    @property
    def current_mapping(self):
        """
        Access the current mapping
        """
        return deepcopy(self._current_mapping)

    @current_mapping.setter
    def current_mapping(self, current_mapping):
        """
        Set the current mapping
        """
        self._current_mapping = current_mapping

    def _send_cmd_with_mapped_ids(self, cmd):
        """
        Send this Command using the mapped qubit ids of self.current_mapping.

        If it is a Measurement gate, then it adds a LogicalQubitID tag.

        Args:
            cmd: Command object with logical qubit ids.
        """
        new_cmd = deepcopy(cmd)
        qubits = new_cmd.qubits
        for qureg in qubits:
            for qubit in qureg:
                if qubit.id != -1:
                    qubit.id = self.current_mapping[qubit.id]
        control_qubits = new_cmd.control_qubits
        for qubit in control_qubits:
            qubit.id = self.current_mapping[qubit.id]
        if isinstance(new_cmd.gate, MeasureGate):
            # Add LogicalQubitIDTag to MeasureGate
            def add_logical_id(command, old_tags=deepcopy(cmd.tags)):
                command.tags = old_tags + [LogicalQubitIDTag(cmd.qubits[0][0].id)]
                return command

            tagger_eng = CommandModifier(add_logical_id)
            insert_engine(self, tagger_eng)
            self.send([new_cmd])
            drop_engine_after(self)
        else:
            self.send([new_cmd])

    def receive(self, command_list):
        """Forward all commands to the next engine."""
        for cmd in command_list:
            self._send_cmd_with_mapped_ids(cmd)
