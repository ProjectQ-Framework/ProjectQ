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
import random

import pytest
import networkx as nx
import projectq
from projectq.cengines import DummyEngine, LocalOptimizer
from projectq.meta import LogicalQubitIDTag
from projectq.ops import (Allocate, BasicGate, Command, Deallocate, FlushGate,
                          X)
from projectq.types import WeakQubitRef

from projectq.cengines import _graphmapper as graphm


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
    graph.add_edges_from([(0, 1), (1, 2), (1, 5), (2, 3), (5, 3), (3, 4), (3,
                                                                           6),
                          (4, 6)])
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
    mapper = graphm.GraphMapper(graph=grid22_graph)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    return mapper, backend


@pytest.fixture
def grid33_graph_mapper(grid33_graph):
    mapper = graphm.GraphMapper(graph=grid33_graph)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    return mapper, backend


@pytest.fixture
def simple_mapper(simple_graph):
    mapper = graphm.GraphMapper(graph=simple_graph)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    return mapper, backend


# ==============================================================================


def test_path_cache_exhaustive():
    path_length_threshold = 3
    cache = graphm.PathCacheExhaustive(path_length_threshold)

    assert not cache._cache
    cache.add_path(['a', 'b', 'c'])
    assert cache._cache == {cache.key_type(('a', 'c')): ['a', 'b', 'c']}

    assert cache.has_path('a', 'c')
    assert not cache.has_path('a', 'b')
    assert not cache.has_path('b', 'c')

    cache.empty_cache()
    assert not cache._cache

    cache.add_path(['a', 'b', 'c', 'd'])
    assert cache._cache == {
        cache.key_type(('a', 'c')): ['a', 'b', 'c'],
        cache.key_type(('a', 'd')): ['a', 'b', 'c', 'd'],
        cache.key_type(('b', 'd')): ['b', 'c', 'd']
    }
    assert cache.has_path('a', 'd')
    assert cache.has_path('d', 'a')
    assert cache.has_path('a', 'c')
    assert cache.has_path('b', 'd')
    assert not cache.has_path('a', 'b')
    assert not cache.has_path('b', 'a')
    assert not cache.has_path('b', 'c')
    assert not cache.has_path('c', 'd')

    str_repr = str(cache)
    assert str_repr.count("['a', 'd']: ['a', 'b', 'c', 'd']") == 1
    assert str_repr.count("['a', 'c']: ['a', 'b', 'c']") == 1
    assert str_repr.count("['b', 'd']: ['b', 'c', 'd']") == 1


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
    qb3 = WeakQubitRef(engine=None, idx=-1)

    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ), controls=[])
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1], ), controls=[])
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb2], ), controls=[])
    cmd3 = Command(engine=None, gate=X, qubits=([qb0], [qb1]), controls=[qb2])
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb3], ))

    with pytest.raises(Exception):
        mapper.receive([cmd0, cmd1, cmd2, cmd3, cmd_flush])


def test_run_infinite_loop_detection(simple_mapper):
    mapper, backend = simple_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=-1)

    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb3], ))

    cmd0 = Command(engine=None, gate=X, qubits=([qb0], ), controls=[])
    with pytest.raises(RuntimeError):
        mapper.receive([cmd0, cmd_flush])

    mapper._stored_commands = []
    cmd0 = Command(engine=None, gate=X, qubits=([qb0], ), controls=[qb1])
    with pytest.raises(RuntimeError):
        mapper.receive([cmd0, cmd_flush])


def test_valid_and_invalid_graphs(simple_graph, grid33_graph):
    graph = nx.Graph()
    graph.add_nodes_from('abcd')
    with pytest.raises(RuntimeError):
        graphm.GraphMapper(graph=graph)

    graph.add_edges_from([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')])
    with pytest.raises(RuntimeError):
        graphm.GraphMapper(graph=graph)

    graph = deepcopy(simple_graph)
    graph.remove_edge(0, 1)
    with pytest.raises(RuntimeError):
        graphm.GraphMapper(graph=graph)

    mapper = graphm.GraphMapper(graph=simple_graph)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)
    mapper._stored_commands = allocate_cmds
    mapper._run()
    assert not mapper._send_possible_commands()
    assert mapper.current_mapping == dict(enumerate(range(len(simple_graph))))

    mapper = graphm.GraphMapper(graph=grid33_graph)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)
    mapper._stored_commands = allocate_cmds
    mapper._run()
    assert not mapper._send_possible_commands()
    assert mapper.current_mapping == dict(enumerate(range(len(grid33_graph))))


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
        mapper._stored_commands = [cmd1, cmd2]
        mapper._send_possible_commands()
        assert len(mapper._stored_commands) == 0

    for qb0_id, qb1_id in itertools.permutations(range(8), 2):
        if ((qb0_id, qb1_id) not in neighbours
                and (qb1_id, qb0_id) not in neighbours):
            qb0 = WeakQubitRef(engine=None, idx=qb0_id)
            qb1 = WeakQubitRef(engine=None, idx=qb1_id)
            cmd = Command(None, X, qubits=([qb0], ), controls=[qb1])
            mapper._stored_commands = [cmd]
            mapper._send_possible_commands()
            assert len(mapper._stored_commands) == 1


def test_send_possible_commands_allocate(simple_mapper):
    mapper, backend = simple_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(
        engine=None, gate=Allocate, qubits=([qb0], ), controls=[], tags=[])
    mapper._stored_commands = [cmd0]
    mapper._currently_allocated_ids = set([10])
    # not in mapping:
    mapper.current_mapping = dict()
    assert len(backend.received_commands) == 0
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 0
    assert mapper._stored_commands == [cmd0]
    # in mapping:
    mapper.current_mapping = {0: 3}
    mapper._send_possible_commands()
    assert len(mapper._stored_commands) == 0
    # Only self._run() sends Allocate gates
    mapped0 = WeakQubitRef(engine=None, idx=3)
    received_cmd = Command(
        engine=mapper,
        gate=Allocate,
        qubits=([mapped0], ),
        controls=[],
        tags=[LogicalQubitIDTag(0)])
    assert backend.received_commands[0] == received_cmd
    assert mapper._currently_allocated_ids == set([10, 0])


def test_send_possible_commands_allocation_no_active_qubits(
        grid22_graph_mapper):
    mapper, backend = grid22_graph_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=3)

    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1], ))
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb2], ))
    cmd3 = Command(engine=None, gate=X, qubits=([qb0], ), controls=[qb2])
    cmd4 = Command(engine=None, gate=Allocate, qubits=([qb3], ))
    cmd5 = Command(engine=None, gate=X, qubits=([qb3], ))
    cmd6 = Command(engine=None, gate=Deallocate, qubits=([qb3], ))

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))

    mapper._stored_commands = [
        cmd0, cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd_flush
    ]

    mapper._run()
    assert len(mapper._stored_commands) == 4
    assert mapper._stored_commands[0] == cmd4
    assert mapper._stored_commands[1] == cmd5
    assert mapper._stored_commands[2] == cmd6
    mapper._run()
    assert len(mapper._stored_commands) == 1
    assert mapper._stored_commands[0] == cmd_flush


def test_send_possible_commands_deallocate(simple_mapper):
    mapper, backend = simple_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(
        engine=None, gate=Deallocate, qubits=([qb0], ), controls=[], tags=[])
    mapper._stored_commands = [cmd0]
    mapper.current_mapping = dict()
    mapper._currently_allocated_ids = set([10])
    # not yet allocated:
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 0
    assert mapper._stored_commands == [cmd0]
    # allocated:
    mapper.current_mapping = {0: 3}
    mapper._currently_allocated_ids.add(0)
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 1
    assert len(mapper._stored_commands) == 0
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
    assert len(mapper._stored_commands) == 0


def test_send_possible_commands_keep_remaining_gates(simple_mapper):
    mapper, backend = simple_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(
        engine=None, gate=Allocate, qubits=([qb0], ), controls=[], tags=[])
    cmd1 = Command(
        engine=None, gate=Deallocate, qubits=([qb0], ), controls=[], tags=[])
    cmd2 = Command(
        engine=None, gate=Allocate, qubits=([qb1], ), controls=[], tags=[])

    mapper._stored_commands = [cmd0, cmd1, cmd2]
    mapper.current_mapping = {0: 0}
    mapper._send_possible_commands()
    assert mapper._stored_commands == [cmd2]


def test_send_possible_commands_one_inactive_qubit(simple_mapper):
    mapper, backend = simple_mapper

    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(
        engine=None, gate=Allocate, qubits=([qb0], ), controls=[], tags=[])
    cmd1 = Command(engine=None, gate=X, qubits=([qb0], ), controls=[qb1])
    mapper._stored_commands = [cmd0, cmd1]
    mapper.current_mapping = {0: 0}
    mapper._send_possible_commands()
    assert mapper._stored_commands == [cmd1]


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
        Command(None, X, qubits=([qb[4]], ), controls=[qb[6]])
    ]
    deallocate_cmds = [
        Command(engine=None, gate=Deallocate, qubits=([qb[1]], ))
    ]

    allocated_qubits_ref = set([0, 2, 3, 4, 5, 6])

    all_cmds = list(itertools.chain(allocate_cmds, gates, deallocate_cmds))
    mapper.receive(all_cmds)
    assert mapper._stored_commands == all_cmds
    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))
    mapper.receive([cmd_flush])
    assert mapper._stored_commands == []
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
    assert mapper._stored_commands == []
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
        mapper.enable_caching = False

        all_cmds[3] = cmd

        mapper._stored_commands = all_cmds
        print([str(cmd) for cmd in all_cmds])
        mapper._run()
        assert mapper.num_mappings == 1
        if mapper.current_mapping[2] == 2:
            # qb[2] has not moved, all_cmds[5] is possible
            assert mapper._stored_commands == all_cmds[6:]
            assert mapper.current_mapping == {0: 1, 1: 0, 2: 2, 3: 3}
        else:
            # qb[2] moved, all_cmds[5] not possible
            assert mapper._stored_commands == all_cmds[5:]
            assert mapper.current_mapping == {0: 0, 1: 2, 2: 1, 3: 3}


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
        mapper.enable_caching = False

        all_cmds[idx] = cmd

        mapper._stored_commands = all_cmds
        mapper._run()
        assert mapper.num_mappings == 1

        if mapper.current_mapping[4] == 4 and mapper.current_mapping[5] == 5:
            if mapper.current_mapping[6] == 3:
                # qb[6] is on position 3, all commands are possible
                assert mapper._stored_commands == all_cmds[-1:]
                assert mapper.current_mapping == {0: 2, 4: 4, 5: 5, 6: 3}
            else:
                # qb[6] is on position 2, all_cmds[8] is not possible
                assert mapper._stored_commands == all_cmds[-2:]
                assert mapper.current_mapping == {0: 1, 4: 4, 5: 5, 6: 2}
        else:
            # Should not happen...
            assert False


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
    assert len(mapper._stored_commands) == 0
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
    assert len(mapper._stored_commands) == 0
    mapper.current_mapping = {1: 0}
    cmd3 = Command(engine=None, gate=Allocate, qubits=([qb1], ))
    cmd4 = Command(None, X, qubits=([qb1], ))
    cmd5 = Command(engine=None, gate=Deallocate, qubits=([qb1], ))
    mapper.receive([cmd3, cmd4, cmd5, cmd_flush])
    assert len(backend.received_commands) == 7


@pytest.mark.parametrize("enable_caching", [False, True])
def test_3x3_grid_multiple_simultaneous_paths(grid33_graph_mapper,
                                              enable_caching):
    mapper, backend = grid33_graph_mapper
    mapper.enable_caching = enable_caching

    qb, allocate_cmds = allocate_all_qubits_cmd(mapper)

    cmd0 = Command(None, X, qubits=([qb[0]], ), controls=[qb[6]])
    cmd1 = Command(None, X, qubits=([qb[1]], ), controls=[qb[7]])
    cmd2 = Command(None, X, qubits=([qb[2]], ), controls=[qb[8]])

    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush], ))

    mapper.receive(allocate_cmds + [cmd0, cmd1, cmd2, cmd_flush])
    assert not mapper._stored_commands
    assert mapper.num_mappings == 1
    assert mapper.depth_of_swaps == {1: 1}
    assert mapper.current_mapping == {
        0: 0,
        1: 1,
        2: 2,
        3: 6,
        4: 7,
        5: 8,
        6: 3,
        7: 4,
        8: 5
    }

    cmd3 = Command(None, X, qubits=([qb[0]], ), controls=[qb[2]])
    cmd4 = Command(None, X, qubits=([qb[3]], ), controls=[qb[5]])
    cmd5 = Command(None, X, qubits=([qb[6]], ), controls=[qb[8]])
    mapper.receive([cmd3, cmd4, cmd5, cmd_flush])

    assert not mapper._stored_commands
    assert mapper.num_mappings == 2
    assert mapper.depth_of_swaps == {1: 2}
    assert mapper.current_mapping == {
        0: 0,
        1: 2,
        2: 1,
        3: 6,
        4: 8,
        5: 7,
        6: 3,
        7: 5,
        8: 4
    }

    if enable_caching:
        assert mapper._path_cache._cache
        assert mapper._path_cache.has_path(0, 6)
        assert mapper._path_cache.has_path(1, 7)
        assert mapper._path_cache.has_path(2, 8)
        assert mapper._path_cache.has_path(0, 2)
        assert mapper._path_cache.has_path(3, 5)
        assert mapper._path_cache.has_path(6, 8)
        assert not mapper._path_cache.has_path(0, 1)
        assert not mapper._path_cache.has_path(1, 2)
        assert not mapper._path_cache.has_path(3, 4)
        assert not mapper._path_cache.has_path(4, 5)
        assert not mapper._path_cache.has_path(6, 7)
        assert not mapper._path_cache.has_path(7, 8)
