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
import itertools

import random
import numpy as np
import networkx as nx

from projectq.cengines import (BasicMapperEngine, return_swap_depth)
from projectq.meta import LogicalQubitIDTag
from projectq.ops import (AllocateQubitGate, Command, DeallocateQubitGate,
                          FlushGate, Swap)
from projectq.types import WeakQubitRef


class GraphMapperError(Exception):
    """Base class for all exceptions related to the GraphMapper."""


class QubitAllocationError(GraphMapperError):
    """
    Exception raised if a qubit allocation is impossible.

    This would typically be the case if the number of allocated qubit is
    greater than the number of nodes inside the graph.
    """


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
    #pylint: disable=unused-argument
    mapping = deepcopy(current_mapping)
    currently_used_nodes = sorted([v for _, v in mapping.items()])
    available_ids = [n for n in graph if n not in currently_used_nodes]

    for i, logical_id in enumerate(new_logical_qubit_ids):
        mapping[logical_id] = available_ids[i]
    return mapping


def _iterate_with_previous(some_iterable):
    prevs, items = itertools.tee(some_iterable, 2)
    items = itertools.islice(items, 1, None)
    prevs = itertools.islice(prevs, len(some_iterable) - 1)
    return zip(prevs, items)


def _return_swaps(paths):
    """
    Generate a list of swap ops based on a list of paths through the graph.

    Args:
        paths (list): List of paths through the graph between pairs
                      of qubits that need to interact

    Returns: A list of swap operations (tuples of logical qubit ids)
             required to move the qubits to the correct locations
    """
    swap_operations = []

    for path in paths:
        swap_operations.append([])
        path_for_qb0, path_for_qb1 = np.array_split(path, 2)

        # Add swaps operations for first half of the path
        for prev, cur in _iterate_with_previous(path_for_qb0):
            swap_operations[-1].append((prev, cur))

        # Add swaps operations for the second half of the path
        for prev, cur in _iterate_with_previous(path_for_qb1[::-1]):
            swap_operations[-1].append((prev, cur))

    return swap_operations


class GraphMapper(BasicMapperEngine):
    """
    Mapper to an arbitrary connected graph.

    Maps a quantum circuit to an arbitrary connected graph of connected qubits
    using Swap gates.


    Attributes:
        current_mapping:  Stores the mapping: key is logical qubit id, value
                          is mapped qubit id from 0,...,self.num_qubits
        graph (networkx.Graph): Arbitrary connected graph
        storage (int): Number of gate it caches before mapping.
        num_qubits(int): number of qubits
        num_mappings (int): Number of times the mapper changed the mapping
        depth_of_swaps (dict): Key are circuit depth of swaps, value is the
                               number of such mappings which have been
                               applied
        num_of_swaps_per_mapping (dict): Key are the number of swaps per
                                         mapping, value is the number of such
                                         mappings which have been applied

    Note:
        1) Gates are cached and only mapped from time to time. A
           FastForwarding gate doesn't empty the cache, only a FlushGate does.
        2) Only 1 and two qubit gates allowed.
        3) Does not optimize for dirty qubits.

    """

    def __init__(self,
                 graph,
                 storage=1000,
                 add_qubits_to_mapping=_add_qubits_to_mapping):
        """
        Initialize a GraphMapper compiler engine.

        Args:
            graph (networkx.Graph): Arbitrary connected graph representing
                                    Qubit connectivity
            storage (int): Number of gates to temporarily store
        Raises:
            RuntimeError: if the graph is not a connected graph
        """
        BasicMapperEngine.__init__(self)

        # Make sure that we start with a valid graph
        if not nx.is_connected(graph):
            raise RuntimeError("Input graph must be a connected graph")
        elif not all([isinstance(n, int) for n in graph]):
            raise RuntimeError(
                "All nodes inside the graph needs to be integers")
        else:
            self.graph = graph
        self.num_qubits = self.graph.number_of_nodes()
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
        # TODO: need to think about merging paths and applying gates in the
        #       middle of the swaps if possible

        paths = []
        allocated_qubits = deepcopy(self._currently_allocated_ids)
        active_qubits = deepcopy(self._currently_allocated_ids)

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
                else:
                    raise QubitAllocationError(
                        "Unable to allocate new qubit: all possible qubits"
                        " ({}) have already been allocated".format(
                            self.num_qubits))

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
                path = self._process_two_qubit_gate_dumb(
                    qubit0=qubit_ids[0],
                    qubit1=qubit_ids[1],
                    active_qubits=active_qubits)

                paths_start = [p[0] for p in paths]
                paths_end = [p[-1] for p in paths]

                if path \
                   and not any([p in paths_start for p in path]) \
                   and not any([p in paths_end for p in path]):
                    paths += [path]
                    # Maybe a bit too conservative: remove all qubits
                    # of the path from the active qubits list
                    # This effectively only allows non-intersecting paths
                    for backend_id in path:
                        if backend_id in self._reverse_current_mapping:
                            active_qubits.discard(
                                self._reverse_current_mapping[backend_id])

        return paths

    def _process_two_qubit_gate_dumb(self, qubit0, qubit1, active_qubits):
        """
        Process a two qubit gate.

        It either removes the two qubits from active_qubits if the gate is
        not possible or generate an optimal path through the graph connecting
        the two qubits.

        Args:
            qubit0 (int): qubit.id of one of the qubits
            qubit1 (int): qubit.id of the other qubit
            active_qubits (set): contains all qubit ids which for which
                                 gates can be applied in this cycle before
                                 the swaps

        Returns: A path through the graph (can be empty)
        """
        # At least one qubit is not an active qubit:
        if qubit0 not in active_qubits or qubit1 not in active_qubits:
            active_qubits.discard(qubit0)
            active_qubits.discard(qubit1)
            return []

        # Path is given using graph nodes (ie. mapped ids)
        # If we come here, the two nodes can't be connected on the graph or the
        # command would have been applied already
        node0 = self._current_mapping[qubit0]
        node1 = self._current_mapping[qubit1]

        # Qubits are both active but not connected via an edge
        return nx.shortest_path(self.graph, source=node0, target=node1)

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
                    self._currently_allocated_ids.add(cmd.qubits[0][0].id)
                    qb = WeakQubitRef(
                        engine=self,
                        idx=self._current_mapping[cmd.qubits[0][0].id])
                    new_cmd = Command(
                        engine=self,
                        gate=AllocateQubitGate(),
                        qubits=([qb], ),
                        tags=[LogicalQubitIDTag(cmd.qubits[0][0].id)])
                    self.send([new_cmd])
                else:
                    new_stored_commands.append(cmd)
            elif isinstance(cmd.gate, DeallocateQubitGate):
                if cmd.qubits[0][0].id in active_ids:
                    qb = WeakQubitRef(
                        engine=self,
                        idx=self._current_mapping[cmd.qubits[0][0].id])
                    new_cmd = Command(
                        engine=self,
                        gate=DeallocateQubitGate(),
                        qubits=([qb], ),
                        tags=[LogicalQubitIDTag(cmd.qubits[0][0].id)])
                    self._currently_allocated_ids.remove(cmd.qubits[0][0].id)
                    active_ids.remove(cmd.qubits[0][0].id)
                    self._current_mapping.pop(cmd.qubits[0][0].id)
                    self.send([new_cmd])
                else:
                    new_stored_commands.append(cmd)
            else:
                send_gate = True
                logical_ids = set()
                backend_ids = set()
                for qureg in cmd.all_qubits:
                    for qubit in qureg:
                        if qubit.id not in active_ids:
                            send_gate = False
                            break
                        logical_ids.add(qubit.id)
                        backend_ids.add(self._current_mapping[qubit.id])

                # Check that mapped ids are connected by an edge on the graph
                if len(backend_ids) == 2:
                    send_gate = self.graph.has_edge(*list(backend_ids))

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
        paths = self._process_commands()

        self._send_possible_commands()
        if not self._stored_commands:
            return

        swaps = _return_swaps(paths)

        if swaps:  # first mapping requires no swaps
            backend_ids_used = {
                self._current_mapping[logical_id]
                for logical_id in self._currently_allocated_ids
            }

            # Get a list of all backend ids we require to perform the swaps
            required_ids = {
                n
                for n in list(itertools.chain.from_iterable(paths))
            }

            # Get a list of the qubits we need to allocate just to perform the
            # swaps
            not_allocated_ids = set(required_ids).difference(backend_ids_used)

            # Allocate all mapped qubit ids (which are not already allocated,
            # i.e., contained in self._currently_allocated_ids)
            # and add them temporarily to the
            for backend_id in not_allocated_ids:
                qb = WeakQubitRef(engine=self, idx=backend_id)
                cmd = Command(
                    engine=self, gate=AllocateQubitGate(), qubits=([qb], ))
                self.send([cmd])

            # Send swap operations to arrive at the new mapping
            swaps = list(itertools.chain.from_iterable(swaps))
            for bqb0, bqb1 in swaps:
                q0 = WeakQubitRef(engine=self, idx=bqb0)
                q1 = WeakQubitRef(engine=self, idx=bqb1)
                cmd = Command(engine=self, gate=Swap, qubits=([q0], [q1]))
                self.send([cmd])

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

            # Calculate reverse internal mapping
            new_internal_mapping = deepcopy(self._reverse_current_mapping)

            # Add missing entries with invalid id to be able to process the
            # swaps operations
            for backend_id in not_allocated_ids:
                new_internal_mapping[backend_id] = -1

            # Update internal mapping based on swap operations
            for bqb0, bqb1 in swaps:
                new_internal_mapping[bqb0], \
                    new_internal_mapping[bqb1] = \
                    new_internal_mapping[bqb1], \
                    new_internal_mapping[bqb0]

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
                qb = WeakQubitRef(engine=self, idx=backend_id)
                cmd = Command(
                    engine=self, gate=DeallocateQubitGate(), qubits=([qb], ))
                self.send([cmd])

            # Calculate new mapping
            new_mapping = {
                v: k
                for k, v in new_reverse_current_mapping.items()
            }
            self.current_mapping = new_mapping

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