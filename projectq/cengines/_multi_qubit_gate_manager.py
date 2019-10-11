#   Copyright 2019 ProjectQ-Framework (www.projectq.ch)
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
This is a helper module for the :py:class:`projectq.cengines.GraphMapper`
class.

Implements a SABRE-like algorithm [1] to generate a list of SWAP operations to
route qubit through an arbitrary graph.

[1] https://arxiv.org/abs/1809.02573v2
"""

import networkx as nx
from projectq.ops import (AllocateQubitGate, DeallocateQubitGate)

# ==============================================================================


def _sum_distance_over_gates(node_list, mapping, distance_matrix):
    """
    Calculate the sum of distances between pairs of qubits

    Args:
        gate_list (list): List of 2-qubit gates
        mapping (dict): Current mapping
        distance_matrix (dict): Distance matrix within the hardware coupling
                                graph

    Returns:
        Sum of all pair-wise distances between qubits
    """
    return sum([
        distance_matrix[mapping[node.logical_id0]][mapping[node.logical_id1]]
        for node in node_list
    ])


def nearest_neighbours_cost_fun(gates_dag, mapping, distance_matrix, swap,
                                opts):
    """
    Nearest neighbours cost function

    .. math::

       H = \sum_{\mathrm{gate}\ \in\ F}
       D(\mathrm{gate}.q_1, \mathrm{gate}.q_2)

    where:

    - :math:`F` is the ensemble of gates in the front layer
    - :math:`D` is the distance matrix
    - :math:`\mathrm{gate}.q_{1, 2}` are the backend qubit IDs for each gate


    Args:
        gates_dag (CommandDAG): Direct acyclic graph of future quantum gates
        mapping (dict): Current mapping
        distance_matrix (dict): Distance matrix within the hardware coupling
                                graph
        swap (tuple): Candidate swap (not used by this function)
        opts (dict): Miscellaneous parameters for cost function (not used by
                     this function)

    Returns:
        Score of current swap operations
    """
    #pylint: disable=unused-argument
    return _sum_distance_over_gates(gates_dag.front_layer, mapping,
                                    distance_matrix)


def look_ahead_parallelism_cost_fun(gates_dag, mapping, distance_matrix, swap,
                                    opts):
    """
    Cost function using nearest-neighbour interactions as well as considering
    gates from the near-term layer (provided it has been calculated) in order
    to favour swap operations that can be performed in parallel.

    .. math::

       H = M \\left[\\frac{1}{|F|}\sum_{\mathrm{gate}\ \in\ F}
       D(\mathrm{gate}.q_1, \mathrm{gate}.q_2)
       + \\frac{W}{|E|}\sum_{\mathrm{gate}\ \in\ E}
       D(\mathrm{gate}.q_1, \mathrm{gate}.q_2) \\right]

    where:

    - :math:`M` is defined as :math:`\max(decay(SWAP.q_1), decay(SWAP.q_2))`
    - :math:`F` is the ensemble of gates in front layer
    - :math:`E` is the ensemble of gates in near-term layer
    - :math:`D` is the distance matrix
    - :math:`\mathrm{gate}.q_{1, 2}` are the backend qubit IDs for each gate


    Args:
        gates_dag (CommandDAG): Direct acyclic graph of future quantum gates
        mapping (dict): Current mapping
        distance_matrix (dict): Distance matrix within the hardware coupling
                                graph
        swap (tuple): Candidate swap operation
        opts (dict): Miscellaneous parameters for cost function

    Returns:
        Score of current swap operations

    Note:
        ``opts`` must contain the following key-values

        .. list-table::
            :header-rows: 1

            * - Key
              - Type
              - Description
            * - decay
              - :py:class:`.DecayManager`
              - | Instance containing current decay information for each
                | backend qubit
            * - W
              - ``float``
              - Weighting factor (see cost function formula)
    """
    decay = opts['decay']
    near_term_weight = opts['W']

    n_front = len(gates_dag.front_layer_for_cost_fun)
    n_near = len(gates_dag.near_term_layer)

    decay_factor = max(decay.get_decay_value(swap[0]),
                       decay.get_decay_value(swap[1]))
    front_layer_term = (1. / n_front * _sum_distance_over_gates(
        gates_dag.front_layer_for_cost_fun, mapping, distance_matrix))

    if n_near == 0:
        return decay_factor * front_layer_term
    return (decay_factor *
            (front_layer_term +
             (near_term_weight / n_near * _sum_distance_over_gates(
                 gates_dag.near_term_layer, mapping, distance_matrix))))


# ==============================================================================


def _apply_swap_to_mapping(mapping, logical_id0, logical_id1, backend_id1):
    """
    Modify a mapping by applying a SWAP operation

    Args:
        mapping (dict): mapping to update
        logical_id0 (int): A logical qubit ID
        logical_id1 (int): A logical qubit ID
        backend_id1 (int): Backend ID corresponding to ``logical_id1``

    .. note::

    ``logical_id1`` can be set to -1 to indicate a non-allocated backend qubit
    """
    # If the qubit is present in the mapping (ie. second qubit is already
    # allocated), update the mapping, otherwise simply assign the new backend
    # ID to the qubit being swapped.

    if logical_id1 != -1:
        mapping[logical_id0], mapping[logical_id1] \
            = mapping[logical_id1], mapping[logical_id0]
    else:
        mapping[logical_id0] = backend_id1


# ==============================================================================


class DecayManager(object):
    """
    Class managing the decay information about a list of backend qubit IDs

    User should call the :py:meth:`step` method each time a swap gate is added and
    :py:meth:`remove_decay` once a 2-qubit gate is executed.
    """

    # def __repr__(self):
    #     s = ''
    #     for backend_id in self._backend_ids:
    #         tmp = self._backend_ids[backend_id]
    #         s += '\n  {:2}: {}, {}'.format(backend_id, tmp.decay, tmp.lifetime)
    #     s += '\n'
    #     return s

    def __init__(self, delta, max_lifetime):
        """
        Constructor

        Args:
            delta (float): Decay parameter
            max_lifetime (int): Maximum lifetime of decay information for a
                                particular qubit
        """
        self._delta = delta
        self._cutoff = max_lifetime
        self._backend_ids = {}

    def clear(self):
        """
        Clear the state of a DecayManager
        """
        self._backend_ids = {}

    def add_to_decay(self, backend_id):
        """
        Add to the decay to a particular backend qubit ID

        Args:
            backend_id (int) : Backend qubit ID
        """
        # Ignore invalid (ie. non-allocated) backend IDs
        if backend_id < 0:
            return

        if backend_id in self._backend_ids:
            self._backend_ids[backend_id]['lifetime'] = self._cutoff
            self._backend_ids[backend_id]['decay'] += self._delta
        else:
            self._backend_ids[backend_id] = {
                'decay': 1 + self._delta,
                'lifetime': self._cutoff
            }

    def remove_decay(self, backend_id):
        """
        Remove the decay of a particular backend qubit ID

        Args:
            backend_id (int) : Backend qubit ID
        """
        if backend_id in self._backend_ids:
            del self._backend_ids[backend_id]

    def get_decay_value(self, backend_id):
        """
        Retrieve the decay value of a particular backend qubit ID

        Args:
            backend_id (int) : Backend qubit ID
        """
        if backend_id in self._backend_ids:
            return self._backend_ids[backend_id]['decay']
        return 1

    def step(self):
        """
        Step all decay values in time

        Use this method to indicate a SWAP search step has been performed.
        """
        backend_ids = list(self._backend_ids)
        for backend_id in backend_ids:
            self._backend_ids[backend_id]['lifetime'] -= 1
            if self._backend_ids[backend_id]['lifetime'] == 0:
                del self._backend_ids[backend_id]


# ==============================================================================


class _DAGNodeBase(object):
    #pylint: disable=too-few-public-methods
    def __init__(self, cmd, *args):
        self.logical_ids = frozenset(args)
        self.cmd = cmd
        self.compatible_successor_cmds = []

    def append_compatible_cmd(self, cmd):
        """
        Append a compatible commands to this DAG node

        Args:
            cmd (Command): A ProjectQ command
        """
        self.compatible_successor_cmds.append(cmd)


class _DAGNodeSingle(_DAGNodeBase):
    """
    Node representing a single qubit gate as part of a Direct Acyclic Graph
    (DAG) of quantum gates
    """

    #pylint: disable=too-few-public-methods
    def __init__(self, cmd, logical_id):
        super(_DAGNodeSingle, self).__init__(cmd, logical_id)
        self.logical_id = logical_id


class _DAGNodeDouble(_DAGNodeBase):
    """
    Node representing a 2-qubit gate as part of a Direct Acyclic Graph (DAG)
    of quantum gates
    """

    #pylint: disable=too-few-public-methods
    def __init__(self, cmd, logical_id0, logical_id1):
        super(_DAGNodeDouble, self).__init__(cmd, logical_id0, logical_id1)
        self.logical_id0 = logical_id0
        self.logical_id1 = logical_id1


class CommandDAG(object):
    """
    Class managing a list of multi-qubit gates and storing them into a Direct
    Acyclic Graph (DAG) in order of precedence.
    """
    def __init__(self):
        self._dag = nx.DiGraph()
        self._logical_ids_in_diag = set()
        self.front_layer = []
        self.front_layer_for_cost_fun = []
        self.near_term_layer = []
        self._back_layer = {}

    def size(self):
        """
        Return the size of the DAG (ie. number of nodes)

        Note:
            This need not be the number of commands stored within the DAG.
        """
        return self._dag.number_of_nodes()

    def clear(self):
        """
        Clear the state of a DAG

        Remove all nodes from the DAG and all layers.
        """
        self._dag.clear()
        self._logical_ids_in_diag = set()
        self.front_layer_for_cost_fun = []
        self.front_layer = []
        self.near_term_layer = []
        self._back_layer = {}

    def add_command(self, cmd):
        """
        Add a command to the DAG

        Args:
            cmd (Command): A ProjectQ command
        """
        logical_ids = [qubit.id for qureg in cmd.all_qubits for qubit in qureg]

        if len(logical_ids) == 2:
            logical_id0_in_dag = logical_ids[0] in self._logical_ids_in_diag
            logical_id1_in_dag = logical_ids[1] in self._logical_ids_in_diag

            if (logical_id0_in_dag and logical_id1_in_dag and self._back_layer[
                    logical_ids[0]] == self._back_layer[logical_ids[1]]):
                self._back_layer[logical_ids[1]].append_compatible_cmd(cmd)
                return

            new_node = _DAGNodeDouble(cmd, *logical_ids)
            self._dag.add_node(new_node)

            if logical_id0_in_dag:
                self._dag.add_edge(self._back_layer[logical_ids[0]], new_node)
                self._logical_ids_in_diag.add(logical_ids[1])
            else:
                self._logical_ids_in_diag.add(logical_ids[0])

            if logical_id1_in_dag:
                self._dag.add_edge(self._back_layer[logical_ids[1]], new_node)
                self._logical_ids_in_diag.add(logical_ids[0])
            else:
                self._logical_ids_in_diag.add(logical_ids[1])

            self._back_layer[logical_ids[0]] = new_node
            self._back_layer[logical_ids[1]] = new_node

            # If both qubit are not already in the DAG, then we just got a new
            # gate on the front layer
            if not logical_id0_in_dag and not logical_id1_in_dag:
                self.front_layer_for_cost_fun.append(new_node)
                self.front_layer.append(new_node)
        else:
            logical_id = logical_ids[0]
            logical_id_in_dag = logical_id in self._logical_ids_in_diag

            if isinstance(cmd.gate, (AllocateQubitGate, DeallocateQubitGate)):
                new_node = _DAGNodeSingle(cmd, logical_id)
                self._dag.add_node(new_node)

                if logical_id_in_dag:
                    self._dag.add_edge(self._back_layer[logical_id], new_node)
                else:
                    self._logical_ids_in_diag.add(logical_id)

                    self.front_layer.append(new_node)

                self._back_layer[logical_id] = new_node
            else:
                if not logical_id_in_dag:
                    new_node = _DAGNodeSingle(cmd, logical_id)
                    self._dag.add_node(new_node)
                    self._logical_ids_in_diag.add(logical_id)

                    self._back_layer[logical_id] = new_node

                    self.front_layer.append(new_node)
                else:
                    self._back_layer[logical_id].append_compatible_cmd(cmd)

    def remove_from_front_layer(self, cmd):
        """
        Remove a gate from the front layer of the DAG

        Args:
            cmd (Command): A ProjectQ command

        Raises:
            RuntimeError if the gate does not exist in the front layer
        """
        # First find the gate inside the first layer list
        node = next((node for node in self.front_layer if node.cmd is cmd),
                    None)
        if not node:
            raise RuntimeError('({}) not found in DAG'.format(cmd))

        logical_ids = [qubit.id for qureg in cmd.all_qubits for qubit in qureg]

        descendants = list(self._dag[node])

        if not descendants:
            for logical_id in logical_ids:
                self._logical_ids_in_diag.remove(logical_id)
                del self._back_layer[logical_id]
            self._dag.remove_node(node)
        else:
            if len(descendants) == 1:
                if isinstance(node, _DAGNodeDouble):
                    # Look for the logical_id not found in the descendant
                    logical_id, tmp = logical_ids
                    if logical_id in descendants[0].logical_ids:
                        logical_id = tmp

                    self._logical_ids_in_diag.remove(logical_id)
                    del self._back_layer[logical_id]

            # Remove gate from DAG
            self._dag.remove_node(node)

            for descendant in descendants:
                if not self._dag.pred[descendant]:
                    self.front_layer.append(descendant)
                    if isinstance(descendant, _DAGNodeDouble):
                        self.front_layer_for_cost_fun.append(descendant)

        # Remove the gate from the first layer
        self.front_layer.remove(node)
        if isinstance(node, _DAGNodeDouble):
            self.front_layer_for_cost_fun.remove(node)

    def max_distance_in_dag(self):
        """
        Calculate the distance between the front layer and each node of the
        DAG.

        A gate with distance 0 is on the front layer.

        Returns:
            Python dictionary indexed by gate with their distance as value
        """
        node_max_distance = {}
        for node in self.front_layer:
            node_max_distance[node] = 0
            self._max_distance_in_dag(node_max_distance, node, 1)

        return node_max_distance

    def calculate_near_term_layer(self, mapping):
        """
        Calculate the first order near term layer.

        This is the set of gates that will become the front layer once these
        get executed.

        Args:
            mapping (dict): current mapping
        """
        near_term_layer_candidates = []
        for node in self.front_layer_for_cost_fun:
            for descendant in self._dag[node]:
                if (isinstance(descendant, _DAGNodeDouble)
                        and descendant.logical_id0 in mapping
                        and descendant.logical_id1 in mapping):
                    near_term_layer_candidates.append(descendant)

        # Only add candidates for which all predecessors are in the front layer
        self.near_term_layer = []
        for node in near_term_layer_candidates:
            for predecessor in self._dag.pred[node]:
                if predecessor not in self.front_layer:
                    break
            else:
                if node not in self.near_term_layer:
                    self.near_term_layer.append(node)

    def calculate_interaction_list(self):
        """
        List all known interactions between multiple qubits

        Returns:
            List of tuples of logical qubit IDs for each 2-qubit gate present
            in the DAG.
        """
        interactions = []
        for node in self._dag:
            if isinstance(node, _DAGNodeDouble):
                interactions.append(tuple(node.logical_ids))
        return interactions

    def calculate_qubit_interaction_subgraphs(self, max_order=2):
        """
        Calculate qubits interaction graph based on all commands stored.

        The interaction graph has logical qubit IDs as nodes and edges
        represent a 2-qubit gate between qubits.

        Args:
            max_order (int): Maximum degree of the nodes in the resulting
                             graph

        Returns:
            A list of list of graph nodes corresponding to all the connected
            components of the qubit interaction graph. Within each components,
            nodes are sorted in decreasing order of their degree.
        """
        graph = nx.Graph()

        for node in self.front_layer:
            self._add_to_interaction_graph(node, graph, max_order)

        return [
            sorted(graph.subgraph(g),
                   key=lambda n: len(graph[n]),
                   reverse=True) for g in sorted(
                       nx.connected_components(graph),
                       key=lambda c: (max(len(graph[n]) for n in c), len(c)),
                       reverse=True)
        ]

    def _add_to_interaction_graph(self, node, graph, max_order):
        """
        Recursively add an interaction to the interaction graph

        Args:
            node (_DAGNodeDouble): Node from DAG
            graph (networkx.Graph): Interaction graph
            max_order (int): Maximum degree of the nodes in the resulting
                             interaction graph
        """
        if isinstance(node, _DAGNodeDouble) \
            and (node.logical_id0 not in graph \
                 or node.logical_id1 not in graph \
                 or (len(graph[node.logical_id0]) < max_order
                         and len(graph[node.logical_id1]) < max_order)):
            graph.add_edge(node.logical_id0, node.logical_id1)

        for descendant in self._dag[node]:
            self._add_to_interaction_graph(descendant, graph, max_order)

    def _max_distance_in_dag(self, node_max_distance, node, distance):
        """
        Recursively calculate the maximum distance for each node of the DAG

        Args:
            node_max_distance (dict): Dictionary containing the current
                                      maximum distance for each node
            node (_DAGNode): Root node from DAG for traversal
            distance (int): Current distance offset
        """
        for descendant in self._dag[node]:
            try:
                if node_max_distance[descendant] < distance:
                    node_max_distance[descendant] = distance
            except KeyError:
                node_max_distance[descendant] = distance

            if self._dag[descendant]:
                self._max_distance_in_dag(node_max_distance, descendant,
                                          distance + 1)


# ==============================================================================


class MultiQubitGateManager(object):
    """
    Class managing qubit interactions
    """
    def __init__(self, graph, decay_opts=None):
        """
        Args:
            graph (networkx.Graph): an arbitrary connected graph
        """
        # Make sure that we start with a valid graph
        if not nx.is_connected(graph):
            raise RuntimeError("Input graph must be a connected graph")

        if not all([isinstance(n, int) for n in graph]):
            raise RuntimeError(
                "All nodes inside the graph needs to be integers")

        self.graph = graph
        self.distance_matrix = dict(
            nx.all_pairs_shortest_path_length(self.graph))

        if decay_opts is None:
            decay_opts = {}
        self._dag = CommandDAG()
        self._decay = DecayManager(decay_opts.get('delta', 0.001),
                                   decay_opts.get('max_lifetime', 5))

    def size(self):
        """
        Return the size of the underlying DAG

        .. seealso::
           :py:meth:`.CommandDAG.size`
        """
        return self._dag.size()

    def clear(self):
        """
        Return the size of the underlying DAG

        .. seealso::
           :py:meth:`.CommandDAG.clear`
           :py:meth:`.DecayManager.clear`
        """
        self._dag.clear()
        self._decay.clear()

    def generate_swaps(self,
                       current_mapping,
                       cost_fun,
                       opts=None,
                       max_steps=100):
        """
        Generate a list of swaps to execute some quantum gates

        Args:
            mapping (dict): Current mapping
            cost_fun (function): Cost function to rank swap candidates
                                 Must accept the following parameters:
                                 - dag (_GatesDAG)
                                 - new_mapping (dict)
                                 - distance_matrix (dict)
                                 - swap_candidate (tuple)
            max_steps (int): (optional) Maximum number of swap steps to
                             attempt before giving up
            opts (dict): (optional) Extra parameters for cost function call
                                    (see note below)

        .. note::

          The ``opts`` optional parameter may contain the following key-values:

          .. list-table::
              :header-rows: 1

              * - Key
                - Type
                - Description
              * - near_term_layer
                - ``int``
                -  | If 0 (default) do not consider near-term gates
                   | when generating the list of swap operations.
                   | If >0, calculate the near-term layer using
                   | all gates in the DAG that have a distance equal
                   | to or less than this value.
              * - ...
                - ...
                -  | Any other parameter will be passed onto the cost
                   | function when it is called.

        Returns:
            A tuple (list, set) of swap operations (tuples of backend IDs) and
            a set of all the backend IDs that are traversed by the SWAP
            operations.
        """

        if not self._dag.front_layer_for_cost_fun:
            return ([], set())

        if opts is None:
            opts = {}

        self._decay.clear()
        opts['decay'] = self._decay

        self._dag.calculate_near_term_layer(current_mapping)

        mapping = current_mapping.copy()
        swaps = []
        all_swapped_qubits = set()
        while not self._can_execute_some_gate(mapping):
            (logical_id0, backend_id0, logical_id1,
             backend_id1) = self._generate_one_swap_step(
                 mapping, cost_fun, opts)
            swaps.append((mapping[logical_id0], backend_id1))
            all_swapped_qubits.add(backend_id0)
            all_swapped_qubits.add(backend_id1)

            self._decay.add_to_decay(backend_id0)
            self._decay.add_to_decay(backend_id1)
            self._decay.step()

            _apply_swap_to_mapping(mapping, logical_id0, logical_id1,
                                   backend_id1)

            if len(swaps) > max_steps:
                raise RuntimeError(
                    'Maximum number of steps ({}) to find a list of'.format(
                        max_steps)
                    + ' SWAP operations reached without convergence')

        return swaps, all_swapped_qubits

    def add_command(self, cmd):
        """
        Add a command to the underlying DAG

        Args:
            cmd (Command): A ProjectQ command

        .. seealso::
          :py:meth:`.GatesDAG.add_command`
        """

        return self._dag.add_command(cmd)

    def get_executable_commands(self, mapping):
        """
        Find as many executable commands as possible given a mapping

        Args:
            mapping (dict): Current mapping

        Returns:
            A tuple (cmds_to_execute, allocate_cmds) where the first one is a
            list of ProjectQ commands that can be executed and the second a
            list of allocation commands for qubits not in the current mapping
        """
        cmds_to_execute = []
        allocate_cmds = []
        has_command_to_execute = True

        while has_command_to_execute:
            # Reset after each pass
            has_command_to_execute = False

            for node in self._dag.front_layer.copy():
                if isinstance(node, _DAGNodeSingle):
                    if isinstance(node.cmd.gate, AllocateQubitGate):
                        # Allocating a qubit already in mapping is allowed
                        if node.logical_id in mapping:
                            has_command_to_execute = True
                            cmds_to_execute.append(node.cmd)
                            cmds_to_execute.extend(
                                node.compatible_successor_cmds)
                            self._dag.remove_from_front_layer(node.cmd)
                        elif node not in allocate_cmds:
                            allocate_cmds.append(node)
                    elif node.logical_id in mapping:
                        has_command_to_execute = True
                        cmds_to_execute.append(node.cmd)
                        cmds_to_execute.extend(node.compatible_successor_cmds)
                        self._dag.remove_from_front_layer(node.cmd)
                elif node.logical_id0 in mapping and node.logical_id1 in mapping:
                    if self.graph.has_edge(mapping[node.logical_id0],
                                           mapping[node.logical_id1]):
                        has_command_to_execute = True
                        cmds_to_execute.append(node.cmd)
                        cmds_to_execute.extend(node.compatible_successor_cmds)
                        self._dag.remove_from_front_layer(node.cmd)

        return cmds_to_execute, allocate_cmds

    def execute_allocate_cmds(self, allocate_cmds, mapping):
        """
        Executea list of allocate commands (ie. remove them from the front
        layer)

        Args:
            allocate_cmds (list): A list of Allocate commands (DAG nodes)
            mapping (dict): Current mapping

        Returns:
            A list of ProjectQ commands to be executed
        """
        cmds_to_execute = []
        for node in allocate_cmds:
            assert isinstance(node.cmd.gate, AllocateQubitGate)
            if node.logical_id in mapping:
                cmds_to_execute.append(node.cmd)
                cmds_to_execute.extend(node.compatible_successor_cmds)
                self._dag.remove_from_front_layer(node.cmd)

        return cmds_to_execute

    # ==========================================================================

    def calculate_qubit_interaction_subgraphs(self, max_order=2):
        """
        Calculate qubits interaction graph based on all commands stored.

        Args:
            max_order (int): Maximum degree of the nodes in the resulting
                             interaction graph

        Returns:
            A list of list of graph nodes corresponding to all the connected
            components of the qubit interaction graph. Within each components,
            nodes are sorted in decreasing order of their degree.

        .. seealso::
           :py:meth:`CommandDAG.calculate_qubit_interaction_subgraphs`
        """
        return self._dag.calculate_qubit_interaction_subgraphs(max_order)

    # ==========================================================================

    def _generate_one_swap_step(self, mapping, cost_fun, opts):
        """
        Find the most optimal swap operation to perform next

        Args:
            mapping (dict): Current mapping
            cost_fun (function): Cost function to rank swap candidates
                                 Must accept the following parameters:
                                   - dag (_GatesDAG)
                                   - new_mapping (dict)
                                   - distance_matrix (dict)
                                   - swap_candidate (tuple)

        Returns:
            Tuple with (logical_id0, backend_id0, logical_id1, backend_id1)
            where logical_id1 can be -1 if backend_id1 does not currently have
            a logical qubit associated to it.
        """

        reverse_mapping = {v: k for k, v in mapping.items()}

        # Only consider gates from the front layer and generate a list of
        # potential SWAP operations with all qubits that are neighours of
        # those concerned by a gate

        swap_candidates = []
        for node in self._dag.front_layer_for_cost_fun:
            for logical_id in node.logical_ids:
                for backend_id1 in self.graph[mapping[logical_id]]:
                    swap_candidates.append(
                        (logical_id, mapping[logical_id],
                         reverse_mapping.get(backend_id1, -1), backend_id1))

        # Rank swap candidates using the provided cost function
        scores = []
        for logical_id0, backend_id0, logical_id1, backend_id1 in swap_candidates:
            new_mapping = mapping.copy()

            _apply_swap_to_mapping(new_mapping, logical_id0, logical_id1,
                                   backend_id1)

            scores.append(
                cost_fun(self._dag, new_mapping, self.distance_matrix,
                         (backend_id0, backend_id1), opts))

        # Return the swap candidate with the lowest score
        return swap_candidates[scores.index(min(scores))]

    def _can_execute_some_gate(self, mapping):
        """
        Test whether some gate from the front layer can be executed

        Args:
            mapping (dict): Current mapping
        """
        for node in self._dag.front_layer:
            if isinstance(node, _DAGNodeSingle) and node.logical_id in mapping:
                return True

            if (isinstance(node, _DAGNodeDouble) and self.graph.has_edge(
                    mapping[node.logical_id0], mapping[node.logical_id1])):
                return True
        return False
