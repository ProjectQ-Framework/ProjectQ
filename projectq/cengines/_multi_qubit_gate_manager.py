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

# ==============================================================================


def _sum_distance_over_gates(gate_list, mapping, distance_matrix):
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
        distance_matrix[mapping[gate.logical_id0]][mapping[gate.logical_id1]]
        for gate in gate_list
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
        gates_dag (GatesDAG): Direct acyclic graph of future quantum gates
        mapping (dict): Current mapping
        distance_matrix (dict): Distance matrix within the hardware coupling
                                graph
        swap (tuple): Candidate swap (not used by this function)
        opts (dict): Miscellaneous parameters for cost function (not used by
                     this function)

    Returns:
        Score of current swap operations
    """
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
        gates_dag (GatesDAG): Direct acyclic graph of future quantum gates
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
    W = opts['W']
    N_front = len(gates_dag.front_layer)
    N_near = len(gates_dag.near_term_layer)

    front_layer_term = (1. / N_front * _sum_distance_over_gates(
        gates_dag.front_layer, mapping, distance_matrix))

    if N_near == 0:
        return (max(decay.get_decay_value(swap[0]),
                    decay.get_decay_value(swap[1])) * front_layer_term)
    return (
        max(decay.get_decay_value(swap[0]), decay.get_decay_value(swap[1])) *
        front_layer_term + (W / N_near * _sum_distance_over_gates(
            gates_dag.near_term_layer, mapping, distance_matrix)))


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


class QubitIDDecay(object):
    """
    Class storing the decay information about a particular backend qubit ID

    Attributes:
        decay (float): Decay value for a backend qubit ID
        lifetime (int): Lifetime of decay information for a backend qubit ID
    """
    def __init__(self, decay, lifetime):
        self.decay = decay
        self.lifetime = lifetime


class DecayManager(object):
    """
    Class managing the decay information about a list of backend qubit IDs

    User should call the :py:meth:`step` method each time a swap gate is added and
    :py:meth:`remove_decay` once a 2-qubit gate is executed.
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
            self._backend_ids[backend_id].lifetime = self._cutoff
            self._backend_ids[backend_id].decay += self._delta
        else:
            self._backend_ids[backend_id] = QubitIDDecay(
                self._delta, self._cutoff)

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
            return self._backend_ids[backend_id].decay
        return 0

    def step(self):
        """
        Step all decay values in time

        Use this method to indicate a SWAP search step has been performed.
        """
        backend_ids = list(self._backend_ids)
        for backend_id in backend_ids:
            self._backend_ids[backend_id].lifetime -= 1
            if self._backend_ids[backend_id].lifetime == 0:
                del self._backend_ids[backend_id]


# ==============================================================================


class _DAGNode(object):
    """
    Class representing a node inside a Direct Acyclic Graph (DAG)

    .. note::

    Main purpose of this class is to allow gates with identical qubits to be
    stored within the same graph (networkx limitation)
    """
    def __init__(self, logical_id0, logical_id1):
        self.logical_id0 = logical_id0
        self.logical_id1 = logical_id1
        self.logical_ids = frozenset((logical_id0, logical_id1))


class GatesDAG(object):
    """
    Class managing a list of multi-qubit gates and storing them into a Direct
    Acyclic Graph (DAG) in order of precedence.
    """
    def __init__(self):
        self._dag = nx.DiGraph()
        self._logical_ids_in_diag = set()
        self.front_layer = []
        self.near_term_layer = set()
        self._back_layer = {}

    def add_gate(self, logical_id0, logical_id1):
        """
        Add a gate to the DAG

        Args:
            logical_id0 (int) : A logical qubit ID
            logical_id1 (int) : A logical qubit ID

        .. note::
          If neither of ``logical_id0`` or ``logical_id1`` are currently found within the
          DAG, also add the gate to the font layer.
        """

        logical_id0_in_dag = logical_id0 in self._logical_ids_in_diag
        logical_id1_in_dag = logical_id1 in self._logical_ids_in_diag

        if not (logical_id0_in_dag and logical_id1_in_dag and self.
                _back_layer[logical_id0] == self._back_layer[logical_id1]):
            # Do not add the new gate to DAG if both qubits are present inside
            # the DAG *and* the gate on the last layer is the same for both
            # qubits.
            new_gate = _DAGNode(logical_id0, logical_id1)

            self._dag.add_node(new_gate)

            if logical_id0_in_dag:
                self._dag.add_edge(self._back_layer[logical_id0], new_gate)
                self._logical_ids_in_diag.add(logical_id1)
            else:
                self._logical_ids_in_diag.add(logical_id0)

            if logical_id1_in_dag:
                self._dag.add_edge(self._back_layer[logical_id1], new_gate)
                self._logical_ids_in_diag.add(logical_id0)
            else:
                self._logical_ids_in_diag.add(logical_id1)

            self._back_layer[logical_id0] = new_gate
            self._back_layer[logical_id1] = new_gate

            # If both qubit are not already in the DAG, then we just got a new
            # gate on the front layer
            if not logical_id0_in_dag and not logical_id1_in_dag:
                self.front_layer.append(new_gate)
            return new_gate
        return None

    def remove_from_front_layer(self, logical_id0, logical_id1):
        """
        Remove a gate from the front layer of the DAG

        Args:
            logical_id0 (int) : A logical qubit ID
            logical_id1 (int) : A logical qubit ID

        Raises:
            RuntimeError if the gate does not exist in the front layer
        """
        # First find the gate inside the first layer list
        for gate in self.front_layer:
            if gate.logical_ids == frozenset((logical_id0, logical_id1)):
                break
        else:
            raise RuntimeError('({}, {}) not found in DAG'.format(
                logical_id0, logical_id1))

        descendants = list(self._dag[gate])

        if not descendants:
            self._logical_ids_in_diag.remove(logical_id0)
            self._logical_ids_in_diag.remove(logical_id1)
            del self._back_layer[logical_id0]
            del self._back_layer[logical_id1]
            self._dag.remove_node(gate)
        else:
            if len(descendants) == 1:
                # Look for the logical_id not found in the descendant
                logical_id = logical_id0
                if logical_id in descendants[0].logical_ids:
                    logical_id = logical_id1

                self._logical_ids_in_diag.remove(logical_id)
                del self._back_layer[logical_id]

            # Remove gate from DAG
            self._dag.remove_node(gate)

            for descendant in descendants:
                if not self._dag.pred[descendant]:
                    self.front_layer.append(descendant)

        # Remove the gate from the first layer
        self.front_layer.remove(gate)

    def max_distance_in_dag(self):
        """
        Calculate the distance between the front layer and each gate of the
        DAG.

        A gate with distance 0 is on the front layer.

        Returns:
            Python dictionary indexed by gate with their distance as value
        """
        gate_max_distance = {}
        for gate in self.front_layer:
            gate_max_distance[gate] = 0
            self._max_distance_in_dag(gate_max_distance, gate, 1)

        return gate_max_distance

    def calculate_near_term_layer(self, max_distance):
        """
        Calculate a near term layer with all gates less than `max_distance`
        from the front layer

        Args:
            max_distance (int): Maximum distance from front layer to consider
        """
        if not max_distance:
            self.near_term_layer = set()
        else:
            self.near_term_layer = {
                gate
                for gate, dist in self.max_distance_in_dag().items()
                if 0 < dist <= max_distance
            }

    def _max_distance_in_dag(self, gate_max_distance, gate, distance):
        """
        Recursively calculate the maximum distance for each gate of the DAG

        Args:
            gate_max_depth (dict): Dictionary containing the current maximum
                                   distance for each gate
            gate (_DAGNode): Root node from DAG for traversal
            distance (int): Current distance offset
        """
        for descendant in self._dag[gate]:
            try:
                if gate_max_distance[descendant] < distance:
                    gate_max_distance[descendant] = distance
            except KeyError:
                gate_max_distance[descendant] = distance

            if self._dag[descendant]:
                self._max_distance_in_dag(gate_max_distance, descendant,
                                          distance + 1)


class MultiQubitGateManager(object):
    """
    Class managing qubit interactions
    """
    def __init__(self, graph, decay_opts={}):
        """
        Args:
            graph (networkx.Graph): an arbitrary connected graph
        """
        # Make sure that we start with a valid graph
        if not nx.is_connected(graph):
            raise RuntimeError("Input graph must be a connected graph")
        elif not all([isinstance(n, int) for n in graph]):
            raise RuntimeError(
                "All nodes inside the graph needs to be integers")
        else:
            self.graph = graph
            self.distance_matrix = dict(
                nx.all_pairs_shortest_path_length(self.graph))

        self._dag = GatesDAG()
        self._decay = DecayManager(decay_opts.get('delta', 0.001),
                                   decay_opts.get('lifetime', 5))
        self.stats = {}

    def generate_swaps(self, current_mapping, cost_fun, opts={},
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

        if not self._dag.front_layer:
            return ([], set())

        opts['decay'] = self._decay

        self._dag.calculate_near_term_layer(opts.get('near_term_layer', 0))

        mapping = current_mapping.copy()
        swaps = []
        all_swapped_qubits = set()
        while not self._can_execute_some_gate(mapping):
            (logical_id0, logical_id1,
             backend_id1) = self._generate_one_swap_step(
                 mapping, cost_fun, opts)
            swaps.append((mapping[logical_id0], backend_id1))
            all_swapped_qubits.add(mapping[logical_id0])
            all_swapped_qubits.add(backend_id1)

            for backend_id in swaps[-1]:
                self._decay.add_to_decay(backend_id)
            self._decay.step()

            _apply_swap_to_mapping(mapping, logical_id0, logical_id1,
                                   backend_id1)

            if len(swaps) > max_steps:
                raise RuntimeError(
                    'Maximum number of steps to find a list of' +
                    ' SWAP operations reached without convergence')

        return swaps, all_swapped_qubits

    def push_interaction(self, logical_id0, logical_id1):
        """
        Plan an interaction between two qubit.

        Args:
            logical_id0 (int) : A logical qubit ID
            logical_id1 (int) : A logical qubit ID
        """

        self._dag.add_gate(logical_id0, logical_id1)

        new_gate = frozenset((logical_id0, logical_id1))
        if new_gate not in self.stats:
            self.stats[new_gate] = 1
        else:
            self.stats[new_gate] += 1

    def execute_gate(
            self,
            mapping,
            logical_id0,
            logical_id1,
    ):
        """
        Execute a gate (ie. mark it as executed if present in the DAG)

        Args:
            mapping (dict): Current mapping
            logical_id0 (int) : A logical qubit ID
            logical_id1 (int) : A logical qubit ID
        """
        if self.graph.has_edge(mapping[logical_id0], mapping[logical_id1]):
            for gate in self._dag.front_layer:
                if (logical_id0 in gate.logical_ids
                        and logical_id1 in gate.logical_ids):
                    self._dag.remove_from_front_layer(logical_id0, logical_id1)
            return True
        return False

    # ==========================================================================

    def _generate_one_swap_step(self, mapping, cost_fun, opts={}):
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
            Tuple with (logical_id0, logical_id1, backend_id1) where
            logical_id1 can be -1 if backend_id1 does not currently have a
            logical qubit associated to it.
        """

        reverse_mapping = {v: k for k, v in mapping.items()}

        # Only consider gates from the front layer and generate a list of
        # potential SWAP operations with all qubits that are neighours of
        # those concerned by a gate
        swap_candidates = []
        for gate in self._dag.front_layer:
            for logical_id in gate.logical_ids:
                for backend_id in self.graph[mapping[logical_id]]:
                    swap_candidates.append(
                        (logical_id, reverse_mapping.get(backend_id,
                                                         -1), backend_id))

        # Rank swap candidates using the provided cost function
        scores = []
        for logical_id0, logical_id1, backend_id1 in swap_candidates:
            new_mapping = mapping.copy()

            _apply_swap_to_mapping(new_mapping, logical_id0, logical_id1,
                                   backend_id1)

            scores.append(
                cost_fun(self._dag, new_mapping, self.distance_matrix,
                         (logical_id0, logical_id1), opts))

        # Return the swap candidate with the lowest score
        return swap_candidates[scores.index(min(scores))]

    def _can_execute_some_gate(self, mapping):
        """
        Test whether some gate from the front layer can be executed

        Args:
            mapping (dict): Current mapping
        """
        for gate in self._dag.front_layer:
            if self.graph.has_edge(mapping[gate.logical_id0],
                                   mapping[gate.logical_id1]):
                return True
        return False
