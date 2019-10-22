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
import itertools

import pytest
import networkx as nx
from projectq.cengines import DummyEngine, LocalOptimizer, MainEngine
from projectq.meta import LogicalQubitIDTag
from projectq.ops import (Allocate, BasicGate, Command, Deallocate, FlushGate,
                          X, H, All, Measure, CNOT)
from projectq.types import WeakQubitRef

from projectq.cengines import _graphmapper as graphm

import projectq.cengines._gate_manager as gatemgr


def decay_to_string(self):
    s = ''
    for qubit_id, node in self._backend_ids.items():
        s += '{}: {}, {}\n'.format(qubit_id, node['decay'], node['lifetime'])
    return s


gatemgr.DecayManager.__str__ = decay_to_string
Command.__repr__ = Command.__str__


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
def grid22_graph():
    graph = nx.Graph()
    graph.add_nodes_from([0, 1, 2, 3])
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
    return graph


@pytest.fixture(scope="module")
def grid33_graph():
    return generate_grid_graph(3, 3)


@pytest.fixture
def grid22_graph_mapper(grid22_graph):
    mapper = graphm.GraphMapper(graph=grid22_graph,
                                add_qubits_to_mapping="fcfs")
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    return mapper, backend


@pytest.fixture
def grid33_graph_mapper(grid33_graph):
    mapper = graphm.GraphMapper(graph=grid33_graph,
                                add_qubits_to_mapping="fcfs")
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    return mapper, backend


@pytest.fixture
def simple_mapper(simple_graph):
    mapper = graphm.GraphMapper(graph=simple_graph,
                                add_qubits_to_mapping="fcfs")
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    return mapper, backend


# ==============================================================================


def get_node_list(self):
    return list(self.dag._dag.nodes)


graphm.GateManager._get_node_list = get_node_list

# ==============================================================================


def test_is_available(simple_graph):
    mapper = graphm.GraphMapper(graph=simple_graph)
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    cmd0 = Command(None, BasicGate(), qubits=([qb0], ))
    assert mapper.is_available(cmd0)
    cmd1 = Command(None, BasicGate(), qubits=([qb0], ), controls=[qb1])
    assert mapper.is_available(cmd1)
    cmd2 = Command(None, BasicGate(), qubits=([qb0], [qb1, qb2]))
    assert not mapper.is_available(cmd2)
    cmd3 = Command(None, BasicGate(), qubits=([qb0], [qb1]), controls=[qb2])
    assert not mapper.is_available(cmd3)


def test_invalid_gates(simple_mapper):
    mapper, backend = simple_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)

    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ), controls=[])
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1], ), controls=[])
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb2], ), controls=[])
    cmd3 = Command(engine=None, gate=X, qubits=([qb0], [qb1]), controls=[qb2])

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))

    with pytest.raises(Exception):
        mapper.receive([cmd0, cmd1, cmd2, cmd3, cmd_flush])


def test_init(simple_graph):
    opts = {'decay_opts': {'delta': 0.002}}

    mapper = graphm.GraphMapper(graph=simple_graph, opts=opts)
    assert mapper.qubit_manager._decay._delta == 0.002
    assert mapper.qubit_manager._decay._cutoff == 5

    opts = {'decay_opts': {'delta': 0.002, 'max_lifetime': 10}}

    mapper = graphm.GraphMapper(graph=simple_graph, opts=opts)
    assert mapper.qubit_manager._decay._delta == 0.002
    assert mapper.qubit_manager._decay._cutoff == 10


def test_resetting_mapping_to_none(simple_graph):
    mapper = graphm.GraphMapper(graph=simple_graph)
    mapper.current_mapping = {0: 1}
    assert mapper._current_mapping == {0: 1}
    assert mapper._reverse_current_mapping == {1: 0}
    mapper.current_mapping = {0: 0, 1: 4}
    assert mapper._current_mapping == {0: 0, 1: 4}
    assert mapper._reverse_current_mapping == {0: 0, 4: 1}
    mapper.current_mapping = None
    assert mapper._current_mapping == {}
    assert mapper._reverse_current_mapping == {}


def test_add_qubits_to_mapping_methods_failure(simple_graph):
    with pytest.raises(ValueError):
        graphm.GraphMapper(graph=simple_graph, add_qubits_to_mapping="as")


@pytest.mark.parametrize("add_qubits", ["fcfs", "fcfs_init", "FCFS"])
def test_add_qubits_to_mapping_methods_only_single(simple_graph, add_qubits):
    mapper = graphm.GraphMapper(graph=simple_graph,
                                add_qubits_to_mapping=add_qubits)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend

    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    gates = [
        Command(None, X, qubits=([qb[1]], )),
        Command(None, X, qubits=([qb[2]], )),
    ]

    mapper.receive(list(itertools.chain(allocate_cmds, gates, [cmd_flush])))
    assert mapper.num_mappings == 0


@pytest.mark.parametrize("add_qubits", ["fcfs", "fcfs_init", "FCFS"])
def test_add_qubits_to_mapping_methods(simple_graph, add_qubits):
    mapper = graphm.GraphMapper(graph=simple_graph,
                                add_qubits_to_mapping=add_qubits)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend

    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    gates = [
        Command(None, X, qubits=([qb[1]], ), controls=[qb[0]]),
        Command(None, X, qubits=([qb[1]], ), controls=[qb[2]]),
    ]

    mapper.receive(list(itertools.chain(allocate_cmds, gates, [cmd_flush])))
    assert mapper.num_mappings == 0


def test_qubit_placement_initial_mapping_single_qubit_gates(
        grid33_graph_mapper):
    grid33_graph_mapper[0].set_add_qubits_to_mapping(
        graphm._add_qubits_to_mapping)
    mapper, backend = deepcopy(grid33_graph_mapper)
    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))

    mapper.receive(allocate_cmds + [cmd_flush])
    mapping = mapper.current_mapping

    assert mapper.num_mappings == 0
    assert mapping[0] == 4
    assert sorted([mapping[1], mapping[2], mapping[3],
                   mapping[4]]) == [1, 3, 5, 7]
    assert sorted([mapping[5], mapping[6], mapping[7],
                   mapping[8]]) == [0, 2, 6, 8]


def test_qubit_placement_single_two_qubit_gate(grid33_graph_mapper):
    grid33_graph_mapper[0].set_add_qubits_to_mapping(
        graphm._add_qubits_to_mapping)
    mapper_ref, backend = deepcopy(grid33_graph_mapper)

    mapper_ref.current_mapping = {3: 3, 4: 4, 5: 5}
    mapper_ref._currently_allocated_ids = set(
        mapper_ref.current_mapping.keys())

    qb, allocate_cmds = allocate_all_qubits_cmd(mapper_ref)
    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))

    mapper = deepcopy(mapper_ref)
    mapper.receive([
        allocate_cmds[0],
        Command(None, X, qubits=([qb[0]], ), controls=[qb[3]]), cmd_flush
    ])
    mapping = mapper.current_mapping

    assert mapper.num_mappings == 0
    assert mapping[0] in {0, 6}

    mapper = deepcopy(mapper_ref)
    mapper.receive([
        allocate_cmds[6],
        Command(None, X, qubits=([qb[3]], ), controls=[qb[6]]), cmd_flush
    ])
    mapping = mapper.current_mapping

    assert mapper.num_mappings == 0
    assert mapping[6] in {0, 6}


def test_qubit_placement_double_two_qubit_gate(grid33_graph_mapper):
    grid33_graph_mapper[0].set_add_qubits_to_mapping(
        graphm._add_qubits_to_mapping)
    mapper_ref, backend_ref = deepcopy(grid33_graph_mapper)

    mapper_ref.current_mapping = {1: 1, 3: 3, 4: 4, 5: 5}
    mapper_ref._currently_allocated_ids = set(
        mapper_ref.current_mapping.keys())

    qb, allocate_cmds = allocate_all_qubits_cmd(mapper_ref)
    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))

    mapper = deepcopy(mapper_ref)
    backend = deepcopy(backend_ref)
    mapper.next_engine = backend
    mapper.receive([
        allocate_cmds[0],
        Command(None, X, qubits=([qb[0]], ), controls=[qb[3]]),
        Command(None, X, qubits=([qb[0]], ), controls=[qb[1]]), cmd_flush
    ])
    mapping = mapper.current_mapping

    assert mapper.num_mappings == 0
    assert mapping[0] == 0

    mapper = deepcopy(mapper_ref)
    backend = deepcopy(backend_ref)
    mapper.next_engine = backend
    mapper.receive([
        allocate_cmds[2],
        Command(None, X, qubits=([qb[2]], ), controls=[qb[3]]),
        Command(None, X, qubits=([qb[2]], ), controls=[qb[1]]),
        Command(None, X, qubits=([qb[2]], ), controls=[qb[5]]),
        cmd_flush,
    ])
    mapping = mapper.current_mapping

    # Make sure that the qb[2] was allocated at backend_id 0
    assert backend.received_commands[0].gate == Allocate
    assert backend.received_commands[0].qubits[0][0].id == 0
    assert backend.received_commands[0].tags == [LogicalQubitIDTag(2)]


def test_qubit_placement_multiple_two_qubit_gates(grid33_graph_mapper):
    grid33_graph_mapper[0].set_add_qubits_to_mapping(
        graphm._add_qubits_to_mapping)
    mapper, backend = deepcopy(grid33_graph_mapper)
    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    gates = [
        Command(None, X, qubits=([qb[1]], ), controls=[qb[0]]),
        Command(None, X, qubits=([qb[1]], ), controls=[qb[2]]),
        Command(None, X, qubits=([qb[1]], ), controls=[qb[3]]),
        Command(None, X, qubits=([qb[1]], ), controls=[qb[4]]),
    ]

    all_cmds = list(itertools.chain(allocate_cmds, gates))
    mapper, backend = deepcopy(grid33_graph_mapper)
    mapper.receive(all_cmds + [cmd_flush])
    mapping = mapper.current_mapping

    assert mapper.num_mappings == 0
    assert mapping[1] == 4
    assert sorted([mapping[0], mapping[2], mapping[3],
                   mapping[4]]) == [1, 3, 5, 7]
    assert sorted([mapping[5], mapping[6], mapping[7],
                   mapping[8]]) == [0, 2, 6, 8]

    all_cmds = list(itertools.chain(allocate_cmds[:5], gates))
    mapper, backend = deepcopy(grid33_graph_mapper)
    mapper.receive(all_cmds + [cmd_flush])

    gates = [
        Command(None, X, qubits=([qb[5]], ), controls=[qb[6]]),
        Command(None, X, qubits=([qb[5]], ), controls=[qb[7]]),
    ]
    all_cmds = list(itertools.chain(allocate_cmds[5:], gates))
    mapper.receive(all_cmds + [cmd_flush])
    assert mapper.num_mappings == 2


def test_send_possible_commands(simple_graph, simple_mapper):
    mapper, backend = simple_mapper
    mapper.current_mapping = dict(enumerate(range(len(simple_graph))))

    neighbours = set()
    for node in simple_graph:
        for other in simple_graph[node]:
            neighbours.add(frozenset((node, other)))

    neighbours = [tuple(s) for s in neighbours]

    for qb0_id, qb1_id in neighbours:
        qb0 = WeakQubitRef(engine=None, idx=qb0_id)
        qb1 = WeakQubitRef(engine=None, idx=qb1_id)
        cmd1 = Command(None, X, qubits=([qb0], ), controls=[qb1])
        cmd2 = Command(None, X, qubits=([qb1], ), controls=[qb0])
        mapper.qubit_manager.add_command(cmd1)
        mapper.qubit_manager.add_command(cmd2)
        mapper._send_possible_commands()
        assert mapper.qubit_manager.size() == 0

    for qb0_id, qb1_id in itertools.permutations(range(7), 2):
        if ((qb0_id, qb1_id) not in neighbours
                and (qb1_id, qb0_id) not in neighbours):
            qb0 = WeakQubitRef(engine=None, idx=qb0_id)
            qb1 = WeakQubitRef(engine=None, idx=qb1_id)
            cmd = Command(None, X, qubits=([qb0], ), controls=[qb1])
            mapper.qubit_manager.clear()
            mapper.qubit_manager.add_command(cmd)
            mapper._send_possible_commands()
            assert mapper.qubit_manager.size() == 1


def test_send_possible_commands_deallocate(simple_mapper):
    mapper, backend = simple_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(engine=None,
                   gate=Deallocate,
                   qubits=([qb0], ),
                   controls=[],
                   tags=[])
    mapper.qubit_manager.add_command(cmd0)
    mapper.current_mapping = dict()
    mapper._currently_allocated_ids = set([10])
    # not yet allocated:
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 0
    assert mapper.qubit_manager.size() == 1
    # allocated:
    mapper.current_mapping = {0: 3}
    mapper._currently_allocated_ids.add(0)
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 1
    assert mapper.qubit_manager.size() == 0
    assert mapper.current_mapping == dict()
    assert mapper._currently_allocated_ids == set([10])


def test_send_possible_commands_no_initial_mapping(simple_mapper):
    mapper, backend = simple_mapper

    assert mapper._current_mapping == {}

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=-1)

    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ), controls=[])
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1], ), controls=[])
    cmd2 = Command(None, X, qubits=([qb0], ), controls=[qb1])
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb2], ))
    all_cmds = [cmd0, cmd1, cmd2, cmd_flush]
    mapper.receive(all_cmds)

    assert mapper._current_mapping
    assert mapper.qubit_manager.size() == 0


def test_send_possible_commands_one_inactive_qubit(simple_mapper):
    mapper, backend = simple_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(engine=None,
                   gate=Allocate,
                   qubits=([qb0], ),
                   controls=[],
                   tags=[])
    cmd1 = Command(engine=None, gate=X, qubits=([qb0], ), controls=[qb1])
    mapper.qubit_manager.add_command(cmd0)
    mapper.qubit_manager.add_command(cmd1)
    mapper.current_mapping = {0: 0}
    mapper._send_possible_commands()
    mapper.qubit_manager._get_node_list()[0].cmd == cmd1


def test_run_and_receive(simple_graph, simple_mapper):
    mapper, backend = simple_mapper

    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)

    gates = [
        Command(None, X, qubits=([qb[0]], ), controls=[qb[1]]),
        Command(None, X, qubits=([qb[1]], ), controls=[qb[2]]),
        Command(None, X, qubits=([qb[1]], ), controls=[qb[5]]),
        Command(None, X, qubits=([qb[2]], ), controls=[qb[3]]),
        Command(None, X, qubits=([qb[5]], ), controls=[qb[3]]),
        Command(None, X, qubits=([qb[3]], ), controls=[qb[4]]),
        Command(None, X, qubits=([qb[3]], ), controls=[qb[6]]),
        Command(None, X, qubits=([qb[4]], ), controls=[qb[6]]),
    ]
    deallocate_cmds = [
        Command(engine=None, gate=Deallocate, qubits=([qb[1]], ))
    ]

    allocated_qubits_ref = set([0, 2, 3, 4, 5, 6])

    all_cmds = list(itertools.chain(allocate_cmds, gates, deallocate_cmds))
    mapper.receive(all_cmds)
    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    mapper.receive([cmd_flush])
    assert mapper.qubit_manager.size() == 0
    assert len(backend.received_commands) == len(all_cmds) + 1
    assert mapper._currently_allocated_ids == allocated_qubits_ref

    mapping = dict(enumerate(range(len(simple_graph))))
    del mapping[1]
    assert mapper.current_mapping == mapping

    cmd9 = Command(None, X, qubits=([qb[0]], ), controls=[qb[6]])
    mapper.receive([cmd9, cmd_flush])
    assert mapper._currently_allocated_ids == allocated_qubits_ref
    for idx in allocated_qubits_ref:
        assert idx in mapper.current_mapping
    assert mapper.qubit_manager.size() == 0
    assert len(mapper.current_mapping) == 6
    assert mapper.num_mappings == 1


def test_send_two_qubit_gate_before_swap(simple_mapper):
    qb, all_cmds = allocate_all_qubits_cmd(simple_mapper[0])

    all_cmds.insert(3, None)
    all_cmds.insert(5, Command(None, X, qubits=([qb[2]], ), controls=[qb[3]]))

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    all_cmds.append(
        Command(engine=None, gate=FlushGate(), qubits=([qb_flush], )))

    for cmd in [
            Command(None, X, qubits=([qb[0]], ), controls=[qb[2]]),
            Command(None, X, qubits=([qb[2]], ), controls=[qb[0]])
    ]:
        mapper, backend = deepcopy(simple_mapper)

        all_cmds[3] = cmd

        mapper.qubit_manager.clear()
        mapper.receive(all_cmds)
        mapper._run()
        assert mapper.num_mappings == 1

        if mapper.current_mapping[2] == 2:
            # qb[2] has not moved, all_cmds[5] and everything
            # thereafter is possible
            assert mapper.qubit_manager.size() == 0
            assert mapper.current_mapping == {
                0: 1,
                1: 0,
                2: 2,
                3: 3,
                4: 4,
                5: 5,
                6: 6
            }
        else:
            # qb[2] moved, all_cmds[5] not possible
            assert mapper._stored_commands == [all_cmds[5]] + all_cmds[-4:]
            assert mapper.current_mapping == {
                0: 0,
                1: 2,
                2: 1,
                3: 3,
            }


def test_send_two_qubit_gate_before_swap_nonallocated_qubits(simple_mapper):
    qb, allocate_cmds = allocate_all_qubits_cmd(simple_mapper[0])

    all_cmds = [
        allocate_cmds[0],
        allocate_cmds[-1],
        None,
        Command(None, X, qubits=([qb[6]], ), controls=[qb[4]]),
    ]

    idx = all_cmds.index(None)

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    all_cmds.append(
        Command(engine=None, gate=FlushGate(), qubits=([qb_flush], )))

    for cmd in [
            Command(None, X, qubits=([qb[0]], ), controls=[qb[6]]),
            Command(None, X, qubits=([qb[6]], ), controls=[qb[0]])
    ]:
        mapper, backend = deepcopy(simple_mapper)
        mapper.current_mapping = dict(enumerate(range(len(qb))))

        all_cmds[idx] = cmd

        mapper.receive(all_cmds)
        mapper._run()
        assert mapper.num_mappings == 1
        assert mapper.current_mapping[4] == 4
        assert mapper.current_mapping[5] == 5
        assert mapper.current_mapping[6] in [3, 6]

        if mapper.current_mapping[6] == 3:
            # qb[6] is on position 3, all commands are possible
            assert mapper.qubit_manager.size() == 0
            assert mapper.current_mapping == {0: 2, 4: 4, 5: 5, 6: 3}
        else:
            assert mapper.qubit_manager.size() == 0
            assert mapper.current_mapping == {0: 3, 4: 4, 5: 5, 6: 6}


def test_allocate_too_many_qubits(simple_mapper):
    mapper, backend = simple_mapper

    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)

    qb.append(WeakQubitRef(engine=None, idx=len(qb)))
    allocate_cmds.append(
        Command(engine=None, gate=Allocate, qubits=([qb[-1]], )))

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))

    with pytest.raises(RuntimeError):
        mapper.receive(allocate_cmds + [cmd_flush])


def test_send_possible_commands_reallocate_backend_id(grid22_graph_mapper):
    mapper, backend = grid22_graph_mapper
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=3)
    qb4 = WeakQubitRef(engine=None, idx=4)
    all_cmds = [
        Command(engine=None, gate=Allocate, qubits=([qb0], )),
        Command(engine=None, gate=Allocate, qubits=([qb1], )),
        Command(engine=None, gate=Allocate, qubits=([qb2], )),
        Command(engine=None, gate=Allocate, qubits=([qb3], )),
        Command(engine=None, gate=X, qubits=([qb1], )),
        Command(engine=None, gate=Deallocate, qubits=([qb1], )),
        Command(engine=None, gate=Allocate, qubits=([qb4], )),
        Command(engine=None, gate=X, qubits=([qb4], )),
    ]

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    mapper.receive(all_cmds + [cmd_flush])
    assert mapper.current_mapping == {0: 0, 2: 2, 3: 3, 4: 1}
    assert mapper.qubit_manager.size() == 0
    assert len(backend.received_commands) == 9


def test_correct_stats(simple_mapper):
    mapper, backend = simple_mapper

    # Should test stats for twice same mapping but depends on heuristic
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1], ))
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb2], ))

    cmd3 = Command(None, X, qubits=([qb0], ), controls=[qb1])
    cmd4 = Command(None, X, qubits=([qb1], ), controls=[qb2])
    cmd5 = Command(None, X, qubits=([qb0], ), controls=[qb2])
    cmd6 = Command(None, X, qubits=([qb2], ), controls=[qb1])
    cmd7 = Command(None, X, qubits=([qb0], ), controls=[qb1])
    cmd8 = Command(None, X, qubits=([qb1], ), controls=[qb2])
    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    mapper.receive(
        [cmd0, cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7, cmd8, cmd_flush])
    assert mapper.num_mappings == 2


def test_send_possible_cmds_before_new_mapping(simple_mapper):
    mapper, backend = simple_mapper

    def dont_call_mapping():
        raise Exception

    mapper._find_paths = dont_call_mapping

    mapper.current_mapping = {0: 1}
    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ))
    qb2 = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb2], ))
    mapper.receive([cmd0, cmd_flush])


def test_logical_id_tags_allocate_and_deallocate(simple_mapper):
    mapper, backend = simple_mapper
    mapper.current_mapping = {0: 1, 1: 6}

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1], ))
    cmd2 = Command(None, X, qubits=([qb0], ), controls=[qb1])
    cmd3 = Command(engine=None, gate=Deallocate, qubits=([qb0], ))
    cmd4 = Command(engine=None, gate=Deallocate, qubits=([qb1], ))

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    mapper.receive([cmd0, cmd1, cmd2, cmd_flush])
    assert backend.received_commands[0].gate == Allocate
    assert backend.received_commands[0].qubits[0][0].id == 1
    assert backend.received_commands[0].tags == [LogicalQubitIDTag(0)]
    assert backend.received_commands[1].gate == Allocate
    assert backend.received_commands[1].qubits[0][0].id == 6
    assert backend.received_commands[1].tags == [LogicalQubitIDTag(1)]
    for cmd in backend.received_commands[2:]:
        if cmd.gate == Allocate:
            assert cmd.tags == []
        elif cmd.gate == Deallocate:
            assert cmd.tags == []
    mapped_id_for_0 = mapper.current_mapping[0]
    mapped_id_for_1 = mapper.current_mapping[1]
    mapper.receive([cmd3, cmd4, cmd_flush])
    assert backend.received_commands[-3].gate == Deallocate
    assert backend.received_commands[-3].qubits[0][0].id == mapped_id_for_0
    assert backend.received_commands[-3].tags == [LogicalQubitIDTag(0)]
    assert backend.received_commands[-2].gate == Deallocate
    assert backend.received_commands[-2].qubits[0][0].id == mapped_id_for_1
    assert backend.received_commands[-2].tags == [LogicalQubitIDTag(1)]


def test_check_that_local_optimizer_doesnt_merge(simple_graph):
    mapper = graphm.GraphMapper(graph=simple_graph)
    optimizer = LocalOptimizer(10)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = optimizer
    mapper.current_mapping = dict(enumerate(range(len(simple_graph))))
    mapper.current_mapping = {0: 0}
    mapper.storage = 1
    optimizer.next_engine = backend

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ))
    cmd1 = Command(None, X, qubits=([qb0], ))
    cmd2 = Command(engine=None, gate=Deallocate, qubits=([qb0], ))
    mapper.receive([cmd0, cmd1, cmd2])
    assert mapper.qubit_manager.size() == 0
    mapper.current_mapping = {1: 0}
    cmd3 = Command(engine=None, gate=Allocate, qubits=([qb1], ))
    cmd4 = Command(None, X, qubits=([qb1], ))
    cmd5 = Command(engine=None, gate=Deallocate, qubits=([qb1], ))
    mapper.receive([cmd3, cmd4, cmd5, cmd_flush])
    assert len(backend.received_commands) == 7


def test_mapper_to_str(simple_graph):
    mapper = graphm.GraphMapper(graph=simple_graph,
                                add_qubits_to_mapping="fcfs")
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend, [mapper])
    qureg = eng.allocate_qureg(len(simple_graph))

    eng.flush()
    assert mapper.current_mapping == dict(enumerate(range(len(simple_graph))))

    H | qureg[0]
    X | qureg[2]

    CNOT | (qureg[6], qureg[4])
    CNOT | (qureg[6], qureg[0])
    CNOT | (qureg[4], qureg[5])

    All(Measure) | qureg
    eng.flush()

    str_repr = str(mapper)
    assert str_repr.count("Number of mappings: 1") == 1
    assert str_repr.count("2:   1") == 1
    assert str_repr.count("3:   1") == 1

    sent_gates = [cmd.gate for cmd in backend.received_commands]
    assert sent_gates.count(H) == 1
    assert sent_gates.count(X) == 4
    assert sent_gates.count(Measure) == 7
