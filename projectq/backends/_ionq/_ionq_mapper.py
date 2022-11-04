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

"""Mapper that has a maximum number of allocatable qubits."""

from projectq.cengines import BasicMapperEngine
from projectq.meta import LogicalQubitIDTag
from projectq.ops import AllocateQubitGate, Command, DeallocateQubitGate, FlushGate
from projectq.types import WeakQubitRef


class BoundedQubitMapper(BasicMapperEngine):
    """Map logical qubits to a fixed number of hardware qubits."""

    def __init__(self, max_qubits):
        """Initialize a BoundedQubitMapper object."""
        super().__init__()
        self._qubit_idx = 0
        self.max_qubits = max_qubits

    def _reset(self):
        # Reset the mapping index.
        self._qubit_idx = 0

    def _process_cmd(self, cmd):
        current_mapping = self.current_mapping
        if current_mapping is None:
            current_mapping = {}

        if isinstance(cmd.gate, AllocateQubitGate):
            qubit_id = cmd.qubits[0][0].id
            if qubit_id in current_mapping:
                raise RuntimeError(f"Qubit with id {qubit_id} has already been allocated!")

            if self._qubit_idx >= self.max_qubits:
                raise RuntimeError(f"Cannot allocate more than {self.max_qubits} qubits!")

            new_id = self._qubit_idx
            self._qubit_idx += 1
            current_mapping[qubit_id] = new_id
            qb = WeakQubitRef(engine=self, idx=new_id)
            new_cmd = Command(
                engine=self,
                gate=AllocateQubitGate(),
                qubits=([qb],),
                tags=[LogicalQubitIDTag(qubit_id)],
            )
            self.current_mapping = current_mapping
            self.send([new_cmd])
        elif isinstance(cmd.gate, DeallocateQubitGate):
            qubit_id = cmd.qubits[0][0].id
            if qubit_id not in current_mapping:
                raise RuntimeError("Cannot deallocate a qubit that is not already allocated!")
            qb = WeakQubitRef(engine=self, idx=current_mapping[qubit_id])
            new_cmd = Command(
                engine=self,
                gate=DeallocateQubitGate(),
                qubits=([qb],),
                tags=[LogicalQubitIDTag(qubit_id)],
            )
            current_mapping.pop(qubit_id)
            self.current_mapping = current_mapping
            self.send([new_cmd])
        else:
            self._send_cmd_with_mapped_ids(cmd)

    def receive(self, command_list):
        """
        Receive a list of commands.

        Args:
            command_list (list<Command>): List of commands to receive.
        """
        for cmd in command_list:
            if isinstance(cmd.gate, FlushGate):
                self._reset()
                self.send([cmd])
            else:
                self._process_cmd(cmd)


__all__ = ['BoundedQubitMapper']
