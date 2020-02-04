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
to be applied in parallel if they act on disjoint qubit(s) and any pair of
qubits can perform a 2 qubit gate (all-to-all connectivity)

Output: Quantum circuit in which qubits are placed in 2-D square grid in which
only nearest neighbour qubits can perform a 2 qubit gate. The mapper uses Swap
gates in order to move qubits next to each other.
"""
from copy import deepcopy

import random
import sys

from projectq.cengines import (BasicMapperEngine, return_swap_depth)
from projectq.meta import LogicalQubitIDTag
from projectq.ops import (AllocateQubitGate, Command, DeallocateQubitGate,
                          FlushGate, Swap)
from projectq.types import WeakQubitRef
from ._gate_manager import GateManager, look_ahead_parallelism_cost_fun

# ------------------------------------------------------------------------------

# https://www.peterbe.com/plog/fastest-way-to-uniquify-a-list-in-python-3.6
if sys.version_info[0] >= 3 and sys.version_info[1] > 6:  # pragma: no cover

    def uniquify_list(seq):
        # pylint: disable=missing-function-docstring
        return list(dict.fromkeys(seq))
else:  # pragma: no cover

    def uniquify_list(seq):
        # pylint: disable=missing-function-docstring
        seen = set()
        seen_add = seen.add
        return [x for x in seq if x not in seen and not seen_add(x)]


# ==============================================================================


class defaults(object):
    """
    Class containing default values for some options
    """
    #: Defaults to :py:func:`.look_ahead_parallelism_cost_fun`
    cost_fun = staticmethod(look_ahead_parallelism_cost_fun)
    max_swap_steps = 30


# ==============================================================================


class GraphMapperError(Exception):
    """Base class for all exceptions related to the GraphMapper."""


def _add_qubits_to_mapping_fcfs(current_mapping, graph, new_logical_qubit_ids,
                                commands_dag):
    """
    Add active qubits to a mapping.

    This function implements the simple first-come first serve approach;
    Qubits that are active but not yet registered in the mapping are added by
    mapping them to the next available backend id

    Args:
        current_mapping (dict): specify which method should be used to
                                 add the new qubits to the current mapping
        graph (networkx.Graph): underlying graph used by the mapper
        new_logical_qubit_ids (list): list of logical ids not yet part of the
                                      mapping and that need to be assigned a
                                      backend id
        stored_commands (CommandList): list of commands yet to be processed by
                                       the mapper

    Returns: A new mapping
    """
    # pylint: disable=unused-argument

    mapping = deepcopy(current_mapping)
    currently_used_nodes = sorted([v for _, v in mapping.items()])
    available_nodes = [n for n in graph if n not in currently_used_nodes]

    for i, logical_id in enumerate(new_logical_qubit_ids):
        mapping[logical_id] = available_nodes[i]
    return mapping


def _generate_mapping_minimize_swaps(graph, qubit_interaction_subgraphs):
    """
    Generate an initial mapping while maximizing the number of 2-qubit gates
    that can be applied without applying any SWAP operations.

    Args:
        graph (networkx.Graph): underlying graph used by the mapper
        qubit_interaction_subgraph (list): see documentation for CommandList

    Returns: A new mapping
    """
    mapping = {}
    available_nodes = sorted(list(graph), key=lambda n: len(graph[n]))

    # Initialize the seed node
    logical_id = qubit_interaction_subgraphs[0].pop(0)
    backend_id = available_nodes.pop()
    mapping[logical_id] = backend_id

    for subgraph in qubit_interaction_subgraphs:
        anchor_node = backend_id
        for logical_id in subgraph:
            neighbours = sorted(
                [n for n in graph[anchor_node] if n in available_nodes],
                key=lambda n: len(graph[n]))

            # If possible, take the neighbour with the highest
            # degree. Otherwise, take the next highest order available node
            if neighbours:
                backend_id = neighbours[-1]
                available_nodes.remove(backend_id)
            else:
                backend_id = available_nodes.pop()
            mapping[logical_id] = backend_id

    return mapping


def _add_qubits_to_mapping_smart_init(current_mapping, graph,
                                      new_logical_qubit_ids, commands_dag):
    """
    Add active qubits to a mapping.

    Similar to the first-come first-serve approach, except the initial mapping
    tries to maximize the initial number of gates to be applied without
    swaps. Otherwise identical to the first-come first-serve approach.

    Args:
        current_mapping (dict): specify which method should be used to
                                 add the new qubits to the current mapping
        graph (networkx.Graph): underlying graph used by the mapper
        new_logical_qubit_ids (list): list of logical ids not yet part of the
                                      mapping and that need to be assigned a
                                      backend id
        stored_commands (CommandList): list of commands yet to be processed by
                                       the mapper

    Returns: A new mapping
    """
    if not current_mapping:
        qubit_interaction_subgraphs = \
            commands_dag.calculate_qubit_interaction_subgraphs(max_order=2)

        # Interaction subgraph list can be empty if only single qubit gates are
        # present
        if not qubit_interaction_subgraphs:
            qubit_interaction_subgraphs = [list(new_logical_qubit_ids)]

        return _generate_mapping_minimize_swaps(graph,
                                                qubit_interaction_subgraphs)
    return _add_qubits_to_mapping_fcfs(current_mapping, graph,
                                       new_logical_qubit_ids, commands_dag)


def _add_qubits_to_mapping(current_mapping, graph, new_logical_qubit_ids,
                           commands_dag):
    """
    Add active qubits to a mapping

    Qubits that are active but not yet registered in the mapping are added by
    mapping them to an available backend id, as close as possible to other
    qubits which they might interact with.

    Args:
        current_mapping (dict): specify which method should be used to
                                 add the new qubits to the current mapping
        graph (networkx.Graph): underlying graph used by the mapper
        new_logical_qubit_ids (list): list of logical ids not yet part of the
                                      mapping and that need to be assigned a
                                      backend id
        stored_commands (CommandList): list of commands yet to be processed by
                                the mapper

    Returns: A new mapping
    """
    if not current_mapping:
        qubit_interaction_subgraphs = \
            commands_dag.calculate_qubit_interaction_subgraphs(max_order=2)

        # Interaction subgraph list can be empty if only single qubit gates are
        # present
        if not qubit_interaction_subgraphs:
            qubit_interaction_subgraphs = [list(new_logical_qubit_ids)]

        return _generate_mapping_minimize_swaps(graph,
                                                qubit_interaction_subgraphs)

    mapping = deepcopy(current_mapping)
    currently_used_nodes = sorted([v for _, v in mapping.items()])
    available_nodes = sorted(
        [n for n in graph if n not in currently_used_nodes],
        key=lambda n: len(graph[n]))

    for logical_id in uniquify_list(new_logical_qubit_ids):
        qubit_interactions = uniquify_list([
            i[0] if i[0] != logical_id else i[1]
            for i in commands_dag.calculate_interaction_list()
            if logical_id in i
        ])

        backend_id = None

        if len(qubit_interactions) == 1:
            # If there's only a single qubit interacting and it is already
            # present within the mapping, find the neighbour with the highest
            # degree

            qubit = qubit_interactions[0]

            if qubit in mapping:
                candidates = sorted(
                    [n for n in graph[mapping[qubit]] if n in available_nodes],
                    key=lambda n: len(graph[n]))
                if candidates:
                    backend_id = candidates[-1]
        elif qubit_interactions:
            # If there are multiple qubits interacting, find out all the
            # neighbouring nodes for each interaction. Then within those
            # nodes, try to find the one that maximizes the number of
            # interactions without swapping

            neighbours = []
            for qubit in qubit_interactions:
                if qubit in mapping:
                    neighbours.append(
                        set(n for n in graph[mapping[qubit]]
                            if n in available_nodes))
                else:
                    break

            # Try to find an intersection that maximizes the number of
            # interactions by iteratively reducing the number of considered
            # interactions

            intersection = set()
            while neighbours and not intersection:
                intersection = neighbours[0].intersection(*neighbours[1:])
                neighbours.pop()

            if intersection:
                backend_id = intersection.pop()

        if backend_id is None:
            backend_id = available_nodes.pop()
        else:
            available_nodes.remove(backend_id)

        mapping[logical_id] = backend_id

    return mapping


class GraphMapper(BasicMapperEngine):
    """
    Mapper to an arbitrary connected graph.

    Maps a quantum circuit to an arbitrary connected graph of connected qubits
    using Swap gates.

    .. seealso::
      :py:mod:`projectq.cengines._gate_manager`

    Args:
        graph (networkx.Graph) : Arbitrary connected graph
        storage (int): Approximate number of gates to temporarily store
        add_qubits_to_mapping (function or str): Function called when
            new qubits are to be added to the current mapping.
            Special possible string values:

            - ``"fcfs"``: first-come first serve
            - ``"fcfs_init"``: first-come first serve with smarter mapping
                               initialisation

    Note:
        1) Gates are cached and only mapped from time to time. A
           FastForwarding gate doesn't empty the cache, only a FlushGate does.
        2) Only 1 and two qubit gates allowed.
        3) Does not optimize for dirty qubits.
        4) Signature for third argument is
           ``add_qubits_to_mapping(current_mapping, graph,
           new_logical_qubit_ids, command_dag)``

    Attributes:
        current_mapping:  Stores the mapping: key is logical qubit id, value
            is mapped qubit id from 0,...,self.num_qubits
        storage (int): Approximate number of gate it caches before mapping.
        num_qubits(int): number of qubits
        num_mappings (int): Number of times the mapper changed the mapping
        depth_of_swaps (dict): Key are circuit depth of swaps, value is the
            number of such mappings which have beenapplied
        num_of_swaps_per_mapping (dict): Key are the number of swaps per
            mapping, value is the number of such mappings which have
            been applied
    """
    def __init__(self,
                 graph,
                 storage=1000,
                 add_qubits_to_mapping=_add_qubits_to_mapping,
                 opts=None):
        """
        Initialize a GraphMapper compiler engine.

        Args:
            graph (networkx.Graph): Arbitrary connected graph representing
                Qubit connectivity
            storage (int): Approximate number of gates to temporarily store
            add_qubits_to_mapping (function or str): Function called
                when new qubits are to be added to the current
                mapping.
                Special possible string values:

                - ``"fcfs"``: first-come first serve
                - ``"fcfs_init"``: first-come first serve with smarter mapping
                                   initialisation
            opts (dict): Extra options (see below)

        Raises:
            RuntimeError: if the graph is not a connected graph

        Note:
            ``opts`` may contain the following key-values:

           .. list-table::
               :header-rows: 1

               * - Key
                 - Type
                 - Description
               * - decay_opts
                 - ``dict``
                 -  | Options to pass onto the :py:class:`.DecayManager`
                      constructor
                    | (see :py:class:`._gate_manager.defaults`)
               * - swap_opts
                 - ``dict``
                 -  | Extra options used when generating a list of swap
                    | operations.
                    | Acceptable keys: W, cost_fun, near_term_layer_depth,
                    | max_swap_steps
                    | (see :py:meth:`.GateManager.generate_swaps`,
                    |  :py:class:`._graphmapper.defaults` and
                    |  :py:class:`._gate_manager.defaults`)
        """
        BasicMapperEngine.__init__(self)

        if opts is None:
            self._opts = {}
        else:
            self._opts = opts

        self.qubit_manager = GateManager(graph=graph,
                                         decay_opts=self._opts.get(
                                             'decay_opts', {
                                                 'delta': 0.001,
                                                 'max_lifetime': 5
                                             }))
        self.num_qubits = graph.number_of_nodes()
        self.storage = storage
        # Randomness to pick permutations if there are too many.
        # This creates an own instance of Random in order to not influence
        # the bound methods of the random module which might be used in other
        # places.
        self._rng = random.Random(11)
        # Logical qubit ids for which the Allocate gate has already been
        # processed and sent to the next engine but which are not yet
        # deallocated:
        self._currently_allocated_ids = set()
        # Our internal mappings
        self._current_mapping = dict()  # differs from other mappers
        self._reverse_current_mapping = dict()
        # Function to add new logical qubits ids to the mapping
        self.set_add_qubits_to_mapping(add_qubits_to_mapping)

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

    def set_add_qubits_to_mapping(self, add_qubits_to_mapping):
        """
        Modify the callback function used to add qubits to an existing mapping

        Args:
            add_qubits_to_mapping (function): Callback function

        Note:
           Signature for callback function is:
           ``add_qubits_to_mapping(current_mapping, graph,
           new_logical_qubit_ids, command_dag)``
        """
        if isinstance(add_qubits_to_mapping, str):
            if add_qubits_to_mapping.lower() == "fcfs":
                self._add_qubits_to_mapping = _add_qubits_to_mapping_fcfs
            elif add_qubits_to_mapping.lower() == "fcfs_init":
                self._add_qubits_to_mapping = _add_qubits_to_mapping_smart_init
            else:
                raise ValueError(
                    "Invalid invalid value for add_qubits_to_mapping: {}".
                    format(add_qubits_to_mapping))
        else:
            self._add_qubits_to_mapping = add_qubits_to_mapping

    def is_available(self, cmd):
        """Only allows 1 or two qubit gates."""
        num_qubits = 0
        for qureg in cmd.all_qubits:
            num_qubits += len(qureg)
        return num_qubits <= 2

    def _send_single_command(self, cmd):
        """
        Send a command to the next engine taking care of mapped qubit IDs

        Args:
            cmd (Command): A ProjectQ command
        """

        if isinstance(cmd.gate, AllocateQubitGate):
            assert cmd.qubits[0][0].id in self._current_mapping
            qb0 = WeakQubitRef(engine=self,
                               idx=self._current_mapping[cmd.qubits[0][0].id])
            self._currently_allocated_ids.add(cmd.qubits[0][0].id)
            self.send([
                Command(engine=self,
                        gate=AllocateQubitGate(),
                        qubits=([qb0], ),
                        tags=[LogicalQubitIDTag(cmd.qubits[0][0].id)])
            ])
        elif isinstance(cmd.gate, DeallocateQubitGate):
            assert cmd.qubits[0][0].id in self._current_mapping
            qb0 = WeakQubitRef(engine=self,
                               idx=self._current_mapping[cmd.qubits[0][0].id])
            self._currently_allocated_ids.remove(cmd.qubits[0][0].id)
            self._current_mapping.pop(cmd.qubits[0][0].id)
            self.send([
                Command(engine=self,
                        gate=DeallocateQubitGate(),
                        qubits=([qb0], ),
                        tags=[LogicalQubitIDTag(cmd.qubits[0][0].id)])
            ])
        else:
            self._send_cmd_with_mapped_ids(cmd)

    def _send_possible_commands(self):
        """
        Send as many commands as possible without introducing swap operations

        Note:
            This function will modify the current mapping when qubit
            allocation/deallocation gates are encountered
        """

        (cmds_to_execute,
         allocate_cmds) = self.qubit_manager.get_executable_commands(
             self._current_mapping)

        # Execute all the commands that can possibly be executed
        for cmd in cmds_to_execute:
            self._send_single_command(cmd)

        # There are no more commands to
        num_available_qubits = self.num_qubits - len(self._current_mapping)
        if allocate_cmds and num_available_qubits > 0:

            def rank_allocate_cmds(cmds_list, dag):
                # pylint: disable=unused-argument
                return cmds_list

            allocate_cmds = rank_allocate_cmds(
                allocate_cmds, self.qubit_manager.dag)[:num_available_qubits]
            not_in_mapping_qubits = [node.logical_id for node in allocate_cmds]

            new_mapping = self._add_qubits_to_mapping(self._current_mapping,
                                                      self.qubit_manager.graph,
                                                      not_in_mapping_qubits,
                                                      self.qubit_manager.dag)

            self.current_mapping = new_mapping

            for cmd in self.qubit_manager.execute_allocate_cmds(
                    allocate_cmds, self._current_mapping):
                self._send_single_command(cmd)

            cmds_to_execute, _ = self.qubit_manager.get_executable_commands(
                self._current_mapping)
            for cmd in cmds_to_execute:
                self._send_single_command(cmd)

    def _run(self):
        """
        Create a new mapping and executes possible gates.

        First execute all possible commands, given the current mapping. Then
        find a new mapping, perform the swap operawtions to get to the new
        mapping and then execute all possible gates once more. Non-allocated
        qubits that are required for the swap operations will be automatically
        allocated and deallocated as required.

        Raises:
            RuntimeError if the mapper is unable to make progress (possibly
            due to an insufficient number of qubits)
        """

        num_of_stored_commands_before = self.qubit_manager.size()

        self._send_possible_commands()
        if not self.qubit_manager.size():
            return

        # NB: default values are taken care of at place of access
        swap_opts = self._opts.get('swap_opts', {})

        swaps, all_swapped_qubits = self.qubit_manager.generate_swaps(
            self._current_mapping,
            cost_fun=swap_opts.get('cost_fun', defaults.cost_fun),
            opts=swap_opts,
            max_steps=swap_opts.get('max_swap_steps', defaults.max_swap_steps))

        if swaps:
            # Get a list of the qubits we need to allocate just to perform the
            # swaps
            not_allocated_ids = all_swapped_qubits.difference({
                self._current_mapping[logical_id]
                for logical_id in self._currently_allocated_ids
            })

            # Calculate temporary internal reverse mapping
            new_internal_mapping = deepcopy(self._reverse_current_mapping)

            # Allocate all mapped qubit ids that are not currently allocated
            # but part of some path so that we may perform the swapping
            # operations.
            for backend_id in not_allocated_ids:
                qb0 = WeakQubitRef(engine=self, idx=backend_id)
                self.send([
                    Command(engine=self,
                            gate=AllocateQubitGate(),
                            qubits=([qb0], ))
                ])

                # Those qubits are not part of the current mapping, so add them
                # to the temporary internal reverse mapping with invalid ids
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
            self.depth_of_swaps[depth] = self.depth_of_swaps.get(depth, 0) + 1
            self.num_of_swaps_per_mapping[len(
                swaps)] = self.num_of_swaps_per_mapping.get(len(swaps), 0) + 1

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
                    Command(engine=self,
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
        if self.qubit_manager.size() == num_of_stored_commands_before:
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

            qubit_ids = [
                qubit.id for qureg in cmd.all_qubits for qubit in qureg
            ]

            if len(qubit_ids) > 2 or not qubit_ids:
                raise Exception("Invalid command (number of qubits): "
                                + str(cmd))

            if isinstance(cmd.gate, FlushGate):
                while self.qubit_manager.size() > 0:
                    self._run()
                self.send([cmd])
            else:
                self.qubit_manager.add_command(cmd)

            # Storage is full: Create new map and send some gates away:
            if self.qubit_manager.size() >= self.storage:
                self._run()

    def __str__(self):
        """
        Return the string representation of this GraphMapper.

        Returns:
            A summary (string) of resources used, including depth of swaps and
            statistics about the swaps themselves
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

        return ("Number of mappings: {}\n" + "Depth of swaps:     {}\n\n"
                + "Number of swaps per mapping:{}\n\n{}\n\n").format(
                    self.num_mappings, depth_of_swaps_str,
                    num_swaps_per_mapping_str, str(self.qubit_manager))
