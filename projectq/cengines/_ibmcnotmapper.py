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
Contains a compiler engine to map the CNOT gates for the IBM backend.
"""
from copy import deepcopy

from projectq.cengines import (BasicEngine,
                               ForwarderEngine,
                               CommandModifier)
from projectq.meta import get_control_count, QubitPlacementTag
from projectq.ops import (Allocate,
                          CNOT,
                          NOT,
                          H,
                          FastForwardingGate,
                          FlushGate,
                          All)

from projectq.backends import IBMBackend


class IBMCNOTMapper(BasicEngine):
    """
    CNOT mapper for the IBM backend.

    Maps a given circuit to the IBM Quantum Experience chip.
    If necessary, it will flip around the CNOT gate by first applying Hadamard
    gates to both qubits, then CNOT with swapped control and target qubit, and
    finally Hadamard gates to both qubits.
    Furthermore, it adds QubitPlacementTags to Allocate gate commands.

    Note:
        The mapper has to be run once on the entire circuit.

    Warning:
        If the provided circuit cannot be mapped to the hardware layout
        without performing Swaps, the mapping procedure
        **raises an Exception**.
    """

    def __init__(self):
        """
        Initialize an IBM CNOT Mapper compiler engine.

        Resets the mapping.
        """
        BasicEngine.__init__(self)
        self._reset()

    def is_available(self, cmd):
        """
        Check if the IBM backend can perform the Command cmd and return True
        if so.

        Args:
            cmd (Command): The command to check
        """
        return IBMBackend().is_available(cmd)

    def _reset(self):
        """
        Reset the mapping parameters so the next circuit can be mapped.
        """
        self._cmds = []
        self._interactions = dict()
        self._num_cnot_target = dict()

    def _is_cnot(self, cmd):
        """
        Check if the command corresponds to a CNOT (controlled NOT gate).

        Args:
            cmd (Command): Command to check whether it is a controlled NOT
                gate.
        """
        return (isinstance(cmd.gate, NOT.__class__) and
                get_control_count(cmd) == 1)

    def _run(self):
        """
        Runs all stored gates.

        Raises:
            Exception:
                If the mapping to the IBM backend cannot be performed or if
                the mapping was already determined but more CNOTs get sent
                down the pipeline.
        """
        mapping = []
        if len(self._interactions) > 0:
            ids_and_interactions = []
            qubits_to_map = set()
            for qubit_id, interactions in self._interactions.items():
                if len(interactions) > 2:
                    num_interactions = len(interactions)
                else:
                    num_interactions = 2
                ids_and_interactions += [[qubit_id, num_interactions,
                                          self._num_cnot_target[qubit_id]]]
                qubits_to_map.add(qubit_id)
            # sort by #interactions (and #times it is the target qubit
            # for optimization purposes):
            ids_and_interactions.sort(key=lambda t: (-t[1], -t[2]))
            mapped_id = ids_and_interactions[0][0]
            corrected_counts = deepcopy(self._num_cnot_target)
            # correct CNOT target counts (the first ID is now fixed):
            for cmd in self._cmds:
                if (self._is_cnot(cmd) and
                        cmd.control_qubits[0].id == mapped_id):
                    corrected_counts[cmd.qubits[0][0].id] -= 1
            # update interaction counts
            for i in range(1, len(ids_and_interactions)):
                ids_and_interactions[i][-1] = (
                    corrected_counts[ids_and_interactions[i][0]]
                )
            ids_and_interactions.sort(key=lambda t: (-t[1], -t[2]))
            # map remaining interactions to connectivity graph
            # where necessary. Else: map according to # of times the qubit
            # is a target qubit in a CNOT.
            interactions = deepcopy(self._interactions)
            places = list(range(5))
            i = 0
            place_idx = 0
            mapping = []
            while len(qubits_to_map) > 0:
                last_mapped_id = ids_and_interactions[i][0]
                ids_and_interactions = (ids_and_interactions[0:i] +
                                        ids_and_interactions[i + 1:])
                current_place = places[place_idx]
                mapping.append((last_mapped_id, current_place))
                qubits_to_map.remove(last_mapped_id)
                places = places[0:place_idx] + places[place_idx + 1:]
                if not len(places) == 4:  # currently mapping non-center qubit
                    # map (potential) interaction partner
                    num_partners = len(interactions[last_mapped_id])
                    if num_partners > 1:
                        self._reset()
                        raise Exception("Mapping without SWAPs failed! "
                                        "Sorry...")
                    elif num_partners == 1:
                        partner_id = interactions[last_mapped_id].pop()
                        idx = [j for j in range(len(ids_and_interactions))
                               if ids_and_interactions[j][0] == partner_id]
                        i = idx[0]
                        place_idx = [pidx for pidx in range(len(places))
                                     if places[pidx] == current_place + 2][0]
                    else:
                        i = 0
                        place_idx = 0
                for idx in interactions:
                    if last_mapped_id in interactions[idx]:
                        interactions[idx].remove(last_mapped_id)

            self._interactions = dict()

        target_indices = {mp[0]: mp[1] for mp in mapping
                          if mp[1] <= 2}
        all_indices = {mp[0]: mp[1] for mp in mapping}
        for cmd in self._cmds:
            if self._needs_flipping(cmd, all_indices):
                # To have nicer syntax when flipping CNOTs, we'll use a
                # forwarder engine and a command modifier to get the tags
                # right. (If the CNOT is an 'uncompute', then so must be the
                # remapped CNOT)
                def cmd_mod(command):
                    command.tags = cmd.tags[:] + command.tags
                    command.engine = self.main_engine
                    return command

                # We'll have to add all meta tags before sending on
                cmd_mod_eng = CommandModifier(cmd_mod)
                cmd_mod_eng.next_engine = self.next_engine
                cmd_mod_eng.main_engine = self.main_engine
                # forward everything to the command modifier
                forwarder_eng = ForwarderEngine(cmd_mod_eng)
                cmd.engine = forwarder_eng
                qubit = cmd.qubits[0]
                ctrl = cmd.control_qubits
                # flip the CNOT using Hadamard gates:
                All(H) | (ctrl + qubit)
                CNOT | (qubit, ctrl)
                All(H) | (ctrl + qubit)
            elif cmd.gate == Allocate:
                ibm_order = [2, 1, 4, 0, 3]
                cmd.tags += [QubitPlacementTag(
                    ibm_order[all_indices[cmd.qubits[0][0].id]])]
                self.next_engine.receive([cmd])
            else:
                self.next_engine.receive([cmd])

        self._cmds = []

    def _needs_flipping(self, cmd, mapping):
        """
        Return True if cmd is a CNOT which needs to be flipped around.

        Args:
            cmd (Command): Command to check
            mapping (dict): Dictionary mapping all qubit indices
                to their position on the IBM QE chip.
        """
        if not self._is_cnot(cmd):
            return False

        target = mapping[cmd.qubits[0][0].id]
        control = mapping[cmd.control_qubits[0].id]

        if isinstance(self.main_engine.backend, IBMBackend):
            device = self.main_engine.backend.device
        else:
            device = 'ibmqx2'

        if device in ['ibmqx2', 'real', 'simulator']:
            interactions = [(1, 0), (2, 0), (3, 0), (4, 0),
                            (4, 2), (3, 1)]
        elif device == 'ibmqx4':
            interactions = [(0, 1), (0, 2), (0, 3), (4, 0),
                            (4, 2), (1, 3)]
        else:
            raise Exception("Unknown backend type. Must be either ibmqx2 or "
                            "ibmqx4.")
        return not (control, target) in interactions

    def _store(self, cmd):
        """
        Store a command and handle CNOTs.

        Args:
            cmd (Command): A command to store
        """
        if not cmd.gate == FlushGate():
            apply_to = cmd.qubits[0][0].id
            if apply_to not in self._interactions:
                self._interactions[apply_to] = set()
                self._num_cnot_target[apply_to] = 0
        if self._is_cnot(cmd):
            # CNOT encountered
            ctrl = cmd.control_qubits[0].id
            if ctrl not in self._interactions:
                self._interactions[ctrl] = set()
                self._num_cnot_target[ctrl] = 0
            self._interactions[ctrl].add(apply_to)
            self._interactions[apply_to].add(ctrl)
            self._num_cnot_target[apply_to] += 1

        self._cmds.append(cmd)

    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until
        completion.

        Args:
            command_list (list of Command objects): list of commands to
                receive.

        Raises:
            Exception: If mapping the CNOT gates to 1 qubit would require
                Swaps. The current version only supports remapping of CNOT
                gates without performing any Swaps due to the large costs
                associated with Swapping given the CNOT constraints.
        """
        for cmd in command_list:
            self._store(cmd)
            if isinstance(cmd.gate, FlushGate):
                self._run()
                self._reset()
