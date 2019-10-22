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
import re
from projectq.ops import (Allocate, Command, Deallocate, X, H)
from projectq.types import WeakQubitRef

from projectq.cengines import _gate_manager as gatemgr

# ==============================================================================


# For debugging purposes
def dagnode_to_string(self):
    return '{} {}'.format(self.__class__.__name__, tuple(self.logical_ids))


gatemgr._DAGNodeBase.__str__ = dagnode_to_string
gatemgr._DAGNodeBase.__repr__ = dagnode_to_string

Command.__repr__ = Command.__str__

# ==============================================================================


def allocate_all_qubits_cmd(num_qubits):
    qb = []
    allocate_cmds = []
    for i in range(num_qubits):
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


def gen_cmd(*logical_ids, gate=X):
    if len(logical_ids) == 1:
        qb0 = WeakQubitRef(engine=None, idx=logical_ids[0])
        return Command(None, gate, qubits=([qb0], ))
    elif len(logical_ids) == 2:
        qb0 = WeakQubitRef(engine=None, idx=logical_ids[0])
        qb1 = WeakQubitRef(engine=None, idx=logical_ids[1])
        return Command(None, gate, qubits=([qb0], ), controls=[qb1])
    else:
        raise RuntimeError('Unsupported')


def search_cmd(command_dag, cmd):
    for node in command_dag._dag:
        if node.cmd is cmd:
            return node
    raise RuntimeError('Unable to find command in DAG')


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
    return gatemgr.DecayManager(0.001, 5)


@pytest.fixture
def command_dag():
    return gatemgr.CommandDAG()


@pytest.fixture
def qubit_manager():
    return gatemgr.GateManager(generate_grid_graph(3, 3))


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
    assert backend_qubit['decay'] == pytest.approx(1 + delta)
    assert backend_qubit['lifetime'] == lifetime

    decay_manager.add_to_decay(0)
    assert list(decay_manager._backend_ids) == [0]
    backend_qubit = decay_manager._backend_ids[0]
    assert backend_qubit['decay'] == pytest.approx(1 + 2 * delta)
    assert backend_qubit['lifetime'] == lifetime

    decay_manager.add_to_decay(1)
    assert sorted(decay_manager._backend_ids) == [0, 1]
    backend_qubit = decay_manager._backend_ids[0]
    assert backend_qubit['decay'] == pytest.approx(1 + 2 * delta)
    assert backend_qubit['lifetime'] == lifetime

    backend_qubit = decay_manager._backend_ids[1]
    assert backend_qubit['decay'] == pytest.approx(1 + delta)
    assert backend_qubit['lifetime'] == lifetime


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

    assert decay_manager.get_decay_value(0) == pytest.approx(1 + 2 * delta)
    assert decay_manager.get_decay_value(1) == pytest.approx(1 + delta)
    assert decay_manager.get_decay_value(-1) == 1
    assert decay_manager.get_decay_value(2) == 1


def test_decay_manager_step(decay_manager):
    delta = decay_manager._delta
    lifetime = decay_manager._cutoff

    decay_manager.add_to_decay(0)
    decay_manager.step()

    backend_qubit = decay_manager._backend_ids[0]
    assert backend_qubit['decay'] == pytest.approx(1 + delta)
    assert backend_qubit['lifetime'] == lifetime - 1

    decay_manager.add_to_decay(0)
    decay_manager.add_to_decay(1)

    decay_manager.step()

    backend_qubit0 = decay_manager._backend_ids[0]
    backend_qubit1 = decay_manager._backend_ids[1]

    assert backend_qubit0['decay'] == pytest.approx(1 + 2 * delta)
    assert backend_qubit0['lifetime'] == lifetime - 1
    assert backend_qubit1['decay'] == pytest.approx(1 + delta)
    assert backend_qubit1['lifetime'] == lifetime - 1

    decay_manager.step()
    assert backend_qubit0['decay'] == pytest.approx(1 + 2 * delta)
    assert backend_qubit0['lifetime'] == lifetime - 2
    assert backend_qubit1['decay'] == pytest.approx(1 + delta)
    assert backend_qubit1['lifetime'] == lifetime - 2

    decay_manager.add_to_decay(1)
    assert backend_qubit1['decay'] == pytest.approx(1 + 2 * delta)
    assert backend_qubit1['lifetime'] == lifetime

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


def test_command_dag_init(command_dag):
    assert command_dag._dag.number_of_nodes() == 0
    assert command_dag._dag.number_of_edges() == 0
    assert not command_dag.front_layer
    assert not command_dag.near_term_layer


def test_command_dag_add_1qubit_gate(command_dag):
    cmd0a = gen_cmd(0)
    cmd0b = gen_cmd(0)
    cmd1 = gen_cmd(1)
    # ----------------------------------

    command_dag.add_command(cmd0a)
    command_dag.add_command(cmd1)
    command_dag.add_command(cmd0b)
    dag_node0a = search_cmd(command_dag, cmd0a)
    dag_node1 = search_cmd(command_dag, cmd1)

    with pytest.raises(RuntimeError):
        search_cmd(command_dag, cmd0b)

    assert command_dag._dag.number_of_nodes() == 2
    assert command_dag._dag.number_of_edges() == 0
    assert command_dag.front_layer
    assert not command_dag.near_term_layer
    assert dag_node0a.logical_ids == frozenset((0, ))
    assert command_dag.front_layer == [dag_node0a, dag_node1]
    assert command_dag._logical_ids_in_diag == {0, 1}
    assert command_dag._back_layer == {0: dag_node0a, 1: dag_node1}


def test_command_dag_add_1qubit_gate_allocate(command_dag):

    allocate2 = gen_cmd(2, gate=Allocate)
    cmd2a = gen_cmd(2)
    cmd2b = gen_cmd(2)
    deallocate2 = gen_cmd(2, gate=Allocate)

    # ----------------------------------

    command_dag.add_command(allocate2)
    command_dag.add_command(cmd2a)
    command_dag.add_command(cmd2b)
    command_dag.add_command(deallocate2)
    dag_allocate = search_cmd(command_dag, allocate2)
    dag_deallocate = search_cmd(command_dag, deallocate2)
    with pytest.raises(RuntimeError):
        search_cmd(command_dag, cmd2a)
    with pytest.raises(RuntimeError):
        search_cmd(command_dag, cmd2b)

    assert command_dag._dag.number_of_nodes() == 2
    assert command_dag._dag.number_of_edges() == 1
    assert command_dag.front_layer == [dag_allocate]
    assert not command_dag.near_term_layer
    assert dag_allocate.logical_ids == frozenset((2, ))
    assert dag_deallocate.logical_ids == frozenset((2, ))
    assert command_dag._logical_ids_in_diag == {2}
    assert command_dag._back_layer == {2: dag_deallocate}


def test_command_dag_add_2qubit_gate(command_dag):
    cmd01 = gen_cmd(0, 1)
    cmd56 = gen_cmd(5, 6)
    cmd12 = gen_cmd(1, 2)
    cmd12b = gen_cmd(1, 2)
    cmd26 = gen_cmd(2, 6)

    # ----------------------------------

    command_dag.add_command(cmd01)
    dag_node01 = search_cmd(command_dag, cmd01)

    assert command_dag._dag.number_of_nodes() == 1
    assert command_dag._dag.number_of_edges() == 0
    assert command_dag.front_layer
    assert not command_dag.near_term_layer
    assert dag_node01.logical_ids == frozenset((0, 1))
    assert command_dag.front_layer == [dag_node01]
    assert command_dag._logical_ids_in_diag == {0, 1}
    assert command_dag._back_layer == {0: dag_node01, 1: dag_node01}

    # ----------------------------------

    command_dag.add_command(cmd56)
    dag_node56 = search_cmd(command_dag, cmd56)

    assert command_dag._dag.number_of_nodes() == 2
    assert command_dag._dag.number_of_edges() == 0
    assert command_dag.front_layer
    assert not command_dag.near_term_layer

    assert dag_node01.logical_ids == frozenset((0, 1))
    assert dag_node56.logical_ids == frozenset((5, 6))

    assert command_dag.front_layer == [dag_node01, dag_node56]
    assert command_dag._logical_ids_in_diag == {0, 1, 5, 6}
    assert command_dag._back_layer == {
        0: dag_node01,
        1: dag_node01,
        5: dag_node56,
        6: dag_node56
    }

    # ----------------------------------

    command_dag.add_command(cmd12)
    command_dag.add_command(cmd12b)
    dag_node12 = search_cmd(command_dag, cmd12)
    with pytest.raises(RuntimeError):
        search_cmd(command_dag, cmd12b)

    assert command_dag._dag.number_of_nodes() == 3
    assert command_dag._dag.number_of_edges() == 1
    assert command_dag.front_layer
    assert not command_dag.near_term_layer

    assert dag_node01.logical_ids == frozenset((0, 1))
    assert dag_node12.logical_ids == frozenset((1, 2))
    assert dag_node56.logical_ids == frozenset((5, 6))

    assert command_dag.front_layer == [dag_node01, dag_node56]
    assert command_dag._logical_ids_in_diag == {0, 1, 2, 5, 6}
    assert command_dag._back_layer == {
        0: dag_node01,
        1: dag_node12,
        2: dag_node12,
        5: dag_node56,
        6: dag_node56
    }

    # ----------------------------------

    command_dag.add_command(cmd26)
    dag_node26 = search_cmd(command_dag, cmd26)
    assert command_dag._dag.number_of_nodes() == 4
    assert command_dag._dag.number_of_edges() == 3
    assert command_dag.front_layer
    assert not command_dag.near_term_layer

    assert command_dag.front_layer == [dag_node01, dag_node56]
    assert command_dag._logical_ids_in_diag == {0, 1, 2, 5, 6}
    assert command_dag._back_layer == {
        0: dag_node01,
        1: dag_node12,
        2: dag_node26,
        5: dag_node56,
        6: dag_node26
    }


def test_command_dag_add_gate(command_dag):
    cmd0 = gen_cmd(0)
    cmd01 = gen_cmd(0, 1)
    cmd56 = gen_cmd(5, 6)
    cmd7 = gen_cmd(7)

    # ----------------------------------

    command_dag.add_command(cmd0)
    command_dag.add_command(cmd01)
    dag_node0 = search_cmd(command_dag, cmd0)

    assert len(command_dag.front_layer) == 1
    assert not command_dag.front_layer_2qubit

    assert command_dag._dag.number_of_nodes() == 2
    assert command_dag._dag.number_of_edges() == 1
    assert command_dag.front_layer == [dag_node0]
    assert not command_dag.near_term_layer

    command_dag.add_command(cmd56)
    command_dag.add_command(cmd7)
    dag_node56 = search_cmd(command_dag, cmd56)

    assert len(command_dag.front_layer) == 3
    assert command_dag.front_layer_2qubit == [dag_node56]


def test_command_dag_remove_command(command_dag):
    allocate0 = gen_cmd(0, gate=Allocate)
    cmd0 = gen_cmd(0)
    deallocate0 = gen_cmd(0, gate=Deallocate)

    # ----------------------------------

    command_dag.add_command(allocate0)
    command_dag.add_command(cmd0)
    command_dag.add_command(deallocate0)
    dag_allocate0 = search_cmd(command_dag, allocate0)
    dag_deallocate = search_cmd(command_dag, deallocate0)

    with pytest.raises(RuntimeError):
        search_cmd(command_dag, cmd0)

    with pytest.raises(RuntimeError):
        command_dag.remove_command(cmd0)

    assert command_dag.front_layer == [dag_allocate0]

    command_dag.remove_command(allocate0)
    assert command_dag.front_layer == [dag_deallocate]
    assert command_dag._logical_ids_in_diag == {0}

    command_dag.remove_command(deallocate0)
    assert not command_dag.front_layer


def test_command_dag_remove_command2(command_dag):
    cmd01 = gen_cmd(0, 1)
    cmd56 = gen_cmd(5, 6)
    cmd12 = gen_cmd(1, 2)
    cmd26 = gen_cmd(2, 6)
    cmd78 = gen_cmd(7, 8)

    # ----------------------------------

    command_dag.add_command(cmd01)
    command_dag.add_command(cmd56)
    command_dag.add_command(cmd12)
    command_dag.add_command(cmd26)
    command_dag.add_command(cmd78)
    dag_node01 = search_cmd(command_dag, cmd01)
    dag_node56 = search_cmd(command_dag, cmd56)
    dag_node12 = search_cmd(command_dag, cmd12)
    dag_node26 = search_cmd(command_dag, cmd26)
    dag_node78 = search_cmd(command_dag, cmd78)

    with pytest.raises(RuntimeError):
        command_dag.remove_command(cmd12)

    assert command_dag.front_layer == [dag_node01, dag_node56, dag_node78]

    command_dag.remove_command(cmd78)
    assert command_dag.front_layer == [dag_node01, dag_node56]
    assert command_dag._logical_ids_in_diag == {0, 1, 2, 5, 6}
    assert 7 not in command_dag._back_layer
    assert 8 not in command_dag._back_layer

    command_dag.remove_command(cmd01)
    assert command_dag.front_layer == [dag_node56, dag_node12]

    command_dag.remove_command(cmd56)
    assert command_dag.front_layer == [dag_node12]

    command_dag.remove_command(cmd12)
    assert command_dag.front_layer == [dag_node26]


def test_command_dag_near_term_layer(command_dag):
    cmd23a = gen_cmd(2, 3)
    cmd56 = gen_cmd(5, 6)
    cmd12 = gen_cmd(1, 2)
    cmd34 = gen_cmd(3, 4)
    cmd23b = gen_cmd(2, 3)
    cmd46 = gen_cmd(4, 6)
    cmd45 = gen_cmd(5, 4)
    cmd14 = gen_cmd(4, 1)
    command_dag.add_command(cmd23a)
    command_dag.add_command(cmd56)
    command_dag.add_command(cmd12)
    command_dag.add_command(cmd34)
    command_dag.add_command(cmd23b)
    command_dag.add_command(cmd46)
    command_dag.add_command(cmd45)
    command_dag.add_command(cmd14)
    dag_node12 = search_cmd(command_dag, cmd12)
    dag_node34 = search_cmd(command_dag, cmd34)

    command_dag.calculate_near_term_layer({i: i for i in range(7)})
    assert command_dag.near_term_layer == [dag_node12, dag_node34]


def test_command_dag_calculate_interaction_list(command_dag):
    cmd01 = gen_cmd(0, 1)
    cmd03 = gen_cmd(0, 3)
    cmd34 = gen_cmd(3, 4)
    cmd7 = gen_cmd(7, gate=Allocate)
    cmd8 = gen_cmd(8)

    command_dag.add_command(cmd01)
    command_dag.add_command(cmd34)
    command_dag.add_command(cmd03)
    command_dag.add_command(cmd8)
    command_dag.add_command(cmd7)

    interactions = command_dag.calculate_interaction_list()

    assert (0, 1) in interactions or (1, 0) in interactions
    assert (0, 3) in interactions or (3, 0) in interactions
    assert (3, 4) in interactions or (4, 3) in interactions


def test_command_dag_generate_qubit_interaction_graph(command_dag):

    qb, allocate_cmds = allocate_all_qubits_cmd(9)
    cmd0 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]])
    cmd1 = Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]])
    cmd2 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]])
    cmd3 = Command(engine=None, gate=X, qubits=([qb[1]], ))

    command_dag.add_command(cmd0)
    command_dag.add_command(cmd1)
    command_dag.add_command(cmd2)
    command_dag.add_command(cmd3)

    subgraphs = command_dag.calculate_qubit_interaction_subgraphs(max_order=2)
    assert len(subgraphs) == 1
    assert len(subgraphs[0]) == 4
    assert all([n in subgraphs[0] for n in [0, 1, 2, 3]])
    assert subgraphs[0][-2:] in ([1, 3], [3, 1])

    # --------------------------------------------------------------------------

    cmd4 = Command(engine=None, gate=X, qubits=([qb[4]], ), controls=[qb[5]])
    cmd5 = Command(engine=None, gate=X, qubits=([qb[5]], ), controls=[qb[6]])
    command_dag.add_command(cmd4)
    command_dag.add_command(cmd5)

    subgraphs = command_dag.calculate_qubit_interaction_subgraphs(max_order=2)
    assert len(subgraphs) == 2
    assert len(subgraphs[0]) == 4

    assert all([n in subgraphs[0] for n in [0, 1, 2, 3]])
    assert subgraphs[0][-2:] in ([1, 3], [3, 1])
    assert subgraphs[1] in ([5, 4, 6], [5, 6, 4])

    # --------------------------------------------------------------------------

    cmd6 = Command(engine=None, gate=X, qubits=([qb[6]], ), controls=[qb[7]])
    cmd7 = Command(engine=None, gate=X, qubits=([qb[7]], ), controls=[qb[8]])
    command_dag.add_command(cmd6)
    command_dag.add_command(cmd7)

    subgraphs = command_dag.calculate_qubit_interaction_subgraphs(max_order=2)

    assert len(subgraphs) == 2
    assert len(subgraphs[0]) == 5
    assert all([n in subgraphs[0] for n in [4, 5, 6, 7, 8]])
    assert subgraphs[0][-2:] in ([4, 8], [8, 4])
    assert len(subgraphs[1]) == 4
    assert all([n in subgraphs[1] for n in [0, 1, 2, 3]])
    assert subgraphs[1][-2:] in ([1, 3], [3, 1])

    # --------------------------------------------------------------------------

    command_dag.add_command(
        Command(engine=None, gate=X, qubits=([qb[3]], ), controls=[qb[0]]))
    subgraphs = command_dag.calculate_qubit_interaction_subgraphs(max_order=3)

    assert len(subgraphs) == 2
    assert len(subgraphs[0]) == 4
    assert all([n in subgraphs[0] for n in [0, 1, 2, 3]])
    assert subgraphs[0][0] == 0
    assert subgraphs[0][-2:] in ([1, 3], [3, 1])
    assert len(subgraphs[1]) == 5
    assert all([n in subgraphs[1] for n in [4, 5, 6, 7, 8]])
    assert subgraphs[1][-2:] in ([4, 8], [8, 4])


# ==============================================================================
# MultiQubitGateManager
# ------------------------------------------------------------------------------


def test_qubit_manager_valid_and_invalid_graphs(simple_graph):
    graph = nx.Graph()
    graph.add_nodes_from('abcd')
    with pytest.raises(RuntimeError):
        gatemgr.GateManager(graph=graph)

    graph.add_edges_from([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')])
    with pytest.raises(RuntimeError):
        gatemgr.GateManager(graph=graph)

    graph = deepcopy(simple_graph)
    graph.remove_edge(0, 1)
    with pytest.raises(RuntimeError):
        gatemgr.GateManager(graph=graph)

    manager = gatemgr.GateManager(graph=simple_graph)
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


def test_qubit_manager_can_execute_gate(qubit_manager):
    cmd0 = gen_cmd(0)
    cmd01 = gen_cmd(0, 1)
    cmd38 = gen_cmd(3, 8)

    mapping = {i: i for i in range(9)}

    manager = deepcopy(qubit_manager)
    manager.add_command(cmd38)
    assert not manager._can_execute_some_gate(mapping)
    manager.add_command(cmd0)
    assert manager._can_execute_some_gate(mapping)

    manager = deepcopy(qubit_manager)
    manager.add_command(cmd38)
    assert not manager._can_execute_some_gate(mapping)
    manager.add_command(cmd01)
    assert manager._can_execute_some_gate(mapping)


def test_qubit_manager_clear(qubit_manager):
    cmd0 = gen_cmd(0)
    cmd01 = gen_cmd(0, 1)
    cmd38 = gen_cmd(3, 8)

    qubit_manager.add_command(cmd38)
    qubit_manager.add_command(cmd0)
    qubit_manager.add_command(cmd38)
    qubit_manager.add_command(cmd01)

    qubit_manager._decay.add_to_decay(0)

    assert qubit_manager._decay._backend_ids
    assert qubit_manager.dag._dag
    qubit_manager.clear()
    assert not qubit_manager._decay._backend_ids
    assert not qubit_manager.dag._dag


def test_qubit_manager_generate_one_swap_step(qubit_manager):
    cmd08 = gen_cmd(0, 8)
    cmd01 = gen_cmd(0, 1)
    cmd5 = gen_cmd(5)

    # ----------------------------------

    manager = deepcopy(qubit_manager)
    manager.add_command(cmd08)
    manager.add_command(cmd5)

    mapping = {i: i for i in range(9)}
    (logical_id0, backend_id0, logical_id1,
     backend_id1) = manager._generate_one_swap_step(
         mapping, gatemgr.nearest_neighbours_cost_fun, {})

    assert logical_id0 in (0, 8)
    if logical_id0 == 0:
        assert backend_id1 in (1, 3)
    else:
        assert backend_id1 in (5, 7)

    mapping = {0: 0, 8: 8}
    (logical_id0, backend_id0, logical_id1,
     backend_id1) = manager._generate_one_swap_step(
         mapping, gatemgr.nearest_neighbours_cost_fun, {})

    assert logical_id1 == -1
    if logical_id0 == 0:
        assert backend_id1 in (1, 3)
    else:
        assert backend_id1 in (5, 7)

    # ----------------------------------

    manager = deepcopy(qubit_manager)
    manager.add_command(cmd01)
    manager.add_command(cmd08)

    mapping = {i: i for i in range(9)}
    (logical_id0, backend_id0, logical_id1,
     backend_id1) = manager._generate_one_swap_step(
         mapping, gatemgr.nearest_neighbours_cost_fun, {})

    # In this case, the only swap that does not increases the overall distance
    # is (0, 1)
    assert logical_id0 in (0, 1)
    assert backend_id1 in (0, 1)


def test_qubit_manager_generate_swaps(qubit_manager):
    cmd08 = gen_cmd(0, 8)
    cmd01 = gen_cmd(0, 1)

    # ----------------------------------

    manager = deepcopy(qubit_manager)
    mapping = {i: i for i in range(9)}

    swaps, all_qubits = manager.generate_swaps(
        mapping, gatemgr.nearest_neighbours_cost_fun)

    assert not swaps
    assert not all_qubits

    # ----------------------------------

    manager.add_command(cmd08)
    assert manager.size() == 1

    with pytest.raises(RuntimeError):
        manager.generate_swaps(mapping,
                               gatemgr.nearest_neighbours_cost_fun,
                               max_steps=2)

    # ----------------------------------

    mapping = {i: i for i in range(9)}
    swaps, _ = manager.generate_swaps(mapping,
                                      gatemgr.nearest_neighbours_cost_fun)

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
    swaps, _ = manager.generate_swaps(mapping,
                                      gatemgr.look_ahead_parallelism_cost_fun,
                                      opts={'W': 0.5})
    reverse_mapping = {v: k for k, v in mapping.items()}
    for id0, id1 in swaps:
        reverse_mapping[id0], reverse_mapping[id1] = (reverse_mapping[id1],
                                                      reverse_mapping[id0])

    mapping = {v: k for k, v in reverse_mapping.items()}
    assert manager.graph.has_edge(mapping[0], mapping[8])

    # ----------------------------------

    manager = deepcopy(qubit_manager)
    mapping = {0: 0, 1: 1, 8: 8}
    manager.add_command(cmd08)
    manager.add_command(cmd01)
    assert manager.size() == 2

    swaps, all_qubits = manager.generate_swaps(
        mapping, gatemgr.look_ahead_parallelism_cost_fun, opts={
            'W': 0.5,
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


def test_qubit_manager_get_executable_commands(qubit_manager):
    cmd0 = gen_cmd(0)
    cmd01 = gen_cmd(0, 1)
    cmd03 = gen_cmd(0, 3)
    cmd34 = gen_cmd(3, 4)
    cmd7 = gen_cmd(7, gate=Allocate)
    cmd8a = gen_cmd(8, gate=Allocate)
    cmd8b = gen_cmd(8)

    manager = deepcopy(qubit_manager)
    mapping = {0: 0, 1: 1, 3: 3, 4: 4, 8: 8}
    manager.add_command(cmd0)
    manager.add_command(cmd01)
    manager.add_command(cmd34)
    manager.add_command(cmd03)
    manager.add_command(cmd8a)
    manager.add_command(cmd8b)
    manager.add_command(cmd7)

    dag_allocate7 = search_cmd(manager.dag, cmd7)

    assert manager.size() == 6

    cmds_to_execute, allocate_cmds = manager.get_executable_commands(mapping)

    assert cmds_to_execute == [cmd0, cmd34, cmd8a, cmd8b, cmd01, cmd03]
    assert allocate_cmds == [dag_allocate7]
    assert manager.size() == 1

    mapping.update({7: 7})
    cmds_to_execute = manager.execute_allocate_cmds(allocate_cmds, mapping)

    assert cmds_to_execute == [cmd7]
    assert manager.size() == 0

    mapping = {0: 0, 1: 1, 3: 3, 4: 4, 8: 8}
    manager.add_command(cmd01)
    manager.add_command(cmd03)
    manager.add_command(cmd34)
    manager.add_command(cmd8a)
    manager.add_command(cmd8b)
    manager.add_command(cmd7)

    dag_allocate7 = search_cmd(manager.dag, cmd7)

    cmds_to_execute, allocate_cmds = manager.get_executable_commands(mapping)

    assert cmds_to_execute == [cmd01, cmd8a, cmd8b, cmd03, cmd34]
    assert allocate_cmds == [dag_allocate7]
    assert manager.size() == 1


def test_qubit_manager_generate_qubit_interaction_graph(qubit_manager):
    qb, allocate_cmds = allocate_all_qubits_cmd(9)
    cmd_list = [
        Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]]),
        Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]]),
        Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]]),
        Command(engine=None, gate=X, qubits=([qb[1]], )),
        Command(engine=None, gate=X, qubits=([qb[4]], ), controls=[qb[5]]),
        Command(engine=None, gate=X, qubits=([qb[5]], ), controls=[qb[6]]),
        Command(engine=None, gate=X, qubits=([qb[6]], ), controls=[qb[7]]),
        Command(engine=None, gate=X, qubits=([qb[7]], ), controls=[qb[8]])
    ]

    for cmd_last in [
            Command(engine=None, gate=X, qubits=([qb[3]], ), controls=[qb[0]]),
            Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[3]])
    ]:
        qubit_manager.clear()
        for cmd in cmd_list:
            qubit_manager.add_command(cmd)
        qubit_manager.add_command(cmd_last)

        subgraphs = qubit_manager.calculate_qubit_interaction_subgraphs(
            max_order=2)

        assert len(subgraphs) == 2
        assert len(subgraphs[0]) == 4
        assert all([n in subgraphs[0] for n in [0, 1, 2, 3]])
        assert subgraphs[0][0] == 0
        assert subgraphs[0][-2:] in ([1, 3], [3, 1])
        assert len(subgraphs[1]) == 3
        assert all([n in subgraphs[1] for n in [4, 5, 6]])


def test_qubit_manager_generate_swaps_change_mapping(qubit_manager):
    cmd05 = gen_cmd(0, 5)
    cmd07 = gen_cmd(0, 7)
    cmd58 = gen_cmd(5, 8)

    qubit_manager.add_command(cmd05)
    qubit_manager.add_command(cmd07)
    qubit_manager.add_command(cmd58)

    mapping = {i: i for i in range(9)}

    swaps, all_qubits = qubit_manager.generate_swaps(
        mapping, gatemgr.look_ahead_parallelism_cost_fun, {'W': 0.5})

    reverse_mapping = {v: k for k, v in mapping.items()}
    for bqb0, bqb1 in swaps:
        (reverse_mapping[bqb0],
         reverse_mapping[bqb1]) = (reverse_mapping[bqb1],
                                   reverse_mapping[bqb0])
    mapping = {v: k for k, v in reverse_mapping.items()}

    cmd_list, _ = qubit_manager.get_executable_commands(mapping)
    assert cmd_list == [cmd05, cmd07, cmd58]
    assert qubit_manager.size() == 0

    # ----------------------------------

    qubit_manager.clear()

    cmd06 = gen_cmd(0, 6)

    qubit_manager.add_command(cmd05)
    qubit_manager.add_command(cmd06)
    qubit_manager.add_command(cmd58)

    mapping = {i: i for i in range(9)}

    swaps, all_qubits = qubit_manager.generate_swaps(
        mapping, gatemgr.look_ahead_parallelism_cost_fun, {'W': 0.5})

    reverse_mapping = {v: k for k, v in mapping.items()}
    for bqb0, bqb1 in swaps:
        (reverse_mapping[bqb0],
         reverse_mapping[bqb1]) = (reverse_mapping[bqb1],
                                   reverse_mapping[bqb0])
    mapping = {v: k for k, v in reverse_mapping.items()}

    cmd_list, _ = qubit_manager.get_executable_commands(mapping)
    assert cmd_list == [cmd05, cmd06]
    assert qubit_manager.size() == 1


def test_qubit_manager_str():
    qubit_manager = gatemgr.GateManager(generate_grid_graph(3, 3))

    qb, allocate_cmds = allocate_all_qubits_cmd(9)
    cmd_list = [
        Command(engine=None, gate=H, qubits=([qb[0]], )),
        Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[8]]),
        Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[6]]),
        Command(engine=None, gate=X, qubits=([qb[1]], ), controls=[qb[7]]),
        Command(engine=None, gate=X, qubits=([qb[1]], )),
        Command(engine=None, gate=X, qubits=([qb[4]], ), controls=[qb[5]]),
        Command(engine=None, gate=X, qubits=([qb[5]], ), controls=[qb[4]]),
        Command(engine=None, gate=X, qubits=([qb[5]], ), controls=[qb[6]]),
        Command(engine=None, gate=X, qubits=([qb[6]], ), controls=[qb[7]]),
        Command(engine=None, gate=X, qubits=([qb[7]], ), controls=[qb[8]]),
    ]

    for cmd in cmd_list:
        qubit_manager.add_command(cmd)

    mapping = {i: i for i in range(16)}

    while qubit_manager.size() > 0:
        qubit_manager.get_executable_commands(mapping)

        swaps, all_qubits = qubit_manager.generate_swaps(
            mapping, gatemgr.look_ahead_parallelism_cost_fun, {'W': 0.5})

        reverse_mapping = {v: k for k, v in mapping.items()}
        for bqb0, bqb1 in swaps:
            (reverse_mapping[bqb0],
             reverse_mapping[bqb1]) = (reverse_mapping[bqb1],
                                       reverse_mapping[bqb0])
        mapping = {v: k for k, v in reverse_mapping.items()}

    str_repr = str(qubit_manager)

    num_of_2qubit_gates_ref = 0
    for cmd in cmd_list:
        if len({qubit.id for qureg in cmd.all_qubits for qubit in qureg}) == 2:
            num_of_2qubit_gates_ref += 1

    num_of_2qubit_gates = 0
    for line in str_repr.split('\n'):
        m = re.match(r'^\s+\[[0-9]+,\s[0-9]+\]:\s*([0-9]+)$', line)
        if m:
            num_of_2qubit_gates += int(m.group(1))

    assert num_of_2qubit_gates == num_of_2qubit_gates_ref
    assert str_repr.count("[4, 5]:  2") == 1
