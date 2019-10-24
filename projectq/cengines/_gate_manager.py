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
import math
from projectq.ops import (AllocateQubitGate, DeallocateQubitGate)

# ==============================================================================


class defaults(object):
    """
    Class containing default values for some options
    """

    delta = 0.001
    max_lifetime = 5
    near_term_layer_depth = 1
    W = 0.5


# ==============================================================================


def _topological_sort(dag):
    """
    Returns a generator of nodes in topologically sorted order.

    A topological sort is a nonunique permutation of the nodes such that an
    edge from u to v implies that u appears before v in the topological sort
    order.

    Args:
        dag (networkx.DiGraph): A Directed Acyclic Graph (DAG)

    Returns:
        An iterable of node names in topological sorted order.

    Note:
        This implementation is based on
        :py:func:`networkx.algorithms.dag.topological_sort`
    """
    indegree_map = {}
    zero_indegree = []
    for node, degree in dag.in_degree():
        if degree > 0:
            indegree_map[node] = degree
        else:
            zero_indegree.append(node)

    while zero_indegree:
        node = zero_indegree.pop()
        for child in dag[node]:
            indegree_map[child] -= 1
            if indegree_map[child] == 0:
                zero_indegree.append(child)
                del indegree_map[child]
        yield node


# Coffaman-Graham algorithm with infinite width
def _coffman_graham_ranking(dag):
    """
    Apply the Coffman-Grapham layering algorithm to a DAG (with infinite width)

    Args:
        dag (networkx.DiGraph): A Directed Acyclic Graph (DAG)

    Returns:
        A list of layers (Python list of lists).

    Note:
        This function does not limit the width of any layers.
    """
    layers = [[]]
    levels = {}

    for node in _topological_sort(dag):
        dependant_level = -1
        for dependant in dag.pred[node]:
            level = levels[dependant]
            if level > dependant_level:
                dependant_level = level

        level = -1
        if dependant_level < len(layers) - 1:
            level = dependant_level + 1
        if level < 0:
            layers.append([])
            level = len(layers) - 1

        layers[level].append(node)
        levels[node] = level

    for layer in layers:
        layer.sort(key=lambda node: node.node_id)
    return layers


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
    r"""
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
    # pylint: disable=unused-argument
    return _sum_distance_over_gates(gates_dag.front_layer_2qubit, mapping,
                                    distance_matrix)


def look_ahead_parallelism_cost_fun(gates_dag, mapping, distance_matrix, swap,
                                    opts):
    r"""
    Cost function using nearest-neighbour interactions as well as considering
    gates from the near-term layer (provided it has been calculated) in order
    to favour swap operations that can be performed in parallel.

    .. math::

       H = M \left[\frac{1}{|F|}\sum_{\mathrm{gate}\ \in\ F}
       D(\mathrm{gate}.q_1, \mathrm{gate}.q_2)
       + \frac{W}{|E|}\sum_{\mathrm{gate}\ \in\ E}
       D(\mathrm{gate}.q_1, \mathrm{gate}.q_2) \right]

    where:

    - :math:`M` is defined as :math:`\max(\mathrm{decay}(SWAP.q_1),
      \mathrm{decay}(SWAP.q_2))`
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
    near_term_weight = opts.get('W', defaults.W)

    n_front = len(gates_dag.front_layer_2qubit)
    n_near = len(gates_dag.near_term_layer)

    decay_factor = max(decay.get_decay_value(swap[0]),
                       decay.get_decay_value(swap[1]))
    front_layer_term = (1. / n_front * _sum_distance_over_gates(
        gates_dag.front_layer_2qubit, mapping, distance_matrix))

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

    User should call the :py:meth:`step` method each time a swap gate is added
    and :py:meth:`remove_decay` once a 2-qubit gate is executed.
    """
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
    # pylint: disable=too-few-public-methods
    def __init__(self, node_id, cmd, *args):
        self.node_id = node_id
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

    # pylint: disable=too-few-public-methods
    def __init__(self, node_id, cmd, logical_id):
        super(_DAGNodeSingle, self).__init__(node_id, cmd, logical_id)
        self.logical_id = logical_id


class _DAGNodeDouble(_DAGNodeBase):
    """
    Node representing a 2-qubit gate as part of a Direct Acyclic Graph (DAG)
    of quantum gates
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, node_id, cmd, logical_id0, logical_id1):
        super(_DAGNodeDouble, self).__init__(node_id, cmd, logical_id0,
                                             logical_id1)
        self.logical_id0 = logical_id0
        self.logical_id1 = logical_id1


class CommandDAG(object):
    """
    Class managing a list of multi-qubit gates and storing them into a Direct
    Acyclic Graph (DAG) in order of precedence.
    """
    def __init__(self):
        self._dag = nx.DiGraph()
        self._node_id = 0
        self._logical_ids_in_diag = set()
        self.near_term_layer = []

        self._layers_up_to_date = True
        self._front_layer = []
        self._front_layer_2qubit = []
        self._layers = [[]]
        self._back_layer = {}

    @property
    def front_layer(self):
        self.calculate_command_hierarchy()
        return self._layers[0]

    @property
    def front_layer_2qubit(self):
        self.calculate_command_hierarchy()
        return self._front_layer_2qubit

    def size(self):
        """
        Return the size of the DAG (ie. number of nodes)

        Note:
            This may not be equal to the number of commands stored within the
            DAG as some nodes might store more than one gate if they are
            compatible.
        """
        return self._dag.number_of_nodes()

    def clear(self):
        """
        Clear the state of a DAG

        Remove all nodes from the DAG and all layers.
        """
        self._dag.clear()
        self._node_id = 0
        self._logical_ids_in_diag = set()
        self.near_term_layer = []

        self._layers_up_to_date = True
        self._front_layer = []
        self._front_layer_2qubit = []
        self._layers = [[]]
        self._back_layer = {}

    def calculate_command_hierarchy(self):
        if not self._layers_up_to_date:
            self._layers = _coffman_graham_ranking(self._dag)
            self._front_layer_2qubit = [
                node for node in self._layers[0]
                if isinstance(node, _DAGNodeDouble)
            ]
            self._layers_up_to_date = True

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

            new_node = _DAGNodeDouble(self._node_id, cmd, *logical_ids)
            self._node_id += 1
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

            self._layers_up_to_date = False
        else:
            logical_id = logical_ids[0]
            logical_id_in_dag = logical_id in self._logical_ids_in_diag

            if isinstance(cmd.gate, (AllocateQubitGate, DeallocateQubitGate)):
                new_node = _DAGNodeSingle(self._node_id, cmd, logical_id)
                self._node_id += 1
                self._dag.add_node(new_node)

                if logical_id_in_dag:
                    self._dag.add_edge(self._back_layer[logical_id], new_node)
                else:
                    self._logical_ids_in_diag.add(logical_id)

                self._back_layer[logical_id] = new_node
                self._layers_up_to_date = False
            else:
                if not logical_id_in_dag:
                    new_node = _DAGNodeSingle(self._node_id, cmd, logical_id)
                    self._node_id += 1
                    self._dag.add_node(new_node)
                    self._logical_ids_in_diag.add(logical_id)

                    self._back_layer[logical_id] = new_node
                    self._layers_up_to_date = False
                else:
                    self._back_layer[logical_id].append_compatible_cmd(cmd)

    def calculate_near_term_layer(self, mapping, depth=1):
        """
        Calculate the first order near term layer.

        This is the set of gates that will become the front layer once these
        get executed.

        Args:
            mapping (dict): current mapping
        """
        self.calculate_command_hierarchy()
        self.near_term_layer = []
        if len(self._layers) > 1:
            for layer in self._layers[1:depth + 1]:
                self.near_term_layer.extend([
                    node for node in layer
                    if (isinstance(node, _DAGNodeDouble) and node.logical_id0
                        in mapping and node.logical_id1 in mapping)
                ])

    def calculate_interaction_list(self):
        """
        List all known interactions between multiple qubits

        Returns:
            List of tuples of logical qubit IDs for each 2-qubit gate present
            in the DAG.
        """
        return [(node.logical_id0, node.logical_id1) for node in self._dag
                if isinstance(node, _DAGNodeDouble)]

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
        self.calculate_command_hierarchy()

        graph = nx.Graph()
        for layer in self._layers:
            for node in layer:
                if isinstance(node, _DAGNodeDouble):
                    node0_in_graph = node.logical_id0 in graph
                    node1_in_graph = node.logical_id1 in graph

                    add_edge = True
                    if (node0_in_graph
                            and len(graph[node.logical_id0]) >= max_order):
                        add_edge = False
                    if (node1_in_graph
                            and len(graph[node.logical_id1]) >= max_order):
                        add_edge = False

                    if add_edge or graph.has_edge(node.logical_id0,
                                                  node.logical_id1):
                        graph.add_edge(node.logical_id0, node.logical_id1)
                    else:
                        break
            else:
                continue  # only executed if the inner loop did NOT break
            break  # only executed if the inner loop DID break

        return [
            sorted(graph.subgraph(g),
                   key=lambda n: len(graph[n]),
                   reverse=True) for g in sorted(
                       nx.connected_components(graph),
                       key=lambda c: (max(len(graph[n]) for n in c), len(c)),
                       reverse=True)
        ]

    def remove_command(self, cmd):
        """
        Remove a command from the DAG

        Note:
            Only commands present in the front layer of the DAG can be
            removed.

        Args:
            cmd (Command): A ProjectQ command

        Raises:
            RuntimeError if the gate does not exist in the front layer
        """
        # First find the gate inside the front layer list
        node = next((node for node in self.front_layer if node.cmd is cmd),
                    None)
        if node is None:
            raise RuntimeError(
                '({}) not found in front layer of DAG'.format(cmd))

        logical_ids = {qubit.id for qureg in cmd.all_qubits for qubit in qureg}

        descendants = list(self._dag[node])

        if not descendants:
            self._logical_ids_in_diag -= logical_ids
            for logical_id in logical_ids:
                del self._back_layer[logical_id]
        elif len(descendants) == 1 and isinstance(node, _DAGNodeDouble):
            logical_id, = logical_ids.difference(descendants[0].logical_ids)

            self._logical_ids_in_diag.remove(logical_id)
            del self._back_layer[logical_id]

        # Remove gate from DAG
        self._dag.remove_node(node)

        self._layers_up_to_date = False


# ==============================================================================


class GateManager(object):
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
        self.dag = CommandDAG()
        self._decay = DecayManager(
            decay_opts.get('delta', defaults.delta),
            decay_opts.get('max_lifetime', defaults.max_lifetime))
        self._stats = {
            'simul_exec': [],
            '2qubit_gates_loc': {},
        }

    def __str__(self):
        """
        Return the string representation of this MultiQubitGateManager.

        Returns:
            A summary (string) about the commands executed.
        """

        max_width = int(
            math.ceil(math.log10(max(
                self._stats['2qubit_gates_loc'].values()))) + 1)
        interactions_str = ""
        for (backend_id0, backend_id1), number \
            in sorted(self._stats['2qubit_gates_loc'].items(),
                      key=lambda x: x[1], reverse=True):
            interactions_str += "\n    {0}: {1:{2}}".format(
                sorted([backend_id0, backend_id1]), number, max_width)

        return ('2-qubit gates locations:{}').format(interactions_str)

    def size(self):
        """
        Return the size of the underlying DAG

        .. seealso::
           :py:meth:`.CommandDAG.size`
        """
        return self.dag.size()

    def clear(self):
        """
        Return the size of the underlying DAG

        .. seealso::
           :py:meth:`.CommandDAG.clear`
           :py:meth:`.DecayManager.clear`
        """
        self.dag.clear()
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

        .. seealso::
           :py:meth:`nearest_neighbours_cost_fun`
           :py:meth:`look_ahead_parallelism_cost_fun`

        Returns:
            A tuple (list, set) of swap operations (tuples of backend IDs) and
            a set of all the backend IDs that are traversed by the SWAP
            operations.
        """

        if not self.dag.front_layer_2qubit:
            return ([], set())

        if opts is None:
            opts = {}

        self._decay.clear()
        opts['decay'] = self._decay

        self.dag.calculate_near_term_layer(
            current_mapping,
            opts.get('near_term_layer_depth', defaults.near_term_layer_depth))

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

        self.dag.add_command(cmd)

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
        self._stats['simul_exec'].append(0)

        def _add_to_execute_list(node):
            cmds_to_execute.append(node.cmd)
            cmds_to_execute.extend(node.compatible_successor_cmds)
            self.dag.remove_command(node.cmd)

        self.dag.calculate_command_hierarchy()

        while has_command_to_execute:
            # Reset after each pass
            has_command_to_execute = False

            for node in self.dag.front_layer:
                if isinstance(node, _DAGNodeSingle):
                    if isinstance(node.cmd.gate, AllocateQubitGate):
                        # Allocating a qubit already in mapping is allowed
                        if node.logical_id in mapping:
                            has_command_to_execute = True
                            _add_to_execute_list(node)
                        elif node not in allocate_cmds:
                            allocate_cmds.append(node)
                    elif node.logical_id in mapping:
                        has_command_to_execute = True
                        self._stats['simul_exec'][-1] += 1
                        _add_to_execute_list(node)
                elif (node.logical_id0 in mapping
                      and node.logical_id1 in mapping):
                    if self.graph.has_edge(mapping[node.logical_id0],
                                           mapping[node.logical_id1]):
                        has_command_to_execute = True
                        _add_to_execute_list(node)
                        self._stats['simul_exec'][-1] += 1
                        key = frozenset((mapping[node.logical_id0],
                                         mapping[node.logical_id1]))
                        self._stats['2qubit_gates_loc'][key] = self._stats.get(
                            node.logical_ids, 0) + 1
                        for cmd in node.compatible_successor_cmds:
                            if len([
                                    qubit.id for qureg in cmd.all_qubits
                                    for qubit in qureg
                            ]) == 2:
                                self._stats['2qubit_gates_loc'][key] += 1

        self.dag.calculate_command_hierarchy()
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
                self.dag.remove_command(node.cmd)

        self.dag.calculate_command_hierarchy()
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
        self.dag.calculate_command_hierarchy()
        return self.dag.calculate_qubit_interaction_subgraphs(max_order)

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

        self.dag.calculate_command_hierarchy()
        reverse_mapping = {v: k for k, v in mapping.items()}

        # Only consider gates from the front layer and generate a list of
        # potential SWAP operations with all qubits that are neighours of
        # those concerned by a gate

        swap_candidates = []
        for node in self.dag.front_layer_2qubit:
            for logical_id in node.logical_ids:
                for backend_id1 in self.graph[mapping[logical_id]]:
                    swap_candidates.append(
                        (logical_id, mapping[logical_id],
                         reverse_mapping.get(backend_id1, -1), backend_id1))

        # Rank swap candidates using the provided cost function
        scores = []
        for (logical_id0, backend_id0, logical_id1,
             backend_id1) in swap_candidates:
            new_mapping = mapping.copy()

            _apply_swap_to_mapping(new_mapping, logical_id0, logical_id1,
                                   backend_id1)

            scores.append(
                cost_fun(self.dag, new_mapping, self.distance_matrix,
                         (backend_id0, backend_id1), opts))

        # Return the swap candidate with the lowest score
        return swap_candidates[scores.index(min(scores))]

    def _can_execute_some_gate(self, mapping):
        """
        Test whether some gate from the front layer can be executed

        Args:
            mapping (dict): Current mapping
        """
        self.dag.calculate_command_hierarchy()
        for node in self.dag.front_layer:
            if isinstance(node, _DAGNodeSingle) and node.logical_id in mapping:
                return True

            if (isinstance(node, _DAGNodeDouble) and self.graph.has_edge(
                    mapping[node.logical_id0], mapping[node.logical_id1])):
                return True
        return False
