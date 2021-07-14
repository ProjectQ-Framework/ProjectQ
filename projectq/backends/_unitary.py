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

"""Contain a backend that saves the unitary of a quantum circuit."""

import itertools
import math
import random
import warnings
from copy import deepcopy

import numpy as np

from projectq.cengines import BasicEngine
from projectq.meta import LogicalQubitIDTag, get_control_count, has_negative_control
from projectq.ops import AllocateQubitGate, DeallocateQubitGate, FlushGate, MeasureGate
from projectq.types import WeakQubitRef


def _qidmask(target_ids, control_ids, n_qubits):
    """
    Calculate index masks.

    Args:
        target_ids (list): list of target qubit indices
        control_ids (list): list of control qubit indices
        control_state (list): list of states for the control qubits (0 or 1)
        n_qubits (int): number of qubits
    """
    mask_list = []
    perms = np.array([x[::-1] for x in itertools.product("01", repeat=n_qubits)]).astype(int)
    all_ids = np.array(range(n_qubits))
    irel_ids = np.delete(all_ids, control_ids + target_ids)

    if len(control_ids) > 0:
        cmask = np.where(np.all(perms[:, control_ids] == [1] * len(control_ids), axis=1))
    else:
        cmask = np.array(range(perms.shape[0]))

    if len(irel_ids) > 0:
        irel_perms = np.array([x[::-1] for x in itertools.product("01", repeat=len(irel_ids))]).astype(int)
        for i in range(2 ** len(irel_ids)):
            irel_mask = np.where(np.all(perms[:, irel_ids] == irel_perms[i], axis=1))
            common = np.intersect1d(irel_mask, cmask)
            if len(common) > 0:
                mask_list.append(common)
    else:
        irel_mask = np.array(range(perms.shape[0]))
        mask_list.append(np.intersect1d(irel_mask, cmask))
    return mask_list


class UnitarySimulator(BasicEngine):
    """
    Simulator engine aimed at calculating the unitary transformation that represents the current quantum circuit.

    Attributes:
        unitary (np.ndarray): Current unitary representing the quantum circuit being processed so far.
        history (list<np.ndarray>): List of previous quantum circuit unitaries.

    Note:
        The current implementation of this backend resets the unitary after the first gate that is neither a qubit
        deallocation nor a measurement occurs after one of those two aforementioned gates.

        The old unitary call be accessed at anytime after such a situation occurs via the `history` property.

        .. code-block:: python

            eng = MainEngine(backend=UnitarySimulator(), engine_list=[])
            qureg = eng.allocate_qureg(3)
            All(X) | qureg

            eng.flush()
            All(Measure) | qureg
            eng.deallocate_qubit(qureg[1])

            X | qureg[0]  # WARNING: appending gate after measurements or deallocations resets the unitary
    """

    def __init__(self):
        """Initialize a UnitarySimulator object."""
        super().__init__()
        self._qubit_map = {}
        self._unitary = [1]
        self._num_qubits = 0
        self._is_valid = True
        self._is_flushed = False
        self._state = [1]
        self._history = []

    @property
    def unitary(self):
        """
        Access the last unitary matrix directly.

        Returns:
            A numpy array which is the unitary matrix of the circuit.
        """
        return deepcopy(self._unitary)

    @property
    def history(self):
        """
        Access all previous unitary matrices.

        The current unitary matrix is appended to this list once a gate is received after either a measurement or a
        qubit deallocation has occurred.

        Returns:
            A list where the elements are all previous unitary matrices representing the circuit, separated by
            measurement/deallocate gates.
        """
        return deepcopy(self._history)

    def is_available(self, cmd):
        """
        Test whether a Command is supported by a compiler engine.

        Specialized implementation of is_available: The unitary simulator can deal with all arbitrarily-controlled gates
        which provide a gate-matrix (via gate.matrix).

        Args:
            cmd (Command): Command for which to check availability (single- qubit gate, arbitrary controls)

        Returns:
            True if it can be simulated and False otherwise.
        """
        if has_negative_control(cmd):
            return False

        if isinstance(cmd.gate, (AllocateQubitGate, DeallocateQubitGate, MeasureGate)):
            return True

        try:
            gate_mat = cmd.gate.matrix
            if len(gate_mat) > 2 ** 6:
                warnings.warn("Potentially large matrix gate encountered! ({} qubits)".format(math.log2(len(gate_mat))))
            return True
        except AttributeError:
            return False

    def receive(self, command_list):
        """
        Receive a list of commands.

        Receive a list of commands from the previous engine and handle them:
            * update the unitary of the quantum circuit
            * update the internal quantum state if a measurement or a qubit deallocation occurs

        prior to sending them on to the next engine.

        Args:
            command_list (list<Command>): List of commands to execute on the simulator.
        """
        for cmd in command_list:
            self._handle(cmd)

        if not self.is_last_engine:
            self.send(command_list)

    def _flush(self):
        """Flush the simulator state."""
        if not self._is_flushed:
            self._is_flushed = True
            self._state = self._unitary @ self._state

    def _handle(self, cmd):
        """
        Handle all commands.

        Args:
            cmd (Command): Command to handle.

        Raises:
            RuntimeError: If a measurement is performed before flush gate.
        """
        if isinstance(cmd.gate, AllocateQubitGate):
            self._qubit_map[cmd.qubits[0][0].id] = self._num_qubits
            self._num_qubits += 1
            self._unitary = np.kron(np.identity(2), self._unitary)
            self._state.extend([0] * len(self._state))

        elif isinstance(cmd.gate, DeallocateQubitGate):
            pos = self._qubit_map[cmd.qubits[0][0].id]
            self._qubit_map = {key: value - 1 if value > pos else value for key, value in self._qubit_map.items()}
            self._num_qubits -= 1
            self._is_valid = False

        elif isinstance(cmd.gate, MeasureGate):
            self._is_valid = False

            if not self._is_flushed:
                raise RuntimeError(
                    'Please make sure all previous gates are flushed before measurement so the state gets updated'
                )

            if get_control_count(cmd) != 0:
                raise ValueError('Cannot have control qubits with a measurement gate!')

            all_qubits = [qb for qr in cmd.qubits for qb in qr]
            measurements = self.measure_qubits([qb.id for qb in all_qubits])

            for qb, res in zip(all_qubits, measurements):
                # Check if a mapper assigned a different logical id
                for tag in cmd.tags:
                    if isinstance(tag, LogicalQubitIDTag):
                        qb = WeakQubitRef(qb.engine, tag.logical_qubit_id)
                        break
                self.main_engine.set_measurement_result(qb, res)

        elif isinstance(cmd.gate, FlushGate):
            self._flush()
        else:
            if not self._is_valid:
                self._flush()

                warnings.warn(
                    "Processing of other gates after a qubit deallocation or measurement will reset the unitary,"
                    "previous unitary can be accessed in history"
                )
                self._history.append(self._unitary)
                self._unitary = np.identity(2 ** self._num_qubits, dtype=complex)
                self._state = np.array([1] + ([0] * (2 ** self._num_qubits - 1)), dtype=complex)
                self._is_valid = True

            self._is_flushed = False
            mask_list = _qidmask(
                [self._qubit_map[qb.id] for qr in cmd.qubits for qb in qr],
                [self._qubit_map[qb.id] for qb in cmd.control_qubits],
                self._num_qubits,
            )
            for mask in mask_list:
                cache = np.identity(2 ** self._num_qubits, dtype=complex)
                cache[np.ix_(mask, mask)] = cmd.gate.matrix
                self._unitary = cache @ self._unitary

    def measure_qubits(self, ids):
        """
        Measure the qubits with IDs ids and return a list of measurement outcomes (True/False).

        Args:
            ids (list<int>): List of qubit IDs to measure.

        Returns:
            List of measurement results (containing either True or False).
        """
        random_outcome = random.random()
        val = 0.0
        i_picked = 0
        while val < random_outcome and i_picked < len(self._state):
            val += np.abs(self._state[i_picked]) ** 2
            i_picked += 1

        i_picked -= 1

        pos = [self._qubit_map[ID] for ID in ids]
        res = [False] * len(pos)

        mask = 0
        val = 0
        for i, _pos in enumerate(pos):
            res[i] = ((i_picked >> _pos) & 1) == 1
            mask |= 1 << _pos
            val |= (res[i] & 1) << _pos

        nrm = 0.0
        for i, _state in enumerate(self._state):
            if (mask & i) != val:
                self._state[i] = 0.0
            else:
                nrm += np.abs(_state) ** 2

        self._state *= 1.0 / np.sqrt(nrm)
        return res
