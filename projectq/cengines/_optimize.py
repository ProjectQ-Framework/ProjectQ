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

from copy import deepcopy as _deepcopy
from projectq.cengines import LastEngineException, BasicEngine
from projectq.ops import FlushGate, FastForwardingGate, NotMergeable


class LocalOptimizer(BasicEngine):
    """
    LocalOptimizer is a compiler engine which optimizes locally (merging
    rotations, cancelling gates with their inverse) in a local window of user-
    defined size.

    It stores all commands in a list of lists, where each qubit has its own
    gate pipeline. After adding a gate, it tries to merge / cancel successive
    gates using the get_merged and get_inverse functions of the gate (if
    available). For examples, see BasicRotationGate. Once a list corresponding
    to a qubit contains >=m gates, the pipeline is sent on to the next engine.
    """
    def __init__(self, m=5):
        """
        Initialize a LocalOptimizer object.

        Args:
            m (int): Number of gates to cache per qubit, before sending on the
                first gate.
        """
        BasicEngine.__init__(self)
        self._l = [[]]  # list of lists containing operations for each qubit
        self._m = m  # wait for m gates before sending on

    # sends n gate operations of the qubit with index idx
    def _send_qubit_pipeline(self, idx, n):
        """
        Send n gate operations of the qubit with index idx to the next engine.
        """
        il = self._l[idx]  # temporary label for readability
        for i in range(min(n, len(il))):  # loop over first n operations
            # send all gates before n-qubit gate for other qubits involved
            # --> recursively call send_helper
            other_involved_qubits = [qb
                                     for qreg in il[i].all_qubits
                                     for qb in qreg
                                     if qb.id != idx]
            for qb in other_involved_qubits:
                Id = qb.id
                try:
                    gateloc = 0
                    # find location of this gate within its list
                    while self._l[Id][gateloc] != il[i]:
                        gateloc += 1

                    gateloc = self._optimize(Id, gateloc)

                    # flush the gates before the n-qubit gate
                    self._send_qubit_pipeline(Id, gateloc)
                    # delete the n-qubit gate, we're taking care of it
                    # and don't want the other qubit to do so
                    self._l[Id] = self._l[Id][1:]
                except IndexError:
                    print("Invalid qubit pipeline encountered (in the"
                          " process of shutting down?).")

            # all qubits that need to be flushed have been flushed
            # --> send on the n-qubit gate
            self.send([il[i]])
        # n operations have been sent on --> resize our gate list
        self._l[idx] = self._l[idx][n:]

    def _get_gate_indices(self, idx, i, IDs):
        """
        Return all indices of a command, each index corresponding to the
        command's index in one of the qubits' command lists.

        Args:
            idx (int): qubit index
            i (int): command position in qubit idx's command list
            IDs (list<int>): IDs of all qubits involved in the command
        """
        N = len(IDs)
        # 1-qubit gate: only gate at index i in list #idx is involved
        if N == 1:
            return [i]

        # When the same gate appears multiple time, we need to make sure not to
        # match earlier instances of the gate applied to the same qubits. So we
        # count how many there are, and skip over them when looking in the
        # other lists.
        cmd = self._l[idx][i]
        num_identical_to_skip = sum(1
                                    for prev_cmd in self._l[idx][:i]
                                    if prev_cmd == cmd)
        indices = []
        for Id in IDs:
            identical_indices = [i
                                 for i, c in enumerate(self._l[Id])
                                 if c == cmd]
            indices.append(identical_indices[num_identical_to_skip])
        return indices

    def _optimize(self, idx, lim=None):
        """
        Try to merge or even cancel successive gates using the get_merged and
        get_inverse functions of the gate (see, e.g., BasicRotationGate).

        It does so for all qubit command lists.
        """
        # loop over all qubit indices
        i = 0
        new_gateloc = 0
        limit = len(self._l[idx])
        if not lim is None:
            limit = lim
            new_gateloc = limit

        while i < limit - 1:
            # can be dropped if two in a row are self-inverses
            inv = self._l[idx][i].get_inverse()

            if inv == self._l[idx][i + 1]:
                # determine index of this gate on all qubits
                qubitids = [qb.id for sublist in self._l[idx][i].all_qubits
                            for qb in sublist]
                gid = self._get_gate_indices(idx, i, qubitids)
                # check that there are no other gates between this and its
                # inverse on any of the other qubits involved
                erase = True
                for j in range(len(qubitids)):
                    erase *= (inv == self._l[qubitids[j]][gid[j] + 1])

                # drop these two gates if possible and goto next iteration
                if erase:
                    for j in range(len(qubitids)):
                        new_list = (self._l[qubitids[j]][0:gid[j]] +
                                    self._l[qubitids[j]][gid[j] + 2:])
                        self._l[qubitids[j]] = new_list
                    i = 0
                    limit -= 2
                    continue

            # gates are not each other's inverses --> check if they're
            # mergeable
            try:
                merged_command = self._l[idx][i].get_merged(
                    self._l[idx][i + 1])
                # determine index of this gate on all qubits
                qubitids = [qb.id for sublist in self._l[idx][i].all_qubits
                            for qb in sublist]
                gid = self._get_gate_indices(idx, i, qubitids)

                merge = True
                for j in range(len(qubitids)):
                    m = self._l[qubitids[j]][gid[j]].get_merged(
                        self._l[qubitids[j]][gid[j] + 1])
                    merge *= (m == merged_command)

                if merge:
                    for j in range(len(qubitids)):
                        self._l[qubitids[j]][gid[j]] = merged_command
                        new_list = (self._l[qubitids[j]][0:gid[j] + 1] +
                                    self._l[qubitids[j]][gid[j] + 2:])
                        self._l[qubitids[j]] = new_list
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
        for i in range(len(self._l)):
            if (len(self._l[i]) >= self._m or len(self._l[i]) > 0
               and isinstance(self._l[i][-1].gate, FastForwardingGate)):
                self._optimize(i)
                if (len(self._l[i]) >= self._m
                   and not isinstance(self._l[i][-1].gate,
                                      FastForwardingGate)):
                    self._send_qubit_pipeline(i, len(self._l[i]) - self._m + 1)
                elif (len(self._l[i]) > 0 and
                      isinstance(self._l[i][-1].gate, FastForwardingGate)):
                    self._send_qubit_pipeline(i, len(self._l[i]))

    def _cache_cmd(self, cmd):
        """
        Cache a command, i.e., inserts it into the command lists of all qubits
        involved.
        """
        # are there qubit ids that haven't been added to the list?
        idlist = [qubit.id for sublist in cmd.all_qubits for qubit in sublist]
        maxidx = int(0)
        for ID in idlist:
            maxidx = max(maxidx, ID)

        # if so, increase size of list to account for these qubits
        add = maxidx + 1 - len(self._l)
        if add > 0:
            self._l += [[] for _ in range(add)]

        # add gate command to each of the qubits involved
        for ID in idlist:
            self._l[ID] += [cmd]

        self._check_and_send()

    def receive(self, command_list):
        """
        Receive commands from the previous engine and cache them.
        If a flush gate arrives, the entire buffer is sent on.
        """
        for cmd in command_list:
            if cmd.gate == FlushGate():  # flush gate --> optimize and flush
                for i in range(len(self._l)):
                    self._optimize(i)
                    self._send_qubit_pipeline(i, len(self._l[i]))
                self.send([cmd])
            else:
                self._cache_cmd(cmd)
