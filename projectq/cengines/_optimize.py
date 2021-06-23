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
Contains a local optimizer engine.
"""

import warnings

from projectq.ops import FlushGate, FastForwardingGate, NotMergeable

from ._basics import BasicEngine


class LocalOptimizer(BasicEngine):
    """
    LocalOptimizer is a compiler engine which optimizes locally (merging rotations, cancelling gates with their
    inverse) in a local window of user- defined size.

    It stores all commands in a dict of lists, where each qubit has its own gate pipeline. After adding a gate, it
    tries to merge / cancel successive gates using the get_merged and get_inverse functions of the gate (if
    available). For examples, see BasicRotationGate. Once a list corresponding to a qubit contains >=m gates, the
    pipeline is sent on to the next engine.
    """

    def __init__(self, cache_size=5, m=None):  # pylint: disable=invalid-name
        """
        Initialize a LocalOptimizer object.

        Args:
            cache_size (int): Number of gates to cache per qubit, before sending on the first gate.
        """
        super().__init__()
        self._l = dict()  # dict of lists containing operations for each qubit

        if m:
            warnings.warn(
                'Pending breaking API change: LocalOptimizer(m=5) will be dropped in a future version in favor of '
                'LinearMapper(cache_size=5)',
                DeprecationWarning,
            )
            cache_size = m
        self._cache_size = cache_size  # wait for m gates before sending on

    # sends n gate operations of the qubit with index idx
    def _send_qubit_pipeline(self, idx, n_gates):
        """
        Send n gate operations of the qubit with index idx to the next engine.
        """
        il = self._l[idx]  # pylint: disable=invalid-name
        for i in range(min(n_gates, len(il))):  # loop over first n operations
            # send all gates before n-qubit gate for other qubits involved
            # --> recursively call send_helper
            other_involved_qubits = [qb for qreg in il[i].all_qubits for qb in qreg if qb.id != idx]
            for qb in other_involved_qubits:
                qubit_id = qb.id
                try:
                    gateloc = 0
                    # find location of this gate within its list
                    while self._l[qubit_id][gateloc] != il[i]:
                        gateloc += 1

                    gateloc = self._optimize(qubit_id, gateloc)

                    # flush the gates before the n-qubit gate
                    self._send_qubit_pipeline(qubit_id, gateloc)
                    # delete the n-qubit gate, we're taking care of it
                    # and don't want the other qubit to do so
                    self._l[qubit_id] = self._l[qubit_id][1:]
                except IndexError:  # pragma: no cover
                    print("Invalid qubit pipeline encountered (in the process of shutting down?).")

            # all qubits that need to be flushed have been flushed
            # --> send on the n-qubit gate
            self.send([il[i]])
        # n operations have been sent on --> resize our gate list
        self._l[idx] = self._l[idx][n_gates:]

    def _get_gate_indices(self, idx, i, qubit_ids):
        """
        Return all indices of a command, each index corresponding to the command's index in one of the qubits' command
        lists.

        Args:
            idx (int): qubit index
            i (int): command position in qubit idx's command list
            IDs (list<int>): IDs of all qubits involved in the command
        """
        N = len(qubit_ids)
        # 1-qubit gate: only gate at index i in list #idx is involved
        if N == 1:
            return [i]

        # When the same gate appears multiple time, we need to make sure not to
        # match earlier instances of the gate applied to the same qubits. So we
        # count how many there are, and skip over them when looking in the
        # other lists.
        cmd = self._l[idx][i]
        num_identical_to_skip = sum(1 for prev_cmd in self._l[idx][:i] if prev_cmd == cmd)
        indices = []
        for qubit_id in qubit_ids:
            identical_indices = [i for i, c in enumerate(self._l[qubit_id]) if c == cmd]
            indices.append(identical_indices[num_identical_to_skip])
        return indices

    def _optimize(self, idx, lim=None):
        """
        Try to remove identity gates using the is_identity function, then merge or even cancel successive gates using
        the get_merged and get_inverse functions of the gate (see, e.g., BasicRotationGate).

        It does so for all qubit command lists.
        """
        # loop over all qubit indices
        i = 0
        limit = len(self._l[idx])
        if lim is not None:
            limit = lim

        while i < limit - 1:
            # can be dropped if the gate is equivalent to an identity gate
            if self._l[idx][i].is_identity():
                # determine index of this gate on all qubits
                qubitids = [qb.id for sublist in self._l[idx][i].all_qubits for qb in sublist]
                gid = self._get_gate_indices(idx, i, qubitids)
                for j, qubit_id in enumerate(qubitids):
                    new_list = (
                        self._l[qubit_id][0 : gid[j]] + self._l[qubit_id][gid[j] + 1 :]  # noqa: E203  # noqa: E203
                    )
                self._l[qubitids[j]] = new_list  # pylint: disable=undefined-loop-variable
                i = 0
                limit -= 1
                continue

            # can be dropped if two in a row are self-inverses
            inv = self._l[idx][i].get_inverse()

            if inv == self._l[idx][i + 1]:
                # determine index of this gate on all qubits
                qubitids = [qb.id for sublist in self._l[idx][i].all_qubits for qb in sublist]
                gid = self._get_gate_indices(idx, i, qubitids)
                # check that there are no other gates between this and its
                # inverse on any of the other qubits involved
                erase = True
                for j, qubit_id in enumerate(qubitids):
                    erase *= inv == self._l[qubit_id][gid[j] + 1]

                # drop these two gates if possible and goto next iteration
                if erase:
                    for j, qubit_id in enumerate(qubitids):
                        new_list = (
                            self._l[qubit_id][0 : gid[j]] + self._l[qubit_id][gid[j] + 2 :]  # noqa: E203  # noqa: E203
                        )
                        self._l[qubit_id] = new_list
                    i = 0
                    limit -= 2
                    continue

            # gates are not each other's inverses --> check if they're
            # mergeable
            try:
                merged_command = self._l[idx][i].get_merged(self._l[idx][i + 1])
                # determine index of this gate on all qubits
                qubitids = [qb.id for sublist in self._l[idx][i].all_qubits for qb in sublist]
                gid = self._get_gate_indices(idx, i, qubitids)

                merge = True
                for j, qubit_id in enumerate(qubitids):
                    merged = self._l[qubit_id][gid[j]].get_merged(self._l[qubit_id][gid[j] + 1])
                    merge *= merged == merged_command

                if merge:
                    for j, qubit_id in enumerate(qubitids):
                        self._l[qubit_id][gid[j]] = merged_command
                        new_list = (
                            self._l[qubit_id][0 : gid[j] + 1]  # noqa: E203
                            + self._l[qubit_id][gid[j] + 2 :]  # noqa: E203
                        )
                        self._l[qubit_id] = new_list
                    i = 0
                    limit -= 1
                    continue
            except NotMergeable:
                pass  # can't merge these two commands.

            i += 1  # next iteration: look at next gate
        return limit

    def _check_and_send(self):
        """
        Check whether a qubit pipeline must be sent on and, if so,
        optimize the pipeline and then send it on.
        """
        for i in self._l:
            if (
                len(self._l[i]) >= self._cache_size
                or len(self._l[i]) > 0
                and isinstance(self._l[i][-1].gate, FastForwardingGate)
            ):
                self._optimize(i)
                if len(self._l[i]) >= self._cache_size and not isinstance(self._l[i][-1].gate, FastForwardingGate):
                    self._send_qubit_pipeline(i, len(self._l[i]) - self._cache_size + 1)
                elif len(self._l[i]) > 0 and isinstance(self._l[i][-1].gate, FastForwardingGate):
                    self._send_qubit_pipeline(i, len(self._l[i]))
        new_dict = dict()
        for idx in self._l:
            if len(self._l[idx]) > 0:
                new_dict[idx] = self._l[idx]
        self._l = new_dict

    def _cache_cmd(self, cmd):
        """
        Cache a command, i.e., inserts it into the command lists of all qubits
        involved.
        """
        # are there qubit ids that haven't been added to the list?
        idlist = [qubit.id for sublist in cmd.all_qubits for qubit in sublist]

        # add gate command to each of the qubits involved
        for qubit_id in idlist:
            if qubit_id not in self._l:
                self._l[qubit_id] = []
            self._l[qubit_id] += [cmd]

        self._check_and_send()

    def receive(self, command_list):
        """
        Receive commands from the previous engine and cache them.
        If a flush gate arrives, the entire buffer is sent on.
        """
        for cmd in command_list:
            if cmd.gate == FlushGate():  # flush gate --> optimize and flush
                for idx in self._l:
                    self._optimize(idx)
                    self._send_qubit_pipeline(idx, len(self._l[idx]))
                new_dict = dict()
                for idx in self._l:
                    if len(self._l[idx]) > 0:  # pragma: no cover
                        new_dict[idx] = self._l[idx]
                self._l = new_dict
                if self._l != dict():  # pragma: no cover
                    raise RuntimeError('Internal compiler error: qubits remaining in LocalOptimizer after a flush!')
                self.send([cmd])
            else:
                self._cache_cmd(cmd)
