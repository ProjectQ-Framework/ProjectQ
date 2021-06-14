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
Contains a backend that saves the unitary of the circuit
"""

from copy import deepcopy
import itertools
import math
import numpy as np
import warnings

from projectq.cengines import BasicEngine
from projectq.ops import (
    AllocateQubitGate,
    DeallocateQubitGate,
    MeasureGate,
    FlushGate,
)


def _qidmask(target_ids, control_ids, control_state, n_qubits):
    """
    Calculate index masks

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
    m = len(irel_ids)

    if len(control_ids) > 0:
        cstate = np.array(list(control_state)).astype(int)
        cmask = np.where(np.all(perms[:, control_ids] == cstate, axis=1))
    else:
        cmask = np.array(range(perms.shape[0]))

    if m > 0:
        irel_perms = np.array([x[::-1] for x in itertools.product("01", repeat=m)]).astype(int)
        for i in range(2 ** m):
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
    The UnitarySimulator is aimed at calculating the unitary transformation that represents the current quantum circuit
    that is being processed.

    Note:
        The current implementation of this backend does not support the processing of any gates after a qubit
        deallocation or qubit measurement has been performed:

        .. code-block:: python

            eng = MainEngine(backend=UnitarySimulator(), engine_list=[])
            qureg = eng.allocate_qureg(3)
            All(X) | qureg

            All(Measure) | qureg
            eng.deallocate_qubit(qureg[1])

            X | qureg[0]  # ERROR: cannot process gate after measurements or deallocations
    """

    def __init__(self):
        """
        Construct the UnitarySimulator
        """
        super().__init__()
        self._qubit_map = dict()
        self._unitary = [1]
        self._num_qubits = 0
        self._is_valid = True

    @property
    def unitary(self):
        return deepcopy(self._unitary)

    def is_available(self, cmd):
        """
        Specialized implementation of is_available: The unitary simulator can deal with all arbitrarily-controlled gates
        which provide a gate-matrix (via gate.matrix).

        Args:
            cmd (Command): Command for which to check availability (single-
                qubit gate, arbitrary controls)

        Returns:
            True if it can be simulated and False otherwise.
        """
        if isinstance(cmd.gate, (AllocateQubitGate, DeallocateQubitGate, MeasureGate)):
            return True
        try:
            m = cmd.gate.matrix
            if len(m) > 2 ** 6:
                warnings.warn("Potentially large matrix gate encountered! ({} qubits)".format(math.log2(len(m))))
            return True
        except AttributeError:
            return False

    def receive(self, command_list):
        """
        Receive a list of commands from the previous engine and handle them
        (simulate them classically) prior to sending them on to the next
        engine.

        Args:
            command_list (list<Command>): List of commands to execute on the
                simulator.
        """
        for cmd in command_list:
            self._handle(cmd)

        if not self.is_last_engine:
            self.send(command_list)

    def _handle(self, cmd):
        """
        Handle all commands.

        Args:
            cmd (Command): Command to handle.

        Raises:
            RuntimeError: If a gate is processed after a qubit deallocation or measurement has been performed.
        """
        if isinstance(cmd.gate, AllocateQubitGate):
            self._qubit_map[cmd.qubits[0][0].id] = self._num_qubits
            self._num_qubits += 1
            self._unitary = np.kron(np.identity(2), self._unitary)

        elif isinstance(cmd.gate, DeallocateQubitGate):
            pos = self._qubit_map[cmd.qubits[0][0].id]
            self._qubit_map = {key: value - 1 if value > pos else value for key, value in self._qubit_map.items()}
            self._num_qubits -= 1

            # TODO: re-calculate the unitary to take the deallocation into account.
            # For now mark that a deallocation took place
            self._is_valid = False

        elif isinstance(cmd.gate, MeasureGate):
            self._is_valid = False

        elif isinstance(cmd.gate, FlushGate):
            pass

        else:
            if not self._is_valid:
                raise RuntimeError(
                    "Processing of other gates after a qubit deallocation or measurement is currently unsupported!"
                    "\nOffending command: {}".format(cmd)
                )

            cmd_mat = cmd.gate.matrix
            target_ids = [self._qubit_map[qb.id] for qr in cmd.qubits for qb in qr]
            control_ids = [self._qubit_map[qb.id] for qb in cmd.control_qubits]

            # TODO: change to with c_state = cmd.control_state once that PR is merged
            c_state = [1] * len(control_ids)

            mask_list = _qidmask(target_ids, control_ids, c_state, self._num_qubits)
            for mask in mask_list:
                cache = np.diag([1] * (2 ** self._num_qubits)).astype(complex)
                cache[np.ix_(mask, mask)] = cmd_mat
                self._unitary = cache @ self._unitary
