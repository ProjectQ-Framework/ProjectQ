#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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

"""Backend to convert ProjectQ commands to OpenQASM."""

from copy import deepcopy

from projectq.cengines import BasicEngine
from projectq.meta import get_control_count, has_negative_control
from projectq.ops import (
    NOT,
    Allocate,
    Barrier,
    Deallocate,
    FlushGate,
    H,
    Measure,
    Ph,
    R,
    Rx,
    Ry,
    Rz,
    S,
    Sdag,
    Swap,
    T,
    Tdag,
    X,
    Y,
    Z,
)

# ==============================================================================


class OpenQASMBackend(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """Engine to convert ProjectQ commands to OpenQASM format (either string or file)."""

    def __init__(
        self,
        collate_callback=None,
        qubit_callback='q{}'.format,
        bit_callback='c{}'.format,
        qubit_id_mapping_redux=True,
    ):
        """
        Initialize an OpenQASMBackend object.

        Contrary to OpenQASM, ProjectQ does not impose the restriction that a program must start with qubit/bit
        allocations and end with some measurements.

        The user can configure what happens each time a FlushGate() is encountered by setting the `collate` and
        `collate_func` arguments to an OpenQASMBackend constructor,

        Args:
            output (list,file):
            collate (function): Each time a FlushGate is received, this callback function will be called. If let
                unspecified, the commands are appended to the existing file/string.
                Function signature: Callable[[Sequence[str]], None]
            qubit_callback (function): Callback function called upon create of each qubit to generate a name for the
                qubit.
                Function signature: Callable[[int], str]
            bit_callback (function): Callback function called upon create of each qubit to generate a name for the
                qubit.
                Function signature: Callable[[int], str]
            qubit_id_mapping_redux (bool): If True, try to allocate new Qubit IDs to the next available qreg/creg (if
                any), otherwise create a new qreg/creg. If False, simply create a new qreg/creg for each new Qubit ID
        """
        super().__init__()
        self._collate_callback = collate_callback
        self._gen_qubit_name = qubit_callback
        self._gen_bit_name = bit_callback
        self._qubit_id_mapping_redux = qubit_id_mapping_redux

        self._output = []
        self._qreg_dict = {}
        self._creg_dict = {}
        self._reg_index = 0
        self._available_indices = []

        self._insert_openqasm_header()

    @property
    def qasm(self):
        """Access to the QASM representation of the circuit."""
        return self._output

    def is_available(self, cmd):
        """
        Return true if the command can be executed.

        Args:
            cmd (Command): Command for which to check availability
        """
        if has_negative_control(cmd):
            return False

        n_controls = get_control_count(cmd)
        gate = cmd.gate
        is_available = False

        if gate in (Measure, Allocate, Deallocate, Barrier):
            is_available = True

        if n_controls == 0:
            if gate in (H, S, Sdag, T, Tdag, X, NOT, Y, Z, Swap):
                is_available = True
            if isinstance(gate, (Ph, R, Rx, Ry, Rz)):
                is_available = True
        elif n_controls == 1:
            if gate in (H, X, NOT, Y, Z):
                is_available = True
            if isinstance(
                gate,
                (
                    R,
                    Rz,
                ),
            ):
                is_available = True
        elif n_controls == 2:
            if gate in (X, NOT):
                is_available = True

        if not is_available:
            return False
        if not self.is_last_engine:
            return self.next_engine.is_available(cmd)
        return True

    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until completion.

        Args:
            command_list: List of commands to execute
        """
        for cmd in command_list:
            if not cmd.gate == FlushGate():
                self._store(cmd)
            else:
                self._reset_after_flush()

        if not self.is_last_engine:
            self.send(command_list)

    def _store(self, cmd):  # pylint: disable=too-many-branches,too-many-statements
        """
        Temporarily store the command cmd.

        Translates the command and stores it the _openqasm_circuit attribute (self._openqasm_circuit)

        Args:
            cmd: Command to store
        """
        gate = cmd.gate
        n_controls = get_control_count(cmd)

        def _format_angle(angle):
            return f'({angle})'

        _ccontrolled_gates_func = {
            X: 'ccx',
            NOT: 'ccx',
        }
        _controlled_gates_func = {
            H: 'ch',
            Ph: 'cu1',
            R: 'cu1',
            Rz: 'crz',
            X: 'cx',
            NOT: 'cx',
            Y: 'cy',
            Z: 'cz',
            Swap: 'cswap',
        }
        _gates_func = {
            Barrier: 'barrier',
            H: 'h',
            Ph: 'u1',
            S: 's',
            Sdag: 'sdg',
            T: 't',
            Tdag: 'tdg',
            R: 'u1',
            Rx: 'rx',
            Ry: 'ry',
            Rz: 'rz',
            X: 'x',
            NOT: 'x',
            Y: 'y',
            Z: 'z',
            Swap: 'swap',
        }

        if gate == Allocate:
            add = True

            # Perform qubit index reduction if possible.  This typically means that existing qubit keep their indices
            # between FlushGates but that qubit indices of deallocated qubit may be reused.
            if self._qubit_id_mapping_redux and self._available_indices:
                add = False
                index = self._available_indices.pop()
            else:
                index = self._reg_index
                self._reg_index += 1

            qb_id = cmd.qubits[0][0].id

            # TODO: only create bit for qubits that are actually measured
            self._qreg_dict[qb_id] = self._gen_qubit_name(index)
            self._creg_dict[qb_id] = self._gen_bit_name(index)

            if add:
                self._output.append(f'qubit {self._qreg_dict[qb_id]};')
                self._output.append(f'bit {self._creg_dict[qb_id]};')

        elif gate == Deallocate:
            qb_id = cmd.qubits[0][0].id

            if self._qubit_id_mapping_redux:
                self._available_indices.append(qb_id)
                del self._qreg_dict[qb_id]
                del self._creg_dict[qb_id]

        elif gate == Measure:
            assert len(cmd.qubits) == 1 and len(cmd.qubits[0]) == 1
            qb_id = cmd.qubits[0][0].id

            self._output.append(f'{self._creg_dict[qb_id]} = measure {self._qreg_dict[qb_id]};')

        elif n_controls == 2:
            targets = [self._qreg_dict[qb.id] for qureg in cmd.qubits for qb in qureg]
            controls = [self._qreg_dict[qb.id] for qb in cmd.control_qubits]

            try:
                self._output.append(f'{_ccontrolled_gates_func[gate]} {",".join(controls + targets)};')
            except KeyError as err:
                raise RuntimeError(f'Unable to perform {gate} gate with n=2 control qubits') from err

        elif n_controls == 1:
            target_qureg = [self._qreg_dict[qb.id] for qureg in cmd.qubits for qb in qureg]

            try:
                if isinstance(gate, Ph):
                    self._output.append(
                        f'{_controlled_gates_func[type(gate)]}{_format_angle(-gate.angle / 2.0)} '
                        f'{self._qreg_dict[cmd.control_qubits[0].id]},{target_qureg[0]};'
                    )
                elif isinstance(
                    gate,
                    (
                        R,
                        Rz,
                    ),
                ):
                    self._output.append(
                        f'{_controlled_gates_func[type(gate)]}{_format_angle(gate.angle)} '
                        f'{self._qreg_dict[cmd.control_qubits[0].id]},{target_qureg[0]};'
                    )
                else:
                    self._output.append(
                        '{} {},{};'.format(  # pylint: disable=consider-using-f-string
                            _controlled_gates_func[gate], self._qreg_dict[cmd.control_qubits[0].id], *target_qureg
                        )
                    )
            except KeyError as err:
                raise RuntimeError(f'Unable to perform {gate} gate with n=1 control qubits') from err
        else:
            target_qureg = [self._qreg_dict[qb.id] for qureg in cmd.qubits for qb in qureg]
            if isinstance(gate, Ph):
                self._output.append(f'{_gates_func[type(gate)]}{_format_angle(-gate.angle / 2.0)} {target_qureg[0]};')
            elif isinstance(gate, (R, Rx, Ry, Rz)):
                self._output.append(f'{_gates_func[type(gate)]}{_format_angle(gate.angle)} {target_qureg[0]};')
            else:
                self._output.append(
                    '{} {};'.format(_gates_func[gate], *target_qureg)  # pylint: disable=consider-using-f-string
                )

    def _insert_openqasm_header(self):
        self._output.append('OPENQASM 3;')
        self._output.append('include "stdgates.inc";')

    def _reset_after_flush(self):
        """Reset the internal quantum circuit after a FlushGate."""
        if not self._collate_callback:
            self._output.append('# ' + '=' * 80)
        else:
            self._collate_callback(deepcopy(self._output))
            self._output.clear()
            self._insert_openqasm_header()
            for qubit_name in self._qreg_dict.values():
                self._output.append(f'qubit {qubit_name};')
            for bit_name in self._creg_dict.values():
                self._output.append(f'bit {bit_name};')
