#   Copyright 2018 ProjectQ-Framework (wOAww.projectq.ch)
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
Mapper for a quantum circuit to an arbitrary connected graph.

Input: Quantum circuit with 1 and 2 qubit gates on n qubits. Gates are assumed
       to be applied in parallel if they act on disjoint qubit(s) and any pair
       of qubits can perform a 2 qubit gate (all-to-all connectivity)
Output: Quantum circuit in which qubits are placed in 2-D square grid in which
        only nearest neighbour qubits can perform a 2 qubit gate. The mapper
        uses Swap gates in order to move qubits next to each other.
"""
from copy import deepcopy

import math
import random

from projectq.cengines import (BasicMapperEngine, return_swap_depth)
from projectq.meta import LogicalQubitIDTag
from projectq.ops import (AllocateQubitGate, Command, DeallocateQubitGate,
                          FlushGate, Swap)
from projectq.types import WeakQubitRef
from projectq.cengines._graph_path_manager import PathManager

# ==============================================================================


class GraphMapperError(Exception):
    """Base class for all exceptions related to the GraphMapper."""


def _add_qubits_to_mapping(current_mapping, graph, new_logical_qubit_ids,
                           stored_commands):
    """
    Add active qubits to a mapping

    Qubits that are active but not yet registered in the mapping are added by
    mapping them to the next available backend id

    Args:
        current_mapping (dict): specify which method should be used to
                                 add the new qubits to the current mapping
        graph (networkx.Graph): underlying graph used by the mapper
        new_logical_qubit_ids (list): list of logical ids not yet part of the
                                      mapping and that need to be assigned a
                                      backend id
        stored_commands (list): list of commands yet to be processed by the
                                mapper

    Returns: A new mapping

    Pre-conditions:
        len(active_qubits) <= num_qubits == len(graph)
    """
    # pylint: disable=unused-argument
    mapping = deepcopy(current_mapping)
    currently_used_nodes = sorted([v for _, v in mapping.items()])
    available_ids = [n for n in graph if n not in currently_used_nodes]

    for i, logical_id in enumerate(new_logical_qubit_ids):
        mapping[logical_id] = available_ids[i]
    return mapping


class GraphMapper(BasicMapperEngine):
    """
    Mapper to an arbitrary connected graph.

    Maps a quantum circuit to an arbitrary connected graph of connected qubits
    using Swap gates.

    Args:
        graph (networkx.Graph) : Arbitrary connected graph
        storage (int) Number of gates to temporarily store
        add_qubits_to_mapping (function) Function called when new qubits are to
                                         be added to the current mapping
                                         Signature of the function call:
                                              current_mapping
                                              graph
                                              new_logical_qubit_ids
                                              stored_commands
        enable_caching(Bool): Controls whether optimal path caching is
                              enabled

    Attributes:
        current_mapping:  Stores the mapping: key is logical qubit id, value
                          is mapped qubit id from 0,...,self.num_qubits
        storage (int): Number of gate it caches before mapping.
        num_qubits(int): number of qubits
        num_mappings (int): Number of times the mapper changed the mapping
        depth_of_swaps (dict): Key are circuit depth of swaps, value is the
                               number of such mappings which have been
                               applied
        num_of_swaps_per_mapping (dict): Key are the number of swaps per
                                         mapping, value is the number of such
                                         mappings which have been applied
        path_stats (dict) : Key is the endpoints of a path, value is the number
                            of such paths which have been applied

    Note:
        1) Gates are cached and only mapped from time to time. A
           FastForwarding gate doesn't empty the cache, only a FlushGate does.
        2) Only 1 and two qubit gates allowed.
        3) Does not optimize for dirty qubits.

    """

    def __init__(self,
                 graph,
                 storage=1000,
                 add_qubits_to_mapping=_add_qubits_to_mapping,
                 enable_caching=True):
        """
        Initialize a GraphMapper compiler engine.

        Args:
            graph (networkx.Graph): Arbitrary connected graph representing
                                    Qubit connectivity
            storage (int): Number of gates to temporarily store
            enable_caching (Bool): Controls whether path caching is enabled
        Raises:
            RuntimeError: if the graph is not a connected graph
        """
        BasicMapperEngine.__init__(self)

        self.paths = PathManager(graph, enable_caching)
        self.num_qubits = graph.number_of_nodes()
        self.storage = storage
        # Randomness to pick permutations if there are too many.
        # This creates an own instance of Random in order to not influence
        # the bound methods of the random module which might be used in other
        # places.
        self._rng = random.Random(11)
        # Storing commands
        self._stored_commands = list()
        # Logical qubit ids for which the Allocate gate has already been
        # processed and sent to the next engine but which are not yet
        # deallocated:
        self._currently_allocated_ids = set()
        # Our internal mappings
        self._current_mapping = dict()  # differs from other mappers
        self._reverse_current_mapping = dict()
        # Function to add new logical qubits ids to the mapping
        self._add_qubits_to_mapping = add_qubits_to_mapping

        # Statistics:
        self.num_mappings = 0
        self.depth_of_swaps = dict()
        self.num_of_swaps_per_mapping = dict()

    @property
    def current_mapping(self):
        """Return a copy of the current mapping."""
        return deepcopy(self._current_mapping)

    @current_mapping.setter
    def current_mapping(self, current_mapping):
        """Set the current mapping to a new value."""
        if not current_mapping:
            self._current_mapping = dict()
            self._reverse_current_mapping = dict()
        else:
            self._current_mapping = current_mapping
            self._reverse_current_mapping = {
                v: k
                for k, v in self._current_mapping.items()
            }

    def is_available(self, cmd):
        """Only allows 1 or two qubit gates."""
        num_qubits = 0
        for qureg in cmd.all_qubits:
            num_qubits += len(qureg)
        return num_qubits <= 2

    def _process_commands(self):
        """
        Process commands and if necessary, calculate paths through the graph.

        Attempts to find as many paths through the graph as possible in order
        to generate a new mapping that is able to apply as many gates as
        possible.

        It goes through stored_commands and tries to find paths through the
        graph that can be applied simultaneously to move the qubits without
        side effects so that as many gates can be applied; gates are applied
        on on a first come first served basis.

        Args:
            None (list): Nothing here for now

        Returns: A list of paths through the graph to move some qubits and have
                 them interact
        """
        not_in_mapping_qubits = set()
        allocated_qubits = deepcopy(self._currently_allocated_ids)
        active_qubits = deepcopy(self._currently_allocated_ids)

        # Always start from scratch again
        # (does not reset cache or path statistics)
        self.paths.clear_paths()

        for cmd in self._stored_commands:
            if (len(allocated_qubits) == self.num_qubits
                    and not active_qubits):
                break

            qubit_ids = [
                qubit.id for qureg in cmd.all_qubits for qubit in qureg
            ]

            if len(qubit_ids) > 2 or not qubit_ids:
                raise Exception("Invalid command (number of qubits): " +
                                str(cmd))

            elif isinstance(cmd.gate, AllocateQubitGate):
                qubit_id = cmd.qubits[0][0].id
                if len(allocated_qubits) < self.num_qubits:
                    allocated_qubits.add(qubit_id)
                    active_qubits.add(qubit_id)
                    if qubit_id not in self._current_mapping:
                        not_in_mapping_qubits.add(qubit_id)

            elif isinstance(cmd.gate, DeallocateQubitGate):
                qubit_id = cmd.qubits[0][0].id
                if qubit_id in active_qubits:
                    active_qubits.remove(qubit_id)
                    # Do not remove from allocated_qubits as this would
                    # allow the mapper to add a new qubit to this location
                    # before the next swaps which is currently not
                    # supported

            # Process a two qubit gate:
            elif len(qubit_ids) == 2:
                # At least one qubit is not an active qubit:
                if qubit_ids[0] not in active_qubits \
                   or qubit_ids[1] not in active_qubits:
                    active_qubits.discard(qubit_ids[0])
                    active_qubits.discard(qubit_ids[1])
                else:
                    if not_in_mapping_qubits:
                        self.current_mapping = self._add_qubits_to_mapping(
                            self._current_mapping, self.paths.graph,
                            not_in_mapping_qubits, self._stored_commands)
                        not_in_mapping_qubits = set()

                    if not self.paths.push_interaction(
                            self._current_mapping[qubit_ids[0]],
                            self._current_mapping[qubit_ids[1]]):
                        break

        if not_in_mapping_qubits:
            self.current_mapping = self._add_qubits_to_mapping(
                self._current_mapping, self.paths.graph, not_in_mapping_qubits,
                self._stored_commands)

    def _send_possible_commands(self):
        """
        Send the stored commands possible without changing the mapping.
        """
        active_ids = deepcopy(self._currently_allocated_ids)

        for logical_id in self._current_mapping:
            # So that loop doesn't stop before AllocateGate applied
            active_ids.add(logical_id)

        new_stored_commands = []
        for i in range(len(self._stored_commands)):
            cmd = self._stored_commands[i]
            if not active_ids:
                new_stored_commands += self._stored_commands[i:]
                break
            if isinstance(cmd.gate, AllocateQubitGate):
                if cmd.qubits[0][0].id in self._current_mapping:
                    qb0 = WeakQubitRef(
                        engine=self,
                        idx=self._current_mapping[cmd.qubits[0][0].id])
                    self._currently_allocated_ids.add(cmd.qubits[0][0].id)
                    self.send([
                        Command(
                            engine=self,
                            gate=AllocateQubitGate(),
                            qubits=([qb0], ),
                            tags=[LogicalQubitIDTag(cmd.qubits[0][0].id)])
                    ])
                else:
                    new_stored_commands.append(cmd)
            elif isinstance(cmd.gate, DeallocateQubitGate):
                if cmd.qubits[0][0].id in active_ids:
                    qb0 = WeakQubitRef(
                        engine=self,
                        idx=self._current_mapping[cmd.qubits[0][0].id])
                    self._currently_allocated_ids.remove(cmd.qubits[0][0].id)
                    active_ids.remove(cmd.qubits[0][0].id)
                    self._current_mapping.pop(cmd.qubits[0][0].id)
                    self.send([
                        Command(
                            engine=self,
                            gate=DeallocateQubitGate(),
                            qubits=([qb0], ),
                            tags=[LogicalQubitIDTag(cmd.qubits[0][0].id)])
                    ])
                else:
                    new_stored_commands.append(cmd)
            else:
                send_gate = True
                backend_ids = set()
                for qureg in cmd.all_qubits:
                    for qubit in qureg:
                        if qubit.id not in active_ids:
                            send_gate = False
                            break
                        backend_ids.add(self._current_mapping[qubit.id])

                # Check that mapped ids are connected by an edge on the graph
                if len(backend_ids) == 2:
                    send_gate = self.paths.graph.has_edge(*list(backend_ids))

                if send_gate:
                    self._send_cmd_with_mapped_ids(cmd)
                else:
                    # Cannot execute gate -> make sure no other gate will use
                    # any of those qubits to preserve sequence
                    for qureg in cmd.all_qubits:
                        for qubit in qureg:
                            active_ids.discard(qubit.id)
                    new_stored_commands.append(cmd)
        self._stored_commands = new_stored_commands

    def _run(self):
        """
        Create a new mapping and executes possible gates.

        It first allocates all 0, ..., self.num_qubits-1 mapped qubit ids, if
        they are not already used because we might need them all for the
        swaps. Then it creates a new map, swaps all the qubits to the new map,
        executes all possible gates, and finally deallocates mapped qubit ids
        which don't store any information.
        """
        num_of_stored_commands_before = len(self._stored_commands)

        # Go through the command list and generate a list of paths.
        # At the same time, add soon-to-be-allocated qubits to the mapping
        self._process_commands()

        self._send_possible_commands()
        if not self._stored_commands:
            return

        swaps = self.paths.generate_swaps()

        if swaps:  # first mapping requires no swaps
            backend_ids_used = {
                self._current_mapping[logical_id]
                for logical_id in self._currently_allocated_ids
            }

            # Get a list of the qubits we need to allocate just to perform the
            # swaps
            not_allocated_ids = set(
                self.paths.get_all_nodes()).difference(backend_ids_used)

            # Calculate temporary internal reverse mapping
            new_internal_mapping = deepcopy(self._reverse_current_mapping)

            # Allocate all mapped qubit ids that are not currently allocated
            # but part of some path so that we may perform the swapping
            # operations.
            for backend_id in not_allocated_ids:
                qb0 = WeakQubitRef(engine=self, idx=backend_id)
                self.send([
                    Command(
                        engine=self,
                        gate=AllocateQubitGate(),
                        qubits=([qb0], ))
                ])

                # Those qubits are not part of the current mapping, so add them
                # to the temporary internal reverse mapping with invalid ids
                new_internal_mapping[backend_id] = -1

            # Calculate reverse internal mapping
            new_internal_mapping = deepcopy(self._reverse_current_mapping)

            # Add missing entries with invalid id to be able to process the
            # swaps operations
            for backend_id in not_allocated_ids:
                new_internal_mapping[backend_id] = -1

            # Send swap operations to arrive at the new mapping
            for bqb0, bqb1 in swaps:
                qb0 = WeakQubitRef(engine=self, idx=bqb0)
                qb1 = WeakQubitRef(engine=self, idx=bqb1)
                self.send(
                    [Command(engine=self, gate=Swap, qubits=([qb0], [qb1]))])

                # Update internal mapping based on swap operations
                new_internal_mapping[bqb0], \
                    new_internal_mapping[bqb1] = \
                    new_internal_mapping[bqb1], \
                    new_internal_mapping[bqb0]

            # Register statistics:
            self.num_mappings += 1
            depth = return_swap_depth(swaps)
            if depth not in self.depth_of_swaps:
                self.depth_of_swaps[depth] = 1
            else:
                self.depth_of_swaps[depth] += 1
            if len(swaps) not in self.num_of_swaps_per_mapping:
                self.num_of_swaps_per_mapping[len(swaps)] = 1
            else:
                self.num_of_swaps_per_mapping[len(swaps)] += 1

            # Calculate the list of "helper" qubits that need to be deallocated
            # and remove invalid entries
            not_needed_anymore = []
            new_reverse_current_mapping = {}
            for backend_id, logical_id in new_internal_mapping.items():
                if logical_id < 0:
                    not_needed_anymore.append(backend_id)
                else:
                    new_reverse_current_mapping[backend_id] = logical_id

            # Deallocate all previously mapped ids which we only needed for the
            # swaps:
            for backend_id in not_needed_anymore:
                qb0 = WeakQubitRef(engine=self, idx=backend_id)
                self.send([
                    Command(
                        engine=self,
                        gate=DeallocateQubitGate(),
                        qubits=([qb0], ))
                ])

            # Calculate new mapping
            self.current_mapping = {
                v: k
                for k, v in new_reverse_current_mapping.items()
            }

        # Send possible gates:
        self._send_possible_commands()
        # Check that mapper actually made progress
        if len(self._stored_commands) == num_of_stored_commands_before:
            raise RuntimeError("Mapper is potentially in an infinite loop. "
                               "It is likely that the algorithm requires "
                               "too many qubits. Increase the number of "
                               "qubits for this mapper.")

    def receive(self, command_list):
        """
        Receive some commands.

        Receive a command list and, for each command, stores it until
        we do a mapping (FlushGate or Cache of stored commands is full).

        Args:
            command_list (list of Command objects): list of commands to
                receive.
        """
        for cmd in command_list:
            if isinstance(cmd.gate, FlushGate):
                while self._stored_commands:
                    self._run()
                self.send([cmd])
            else:
                self._stored_commands.append(cmd)
            # Storage is full: Create new map and send some gates away:
            if len(self._stored_commands) >= self.storage:
                self._run()

    def __str__(self):
        """
        Return the string representation of this GraphMapper.

        Returns:
            A summary (string) of resources used, including depth of swaps and
            statistics about the paths generated
        """

        depth_of_swaps_str = ""
        for depth_of_swaps, num_mapping in sorted(self.depth_of_swaps.items()):
            depth_of_swaps_str += "\n    {:3d}: {:3d}".format(
                depth_of_swaps, num_mapping)

        num_swaps_per_mapping_str = ""
        for num_swaps_per_mapping, num_mapping \
            in sorted(self.num_of_swaps_per_mapping.items(),
                      key=lambda x: x[1], reverse=True):
            num_swaps_per_mapping_str += "\n    {:3d}: {:3d}".format(
                num_swaps_per_mapping, num_mapping)

        interactions = [
            k for _, k in sorted(
                zip(self.paths.paths_stats.values(),
                    self.paths.paths_stats.keys()),
                reverse=True)
        ]

        max_width = int(math.ceil(
            math.log10(max(self.paths.paths_stats.values()))) + 1)
        paths_stats_str = ""
        if self.paths.enable_caching:
            for k in interactions:
                if self.paths.graph.has_edge(*list(k)):
                    path = list(k)
                else:
                    path = self.paths.cache.get_path(*list(k))
                paths_stats_str += "\n    {3:3} - {4:3}: {0:{1}} | {2}".format(
                    self.paths.paths_stats[k], max_width, path, *k)
        else:
            for k in interactions:
                paths_stats_str += "\n    {2:3} - {3:3}: {0:{1}}".format(
                    self.paths.paths_stats[k], max_width, *k)

        return ("Number of mappings: {}\n" + "Depth of swaps:     {}\n\n" +
                "Number of swaps per mapping:{}\n\n" +
                "Path statistics:{}\n\n").format(
                    self.num_mappings, depth_of_swaps_str,
                    num_swaps_per_mapping_str, paths_stats_str)
