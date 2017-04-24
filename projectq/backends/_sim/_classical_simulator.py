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
from projectq.ops import (XGate,
                          BasicMathGate,
                          Measure,
                          FlushGate,
                          Allocate,
                          Deallocate)


class ClassicalSimulator(BasicEngine):
    """
    A simple introspective simulator that only permits classical operations.

    Allows allocation, deallocation, measuring (no-pop), flushing (no-op),
    controls, NOTs, and any BasicMathGate. Supports reading/writing directly
    from/to bits and registers of bits.
    """
    def __init__(self):
        BasicEngine.__init__(self)
        self._state = 0
        self._bit_positions = {}

    def read_bit(self, qubit):
        """
        Reads a bit.

        Args:
            qubit (projectq.types.Qubit): The bit to read.

        Returns:
            int: 0 if the target bit is off, 1 if it's on.
        """
        p = self._bit_positions[qubit.id]
        return (self._state >> p) & 1

    def write_bit(self, qubit, value):
        """
        Resets/sets a bit to the given value.

        Args:
            qubit (projectq.types.Qubit): The bit to write.
            value (bool|int): Writes 1 if this value is truthy, else 0.
        """
        p = self._bit_positions[qubit.id]
        if value:
            self._state |= 1 << p
        else:
            self._state &= ~(1 << p)

    def _mask(self, qureg):
        """
        Returns a mask, to compare against the state, with bits from the
        register set to 1 and other bits set to 0.

        Args:
            qureg (projectq.types.Qureg):
                The bits whose positions should be set.

        Returns:
            int: The mask.
        """
        t = 0
        for q in qureg:
            t |= 1 << self._bit_positions[q.id]
        return t

    def read_register(self, qureg):
        """
        Reads a group of bits as a little-endian integer.

        Args:
            qureg (projectq.types.Qureg):
                The group of bits to read, in little-endian order.

        Returns:
            int: Little-endian register value.
        """
        t = 0
        for i in range(len(qureg)):
            t |= self.read_bit(qureg[i]) << i
        return t

    def write_register(self, qureg, value):
        """
        Sets a group of bits to store a little-endian integer value.

        Args:
            qureg (projectq.types.Qureg):
                The bits to write, in little-endian order.
            value (int): The integer value to store. Must fit in the register.
        """
        if value < 0 or value >= 1 << len(qureg):
            raise ValueError("Value won't fit in register.")
        for i in range(len(qureg)):
            self.write_bit(qureg[i], (value >> i) & 1)

    def is_available(self, cmd):
        return (cmd.gate == Measure or
                cmd.gate == Allocate or
                cmd.gate == Deallocate or
                isinstance(cmd.gate, BasicMathGate) or
                isinstance(cmd.gate, FlushGate) or
                isinstance(cmd.gate, XGate))

    def receive(self, command_list):
        for cmd in command_list:
            self._handle(cmd)
        if not self.is_last_engine:
            self.send(command_list)

    def _handle(self, cmd):
        if cmd.gate == Measure or isinstance(cmd.gate, FlushGate):
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
            self._bit_positions = {
                k: b - (0 if b < pos else 1)
                for k, b in self._bit_positions.items()
            }
            return

        controls_mask = self._mask(cmd.control_qubits)
        meets_controls = self._state & controls_mask == controls_mask

        if isinstance(cmd.gate, XGate):
            assert len(cmd.qubits) == 1 and len(cmd.qubits[0]) == 1
            target = cmd.qubits[0][0]
            if meets_controls:
                self.write_bit(target, not self.read_bit(target))
            return

        if isinstance(cmd.gate, BasicMathGate):
            if meets_controls:
                ins = [self.read_register(reg) for reg in cmd.qubits]
                outs = cmd.gate.get_math_function(cmd.qubits)(ins)
                for reg, out in zip(cmd.qubits, outs):
                    self.write_register(reg, out & ((1 << len(reg)) - 1))
            return

        raise ValueError("Only support alloc/dealloc/measure/not/math ops.")
