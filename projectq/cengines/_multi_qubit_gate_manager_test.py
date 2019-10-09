#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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
"""Tests for projectq.cengines._graphmapper.py."""

from copy import deepcopy

import pytest
import networkx as nx
# from projectq.cengines import DummyEngine, LocalOptimizer, MainEngine
# from projectq.meta import LogicalQubitIDTag
from projectq.ops import (Allocate, BasicGate, Command, Deallocate, FlushGate,
                          X, H, All, Measure, CNOT)
from projectq.types import WeakQubitRef

from projectq.cengines import _multi_qubit_gate_manager as multi


# For debugging purposes
def to_string(self):
    return str(tuple(self.logical_ids))


multi._dag_node.__str__ = to_string
multi._dag_node.__repr__ = to_string


def allocate_all_qubits_cmd(mapper):
    qb = []
    allocate_cmds = []
    for i in range(mapper.num_qubits):
        qb.append(WeakQubitRef(engine=None, idx=i))
        allocate_cmds.append(
            Command(engine=None, gate=Allocate, qubits=([qb[i]], )))
    return qb, allocate_cmds


def generate_grid_graph(nrows, ncols):
    graph = nx.Graph()
    graph.add_nodes_from(range(nrows * ncols))

    for row in range(nrows):
        for col in range(ncols):
            node0 = col + ncols * row

            is_middle = ((0 < row < nrows - 1) and (0 < col < ncols - 1))
            add_horizontal = is_middle or (row in (0, nrows - 1) and
                                           (0 < col < ncols - 1))
            add_vertical = is_middle or (col in (0, ncols - 1) and
                                         (0 < row < nrows - 1))
            if add_horizontal:
                graph.add_edge(node0, node0 - 1)
                graph.add_edge(node0, node0 + 1)
            if add_vertical:
                graph.add_edge(node0, node0 - ncols)
                graph.add_edge(node0, node0 + ncols)
            if nrows == 2:
                node0 = col
                graph.add_edge(node0, node0 + ncols)
        if ncols == 2:
            node0 = ncols * row
            graph.add_edge(node0, node0 + 1)

    return graph


@pytest.fixture(scope="module")
def simple_graph():
    #         2     4
    #       /  \  / |
    # 0 - 1     3   |
    #      \  /   \ |
    #       5       6
    graph = nx.Graph()
    graph.add_nodes_from(range(7))
    graph.add_edges_from([(0, 1), (1, 2), (1, 5), (2, 3), (5, 3), (3, 4),
                          (3, 6), (4, 6)])
    return graph


@pytest.fixture(scope="module")
def grid33_graph():
    return generate_grid_graph(3, 3)


@pytest.fixture
def decay_manager():
    return multi.DecayManager(0.001, 5)


@pytest.fixture
def gates_dag():
    return multi.GatesDAG()


@pytest.fixture
def qubit_manager():
    return multi.MultiQubitGateManager(generate_grid_graph(3, 3))


# ==============================================================================
# DecayManager
# ------------------------------------------------------------------------------


def test_decay_manager_add(decay_manager):
    delta = decay_manager._delta
    lifetime = decay_manager._cutoff

    decay_manager.add_to_decay(-1)
    assert not decay_manager._backend_ids

    decay_manager.add_to_decay(0)
    assert list(decay_manager._backend_ids) == [0]
    backend_qubit = decay_manager._backend_ids[0]
    assert backend_qubit.decay == delta
    assert backend_qubit.lifetime == lifetime

    decay_manager.add_to_decay(0)
    assert list(decay_manager._backend_ids) == [0]
    backend_qubit = decay_manager._backend_ids[0]
    assert backend_qubit.decay == 2 * delta
    assert backend_qubit.lifetime == lifetime

    decay_manager.add_to_decay(1)
    assert sorted(decay_manager._backend_ids) == [0, 1]
    backend_qubit = decay_manager._backend_ids[0]
    assert backend_qubit.decay == 2 * delta
    assert backend_qubit.lifetime == lifetime

    backend_qubit = decay_manager._backend_ids[1]
    assert backend_qubit.decay == delta
    assert backend_qubit.lifetime == lifetime


def test_decay_manager_remove(decay_manager):
    decay_manager.add_to_decay(0)
    decay_manager.add_to_decay(0)
    decay_manager.add_to_decay(1)
    assert sorted(list(decay_manager._backend_ids)) == [0, 1]

    decay_manager.remove_decay(0)
    assert list(decay_manager._backend_ids) == [1]
    decay_manager.remove_decay(1)
    assert not decay_manager._backend_ids


def test_decay_manager_get_decay_value(decay_manager):
    delta = decay_manager._delta

    decay_manager.add_to_decay(0)
    decay_manager.add_to_decay(0)
    decay_manager.add_to_decay(1)

    assert decay_manager.get_decay_value(0) == 2 * delta
    assert decay_manager.get_decay_value(1) == delta
    assert decay_manager.get_decay_value(-1) == 0
    assert decay_manager.get_decay_value(2) == 0


def test_decay_manager_step(decay_manager):
    delta = decay_manager._delta
    lifetime = decay_manager._cutoff

    decay_manager.add_to_decay(0)
    decay_manager.step()

    backend_qubit = decay_manager._backend_ids[0]
    assert backend_qubit.decay == delta
    assert backend_qubit.lifetime == lifetime - 1

    decay_manager.add_to_decay(0)
    decay_manager.add_to_decay(1)

    decay_manager.step()

    backend_qubit0 = decay_manager._backend_ids[0]
    backend_qubit1 = decay_manager._backend_ids[1]

    assert backend_qubit0.decay == 2 * delta
    assert backend_qubit0.lifetime == lifetime - 1
    assert backend_qubit1.decay == delta
    assert backend_qubit1.lifetime == lifetime - 1

    decay_manager.step()
    assert backend_qubit0.decay == 2 * delta
    assert backend_qubit0.lifetime == lifetime - 2
    assert backend_qubit1.decay == delta
    assert backend_qubit1.lifetime == lifetime - 2

    decay_manager.add_to_decay(1)
    assert backend_qubit1.lifetime == lifetime

    for i in range(3):
        decay_manager.step()

    # Qubit 0 decay information should be deleted by now
    assert list(decay_manager._backend_ids) == [1]

    for i in range(2):
        assert list(decay_manager._backend_ids) == [1]
        decay_manager.step()
    assert not decay_manager._backend_ids


# ==============================================================================
# GatesDAG
# ------------------------------------------------------------------------------


def test_gates_dag_init(gates_dag):
    assert gates_dag._dag.number_of_nodes() == 0
    assert gates_dag._dag.number_of_edges() == 0
    assert not gates_dag.front_layer
    assert not gates_dag.near_term_layer


def test_gates_dag_add_gate(gates_dag):
    dag_node01 = gates_dag.add_gate(0, 1)

    assert gates_dag._dag.number_of_nodes() == 1
    assert gates_dag._dag.number_of_edges() == 0
    assert gates_dag.front_layer
    assert not gates_dag.near_term_layer
    assert dag_node01.logical_id0 == 0
    assert dag_node01.logical_id1 == 1
    assert dag_node01.logical_ids == frozenset((0, 1))
    assert gates_dag.front_layer == [dag_node01]
    assert gates_dag._logical_ids_in_diag == {0, 1}
    assert gates_dag._back_layer == {0: dag_node01, 1: dag_node01}

    # ----------------------------------

    dag_node56 = gates_dag.add_gate(5, 6)

    assert gates_dag._dag.number_of_nodes() == 2
    assert gates_dag._dag.number_of_edges() == 0
    assert gates_dag.front_layer
    assert not gates_dag.near_term_layer

    assert dag_node01.logical_id0 == 0
    assert dag_node01.logical_id1 == 1
    assert dag_node01.logical_ids == frozenset((0, 1))
    assert dag_node56.logical_id0 == 5
    assert dag_node56.logical_id1 == 6
    assert dag_node56.logical_ids == frozenset((5, 6))

    assert gates_dag.front_layer == [dag_node01, dag_node56]
    assert gates_dag._logical_ids_in_diag == {0, 1, 5, 6}
    assert gates_dag._back_layer == {
        0: dag_node01,
        1: dag_node01,
        5: dag_node56,
        6: dag_node56
    }

    # ----------------------------------

    dag_node12 = gates_dag.add_gate(1, 2)
    assert gates_dag._dag.number_of_nodes() == 3
    assert gates_dag._dag.number_of_edges() == 1
    assert gates_dag.front_layer
    assert not gates_dag.near_term_layer

    assert dag_node01.logical_id0 == 0
    assert dag_node01.logical_id1 == 1
    assert dag_node01.logical_ids == frozenset((0, 1))
    assert dag_node12.logical_id0 == 1
    assert dag_node12.logical_id1 == 2
    assert dag_node12.logical_ids == frozenset((1, 2))
    assert dag_node56.logical_id0 == 5
    assert dag_node56.logical_id1 == 6
    assert dag_node56.logical_ids == frozenset((5, 6))

    assert gates_dag.front_layer == [dag_node01, dag_node56]
    assert gates_dag._logical_ids_in_diag == {0, 1, 2, 5, 6}
    assert gates_dag._back_layer == {
        0: dag_node01,
        1: dag_node12,
        2: dag_node12,
        5: dag_node56,
        6: dag_node56
    }

    # ----------------------------------

    dag_node26 = gates_dag.add_gate(2, 6)
    assert gates_dag.add_gate(2, 6) is None
    assert gates_dag._dag.number_of_nodes() == 4
    assert gates_dag._dag.number_of_edges() == 3
    assert gates_dag.front_layer
    assert not gates_dag.near_term_layer

    assert gates_dag.front_layer == [dag_node01, dag_node56]
    assert gates_dag._logical_ids_in_diag == {0, 1, 2, 5, 6}
    assert gates_dag._back_layer == {
        0: dag_node01,
        1: dag_node12,
        2: dag_node26,
        5: dag_node56,
        6: dag_node26
    }


def test_gates_dag_remove_from_front_layer(gates_dag):
    dag_node01 = gates_dag.add_gate(0, 1)
    dag_node56 = gates_dag.add_gate(5, 6)
    dag_node12 = gates_dag.add_gate(1, 2)
    dag_node26 = gates_dag.add_gate(2, 6)
    dag_node78 = gates_dag.add_gate(7, 8)

    with pytest.raises(RuntimeError):
        gates_dag.remove_from_front_layer(1, 2)

    assert gates_dag.front_layer == [dag_node01, dag_node56, dag_node78]

    gates_dag.remove_from_front_layer(7, 8)
    assert gates_dag.front_layer == [dag_node01, dag_node56]
    assert gates_dag._logical_ids_in_diag == {0, 1, 2, 5, 6}
    assert 7 not in gates_dag._back_layer
    assert 8 not in gates_dag._back_layer

    gates_dag.remove_from_front_layer(1, 0)
    assert gates_dag.front_layer == [dag_node56, dag_node12]

    gates_dag.remove_from_front_layer(5, 6)
    assert gates_dag.front_layer == [dag_node12]

    gates_dag.remove_from_front_layer(1, 2)
    assert gates_dag.front_layer == [dag_node26]


def test_gates_dag_max_distance(gates_dag):
    dag_node23a = gates_dag.add_gate(2, 3)
    dag_node56 = gates_dag.add_gate(5, 6)
    dag_node12 = gates_dag.add_gate(1, 2)
    dag_node34 = gates_dag.add_gate(3, 4)
    dag_node23b = gates_dag.add_gate(2, 3)
    dag_node46 = gates_dag.add_gate(4, 6)
    dag_node45 = gates_dag.add_gate(5, 4)
    dag_node14 = gates_dag.add_gate(4, 1)

    distance = gates_dag.max_distance_in_dag()
    assert distance[dag_node23a] == 0
    assert distance[dag_node56] == 0
    assert distance[dag_node12] == 1
    assert distance[dag_node34] == 1
    assert distance[dag_node23b] == 2
    assert distance[dag_node46] == 2
    assert distance[dag_node45] == 3
    assert distance[dag_node14] == 4


def test_gates_dag_near_term_layer(gates_dag):
    dag_node23a = gates_dag.add_gate(2, 3)
    dag_node56 = gates_dag.add_gate(5, 6)
    dag_node12 = gates_dag.add_gate(1, 2)
    dag_node34 = gates_dag.add_gate(3, 4)
    dag_node23b = gates_dag.add_gate(2, 3)
    dag_node46 = gates_dag.add_gate(4, 6)
    dag_node45 = gates_dag.add_gate(5, 4)
    dag_node14 = gates_dag.add_gate(4, 1)

    gates_dag.calculate_near_term_layer(0)
    assert not gates_dag.near_term_layer

    gates_dag.calculate_near_term_layer(1)
    assert {dag_node12, dag_node34} == gates_dag.near_term_layer

    gates_dag.calculate_near_term_layer(2)
    assert {dag_node12, dag_node34, dag_node23b,
            dag_node46} == gates_dag.near_term_layer


# ==============================================================================
# MultiQubitGateManager
# ------------------------------------------------------------------------------


def test_qubit_manager_valid_and_invalid_graphs(simple_graph):
    graph = nx.Graph()
    graph.add_nodes_from('abcd')
    with pytest.raises(RuntimeError):
        multi.MultiQubitGateManager(graph=graph)

    graph.add_edges_from([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')])
    with pytest.raises(RuntimeError):
        multi.MultiQubitGateManager(graph=graph)

    graph = deepcopy(simple_graph)
    graph.remove_edge(0, 1)
    with pytest.raises(RuntimeError):
        multi.MultiQubitGateManager(graph=graph)

    manager = multi.MultiQubitGateManager(graph=simple_graph)
    dist = manager.distance_matrix

    assert dist[0][1] == 1
    assert dist[0][2] == 2
    assert dist[0][3] == 3
    assert dist[0][4] == 4
    assert dist[0][5] == 2
    assert dist[0][6] == 4
    assert dist[1][0] == 1
    assert dist[1][2] == 1
    assert dist[1][3] == 2
    assert dist[1][4] == 3
    assert dist[1][5] == 1
    assert dist[1][6] == 3


def test_qubit_manager_push_interaction(qubit_manager):
    qubit_manager.push_interaction(0, 1)
    assert qubit_manager.stats[frozenset((0, 1))] == 1
    qubit_manager.push_interaction(0, 1)
    assert qubit_manager.stats[frozenset((0, 1))] == 2
    qubit_manager.push_interaction(5, 6)
    assert qubit_manager.stats[frozenset((0, 1))] == 2
    assert qubit_manager.stats[frozenset((5, 6))] == 1


def test_qubit_manager_can_execute_gate(qubit_manager):
    mapping = {i: i for i in range(9)}

    qubit_manager.push_interaction(5, 6)
    assert not qubit_manager._can_execute_some_gate(mapping)
    qubit_manager.push_interaction(0, 1)
    assert qubit_manager._can_execute_some_gate(mapping)


def test_qubit_manager_generatae_one_swap_step(qubit_manager):
    manager = deepcopy(qubit_manager)
    manager.push_interaction(0, 8)

    mapping = {i: i for i in range(9)}
    (logical_id0, logical_id1, backend_id1) = manager._generate_one_swap_step(
        mapping, multi.nearest_neighbours_cost_fun)

    assert logical_id0 in (0, 8)
    if logical_id0 == 0:
        assert backend_id1 in (1, 3)
    else:
        assert backend_id1 in (5, 7)

    mapping = {0: 0, 8: 8}
    (logical_id0, logical_id1, backend_id1) = manager._generate_one_swap_step(
        mapping, multi.nearest_neighbours_cost_fun)

    assert logical_id1 == -1
    if logical_id0 == 0:
        assert backend_id1 in (1, 3)
    else:
        assert backend_id1 in (5, 7)

    # ----------------------------------

    manager = deepcopy(qubit_manager)
    manager.push_interaction(0, 1)
    manager.push_interaction(0, 8)

    mapping = {i: i for i in range(9)}
    (logical_id0, logical_id1, backend_id1) = manager._generate_one_swap_step(
        mapping, multi.nearest_neighbours_cost_fun)

    # In this case, the only swap that does not increases the overall distance
    # is (0, 1)
    assert logical_id0 in (0, 1)
    assert backend_id1 in (0, 1)


def test_qubit_manager_generate_swaps(qubit_manager):
    manager = deepcopy(qubit_manager)
    mapping = {i: i for i in range(9)}

    swaps, all_qubits = manager.generate_swaps(
        mapping, multi.nearest_neighbours_cost_fun)

    assert not swaps
    assert not all_qubits

    # ----------------------------------

    manager.push_interaction(0, 8)

    with pytest.raises(RuntimeError):
        manager.generate_swaps(mapping,
                               multi.nearest_neighbours_cost_fun,
                               max_steps=2)

    # ----------------------------------

    mapping = {i: i for i in range(9)}
    swaps, _ = manager.generate_swaps(mapping,
                                      multi.nearest_neighbours_cost_fun)

    # Make sure the original mapping was not modified
    assert mapping == {i: i for i in range(9)}

    reverse_mapping = {v: k for k, v in mapping.items()}
    for id0, id1 in swaps:
        reverse_mapping[id0], reverse_mapping[id1] = (reverse_mapping[id1],
                                                      reverse_mapping[id0])

    mapping = {v: k for k, v in reverse_mapping.items()}
    assert manager.graph.has_edge(mapping[0], mapping[8])

    # ----------------------------------

    mapping = {i: i for i in range(9)}
    manager._use_near_term_layer = 1
    swaps, _ = manager.generate_swaps(mapping,
                                      multi.look_ahead_parallelism_cost_fun,
                                      opts={'W': 0.5})
    reverse_mapping = {v: k for k, v in mapping.items()}
    for id0, id1 in swaps:
        reverse_mapping[id0], reverse_mapping[id1] = (reverse_mapping[id1],
                                                      reverse_mapping[id0])

    mapping = {v: k for k, v in reverse_mapping.items()}
    assert manager.graph.has_edge(mapping[0], mapping[8])

    # ----------------------------------

    manager = deepcopy(qubit_manager)
    manager._use_near_term_layer = 1
    mapping = {0: 0, 1: 1, 8: 8}
    manager.push_interaction(0, 8)
    manager.push_interaction(0, 1)

    swaps, all_qubits = manager.generate_swaps(
        mapping,
        multi.look_ahead_parallelism_cost_fun,
        opts={
            'W': 0.5,
            'near_term_layer': 1
        })

    mapping = {i: i for i in range(9)}
    reverse_mapping = {v: k for k, v in mapping.items()}
    all_qubits_ref = set()
    for id0, id1 in swaps:
        all_qubits_ref.update((id0, id1))
        reverse_mapping[id0], reverse_mapping[id1] = (reverse_mapping[id1],
                                                      reverse_mapping[id0])

    mapping = {v: k for k, v in reverse_mapping.items()}

    assert all_qubits == all_qubits_ref

    # Both gates should be executable at the same time
    assert manager.graph.has_edge(mapping[0], mapping[8])
    assert manager.graph.has_edge(mapping[0], mapping[1])
