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
A simulator that only permits classical operations, for faster/easier testing.
"""

from projectq.cengines import BasicEngine
from projectq.meta import LogicalQubitIDTag
from projectq.ops import XGate, BasicMathGate, Measure, FlushGate, Allocate, Deallocate
from projectq.types import WeakQubitRef


class ClassicalSimulator(BasicEngine):
    """
    A simple introspective simulator that only permits classical operations.

    Allows allocation, deallocation, measuring (no-op), flushing (no-op), controls, NOTs, and any
    BasicMathGate. Supports reading/writing directly from/to bits and registers of bits.
    """

    def __init__(self):
        BasicEngine.__init__(self)
        self._state = 0
        self._bit_positions = {}

    def _convert_logical_to_mapped_qubit(self, qubit):
        """
        Converts a qubit from a logical to a mapped qubit if there is a mapper.

        Args:
            qubit (projectq.types.Qubit): Logical quantum bit
        """
        mapper = self.main_engine.mapper
        if mapper is not None:
            if qubit.id not in mapper.current_mapping:
                raise RuntimeError("Unknown qubit id. Please make sure you have called eng.flush().")
            return WeakQubitRef(qubit.engine, mapper.current_mapping[qubit.id])
        return qubit

    def read_bit(self, qubit):
        """
        Reads a bit.

        Note:
            If there is a mapper present in the compiler, this function automatically converts from logical qubits to
            mapped qubits for the qureg argument.

        Args:
            qubit (projectq.types.Qubit): The bit to read.

        Returns:
            int: 0 if the target bit is off, 1 if it's on.
        """
        qubit = self._convert_logical_to_mapped_qubit(qubit)
        return self._read_mapped_bit(qubit)

    def _read_mapped_bit(self, mapped_qubit):
        """Internal use only. Does not change logical to mapped qubits."""
        return (self._state >> self._bit_positions[mapped_qubit.id]) & 1

    def write_bit(self, qubit, value):
        """
        Resets/sets a bit to the given value.

        Note:
            If there is a mapper present in the compiler, this function automatically converts from logical qubits to
            mapped qubits for the qureg argument.

        Args:
            qubit (projectq.types.Qubit): The bit to write.
            value (bool|int): Writes 1 if this value is truthy, else 0.
        """
        qubit = self._convert_logical_to_mapped_qubit(qubit)
        self._write_mapped_bit(qubit, value)

    def _write_mapped_bit(self, mapped_qubit, value):
        """Internal use only. Does not change logical to mapped qubits."""
        pos = self._bit_positions[mapped_qubit.id]
        if value:
            self._state |= 1 << pos
        else:
            self._state &= ~(1 << pos)

    def _mask(self, qureg):
        """
        Returns a mask, to compare against the state, with bits from the register set to 1 and other bits set to 0.

        Args:
            qureg (projectq.types.Qureg): The bits whose positions should be set.

        Returns:
            int: The mask.
        """
        mask = 0
        for qb in qureg:
            mask |= 1 << self._bit_positions[qb.id]
        return mask

    def read_register(self, qureg):
        """
        Reads a group of bits as a little-endian integer.

        Note:
            If there is a mapper present in the compiler, this function automatically converts from logical qubits to
            mapped qubits for the qureg argument.

        Args:
            qureg (projectq.types.Qureg):
                The group of bits to read, in little-endian order.

        Returns:
            int: Little-endian register value.
        """
        new_qureg = []
        for qubit in qureg:
            new_qureg.append(self._convert_logical_to_mapped_qubit(qubit))
        return self._read_mapped_register(new_qureg)

    def _read_mapped_register(self, mapped_qureg):
        """Internal use only. Does not change logical to mapped qubits."""
        mask = 0
        for i, qubit in enumerate(mapped_qureg):
            mask |= self._read_mapped_bit(qubit) << i
        return mask

    def write_register(self, qureg, value):
        """
        Sets a group of bits to store a little-endian integer value.

        Note:
            If there is a mapper present in the compiler, this function automatically converts from logical qubits to
            mapped qubits for the qureg argument.

        Args:
            qureg (projectq.types.Qureg): The bits to write, in little-endian order.
            value (int): The integer value to store. Must fit in the register.
        """
        new_qureg = []
        for qubit in qureg:
            new_qureg.append(self._convert_logical_to_mapped_qubit(qubit))
        self._write_mapped_register(new_qureg, value)

    def _write_mapped_register(self, mapped_qureg, value):
        """Internal use only. Does not change logical to mapped qubits."""
        if value < 0 or value >= 1 << len(mapped_qureg):
            raise ValueError("Value won't fit in register.")
        for i, mapped_qubit in enumerate(mapped_qureg):
            self._write_mapped_bit(mapped_qubit, (value >> i) & 1)

    def is_available(self, cmd):
        return (
            cmd.gate == Measure
            or cmd.gate == Allocate
            or cmd.gate == Deallocate
            or isinstance(cmd.gate, (BasicMathGate, FlushGate, XGate))
        )

    def receive(self, command_list):
        """Forward all commands to the next engine."""
        for cmd in command_list:
            self._handle(cmd)
        if not self.is_last_engine:
            self.send(command_list)

    def _handle(self, cmd):  # pylint: disable=too-many-branches,too-many-locals
        if isinstance(cmd.gate, FlushGate):
            return

        if cmd.gate == Measure:
            for qureg in cmd.qubits:
                for qubit in qureg:
                    # Check if a mapper assigned a different logical id
                    logical_id_tag = None
                    for tag in cmd.tags:
                        if isinstance(tag, LogicalQubitIDTag):
                            logical_id_tag = tag
                    log_qb = qubit
                    if logical_id_tag is not None:
                        log_qb = WeakQubitRef(qubit.engine, logical_id_tag.logical_qubit_id)
                    self.main_engine.set_measurement_result(log_qb, self._read_mapped_bit(qubit))
            return

        if cmd.gate == Allocate:
            new_id = cmd.qubits[0][0].id
            self._bit_positions[new_id] = len(self._bit_positions)
            return

        if cmd.gate == Deallocate:
            old_id = cmd.qubits[0][0].id
            pos = self._bit_positions[old_id]
            low = (1 << pos) - 1

            self._state = (self._state & low) | ((self._state >> 1) & ~low)
            self._bit_positions = {k: b - (0 if b < pos else 1) for k, b in self._bit_positions.items() if k != old_id}
            return

        controls_mask = self._mask(cmd.control_qubits)
        meets_controls = self._state & controls_mask == controls_mask

        if isinstance(cmd.gate, XGate):
            if not (len(cmd.qubits) == 1 and len(cmd.qubits[0]) == 1):
                raise ValueError('The XGate only accepts one qubit!')
            target = cmd.qubits[0][0]
            if meets_controls:
                self._write_mapped_bit(target, not self._read_mapped_bit(target))
            return

        if isinstance(cmd.gate, BasicMathGate):
            if meets_controls:
                ins = [self._read_mapped_register(reg) for reg in cmd.qubits]
                outs = cmd.gate.get_math_function(cmd.qubits)(ins)
                for reg, out in zip(cmd.qubits, outs):
                    self._write_mapped_register(reg, out & ((1 << len(reg)) - 1))
            return

        raise ValueError("Only support alloc/dealloc/measure/not/math ops.")
