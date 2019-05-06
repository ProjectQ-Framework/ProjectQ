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
"""Tests for projectq.cengines._graph_path_manager.py."""

from copy import deepcopy
import itertools
import networkx as nx
import pytest
from projectq.cengines._graph_path_manager import PathManager, \
    PathCacheExhaustive, _find_first_order_intersections, _Crossing

# ==============================================================================


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


@pytest.fixture
def grid44_manager():
    return PathManager(graph=generate_grid_graph(4, 4), enable_caching=False)


# ==============================================================================


def test_path_cache_exhaustive():
    path_length_threshold = 3
    cache = PathCacheExhaustive(path_length_threshold)

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
    assert cache.get_path('a', 'd') == ['a', 'b', 'c', 'd']
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


def test_path_container_crossing_class():
    Crossing = _Crossing
    crossing_list = [Crossing(0, [1]), Crossing(1, [1]), Crossing(2, [2])]

    assert Crossing(0, [1]) == Crossing(0, [1])
    assert Crossing(0, [1]) != Crossing(1, [1])
    assert Crossing(0, [1]) != Crossing(0, [0, 1])
    assert Crossing(0, [0]) != Crossing(1, [0, 1])

    assert [0, 1] == Crossing(0, [0, 1])
    assert [0, 1] == Crossing(1, [0, 1])
    assert [0, 1] != Crossing(0, [0])
    assert [0, 1] != Crossing(1, [0])

    assert Crossing(0, [1]) in crossing_list
    assert [0] not in crossing_list
    assert [1] in crossing_list

    assert str(Crossing(0, [1])) == "{} {}".format(0, [1])
    assert repr(Crossing(0, [1])) == "Crossing({}, {})".format(0, [1])

    with pytest.raises(NotImplementedError):
        assert "" == Crossing(0, [1])


# ==============================================================================


def test_valid_and_invalid_graphs(simple_graph):
    graph = nx.Graph()
    graph.add_nodes_from('abcd')
    with pytest.raises(RuntimeError):
        PathManager(graph=graph)

    graph.add_edges_from([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')])
    with pytest.raises(RuntimeError):
        PathManager(graph=graph)

    graph = deepcopy(simple_graph)
    graph.remove_edge(0, 1)
    with pytest.raises(RuntimeError):
        PathManager(graph=graph)


def test_path_container_has_interaction(grid44_manager):
    path_dict = {
        0: ([4, 5], [6, 7]),
        1: ([1, 5], [9, 13]),
        2: ([8, 9], [10, 11, 15])
    }
    grid44_manager.paths = path_dict

    assert grid44_manager.has_interaction(4, 7)
    assert grid44_manager.has_interaction(7, 4)
    assert grid44_manager.has_interaction(8, 15)
    assert grid44_manager.has_interaction(15, 8)
    assert not grid44_manager.has_interaction(4, 5)
    assert not grid44_manager.has_interaction(4, 6)
    assert not grid44_manager.has_interaction(4, 8)
    assert not grid44_manager.has_interaction(4, 9)
    assert not grid44_manager.has_interaction(9, 4)
    assert not grid44_manager.has_interaction(1, 5)
    assert not grid44_manager.has_interaction(1, 9)
    assert not grid44_manager.has_interaction(8, 9)
    assert not grid44_manager.has_interaction(8, 10)
    assert not grid44_manager.has_interaction(8, 11)


def test_path_container_get_all_nodes(grid44_manager):
    path_dict = {
        0: ([4, 5], [6, 7]),
        1: ([1, 5], [9, 13]),
        2: ([8, 9], [10, 11, 15])
    }
    grid44_manager.paths = path_dict

    assert grid44_manager.get_all_nodes() == set((1, 4, 5, 6, 7, 8, 9, 10, 11,
                                                  13, 15))


def test_path_container_get_all_paths(grid44_manager):
    path_dict = {
        0: ([4, 5], [6, 7]),
        1: ([1, 5], [9, 13]),
        2: ([8, 9], [10, 11, 15])
    }
    grid44_manager.paths = path_dict

    assert grid44_manager.get_all_paths() == [[4, 5, 6, 7], [1, 5, 9, 13],
                                              [8, 9, 10, 11, 15]]


def test_path_container_max_order(grid44_manager):
    assert grid44_manager.max_crossing_order() == 0

    assert grid44_manager.try_add_path([4, 5, 6, 7])
    assert grid44_manager.max_crossing_order() == 0

    assert grid44_manager.try_add_path([1, 5, 9, 13])
    assert grid44_manager.max_crossing_order() == 1


def test_path_container_clear(grid44_manager):
    grid44_manager.paths = {
        0: ([4, 5], [6, 7]),
        1: ([1, 5], [9, 13]),
        2: ([8, 9], [10, 11, 15])
    }
    grid44_manager.crossings = {0: None, 1: None, 2: None}  # dummy values
    grid44_manager.paths_stats = {0: 0, 1: 1, 2: 2}  # dummy values

    grid44_manager.clear_paths()
    assert not grid44_manager.paths
    assert not grid44_manager.crossings
    assert grid44_manager.paths_stats

    grid44_manager.paths = {
        0: ([4, 5], [6, 7]),
        1: ([1, 5], [9, 13]),
        2: ([8, 9], [10, 11, 15])
    }
    grid44_manager.crossings = {0: None, 1: None, 2: None}  # dummy values
    grid44_manager.paths_stats = {0: 0, 1: 1, 2: 2}  # dummy values

    grid44_manager.clear()
    assert not grid44_manager.paths
    assert not grid44_manager.crossings
    assert not grid44_manager.paths_stats


def test_path_container_add_path(grid44_manager):
    Crossing = _Crossing

    assert grid44_manager.try_add_path([4, 5, 6, 7])
    assert grid44_manager.get_all_paths() == [[4, 5, 6, 7]]
    assert grid44_manager.crossings == {0: []}

    assert not grid44_manager.try_add_path([4, 8, 12])
    assert not grid44_manager.try_add_path([0, 1, 2, 3, 7])
    assert not grid44_manager.try_add_path([1, 5, 6, 10])
    assert grid44_manager.get_all_paths() == [[4, 5, 6, 7]]
    assert grid44_manager.crossings == {0: []}

    assert grid44_manager.try_add_path([1, 5, 9, 13])
    assert [4, 5, 6, 7] in grid44_manager.get_all_paths()
    assert [1, 5, 9, 13] in grid44_manager.get_all_paths()
    assert grid44_manager.crossings == {
        0: [Crossing(1, [5])],
        1: [Crossing(0, [5])]
    }

    assert grid44_manager.try_add_path([10, 6, 9, 14, 15])
    assert [4, 5, 6, 7] in grid44_manager.get_all_paths()
    assert [4, 5, 6, 7] in grid44_manager.get_all_paths()
    assert [10, 6, 9, 14, 15] in grid44_manager.get_all_paths()

    crossings_overlap = [
        sorted([c.overlap[0] for c in crossing_list])
        for crossing_list in grid44_manager.crossings.values()
    ]

    assert [6, 9] in crossings_overlap
    assert [5, 9] in crossings_overlap
    assert [5, 6] in crossings_overlap


def test_path_container_push_interaction(grid44_manager):
    assert grid44_manager.push_interaction(4, 7)
    assert grid44_manager.push_interaction(4, 7)
    assert grid44_manager.get_all_paths() == [[4, 5, 6, 7]]
    assert grid44_manager.crossings == {0: []}

    assert grid44_manager.push_interaction(14, 15)
    assert grid44_manager.get_all_paths() == [[4, 5, 6, 7]]
    assert grid44_manager.crossings == {0: []}

    assert not grid44_manager.push_interaction(0, 4)


@pytest.mark.parametrize("enable_caching", [False, True])
def test_path_container_push_interaction_alternative(grid44_manager,
                                                     enable_caching):
    grid44_manager.enable_caching = enable_caching
    interaction_list = [
        [(4, 7), (0, 12), False],
        [(4, 7), (12, 0), True],
        [(7, 4), (0, 12), False],
        [(7, 4), (12, 0), True],
    ]

    for inter1, inter2, may_fail in interaction_list:
        grid44_manager.clear_paths()
        assert grid44_manager.push_interaction(*inter1)
        if may_fail:
            if grid44_manager.push_interaction(*inter2):
                assert grid44_manager.get_all_paths()[1] in ([4, 5, 6, 7],
                                                             [7, 6, 5, 4])
        else:
            assert grid44_manager.push_interaction(*inter2)
            assert grid44_manager.get_all_paths()[1] in ([4, 5, 6, 7],
                                                         [7, 6, 5, 4])

    interaction_list = [
        [(4, 7), (15, 3)],
        [(4, 7), (3, 15)],
        [(7, 4), (15, 3)],
        [(7, 4), (3, 15)],
    ]
    grid44_manager.clear()
    for inter1, inter2 in interaction_list:
        grid44_manager.clear_paths()
        assert grid44_manager.push_interaction(*inter1)
        assert grid44_manager.push_interaction(*inter2)
        assert grid44_manager.get_all_paths()[1] in ([4, 5, 6, 7],
                                                     [7, 6, 5, 4])


def test_path_container_remove_path(grid44_manager):
    Crossing = _Crossing

    assert grid44_manager.try_add_path([4, 5, 6, 7])
    assert grid44_manager.try_add_path([1, 5, 9, 13])
    assert grid44_manager.try_add_path([8, 9, 10, 11, 15])

    with pytest.raises(KeyError):
        grid44_manager.remove_path_by_id(10)

    grid44_manager.remove_path_by_id(0)
    assert [4, 5, 6, 7] in grid44_manager.get_all_paths()
    assert [1, 5, 9, 13] in grid44_manager.get_all_paths()
    assert grid44_manager.crossings == {
        1: [Crossing(2, [5])],
        2: [Crossing(1, [5])]
    }

    grid44_manager.remove_path_by_id(1)
    assert [[1, 5, 9, 13]] == grid44_manager.get_all_paths()
    assert grid44_manager.crossings == {2: []}

    assert grid44_manager.try_add_path([8, 9, 10, 11, 15])
    assert [1, 5, 9, 13] in grid44_manager.get_all_paths()
    assert [8, 9, 10, 11, 15] in grid44_manager.get_all_paths()
    assert grid44_manager.crossings == {
        2: [Crossing(3, [9])],
        3: [Crossing(2, [9])]
    }


def test_path_container_swap_paths(grid44_manager):
    path_dict = {0: [4, 5, 6, 7], 1: [1, 5, 9, 13], 2: [8, 9, 10, 11, 15]}
    for _, path in path_dict.items():
        assert grid44_manager.try_add_path(path)
        assert path in grid44_manager.get_all_paths()
    path_dict_ref = grid44_manager.paths

    with pytest.raises(KeyError):
        grid44_manager.swap_paths(10, 0)
    with pytest.raises(KeyError):
        grid44_manager.swap_paths(0, 10)

    grid44_manager.swap_paths(0, 1)
    path_dict_ref[0], path_dict_ref[1] = path_dict_ref[1], path_dict_ref[0]
    assert grid44_manager.paths == path_dict_ref

    path_dict[3] = [20, 21, 6, 22, 23, 10, 24, 25]
    assert grid44_manager.try_add_path(path_dict[3])
    assert path_dict[3] in grid44_manager.get_all_paths()
    path_dict_ref = grid44_manager.paths

    grid44_manager.swap_paths(1, 3)
    path_dict_ref[1], path_dict_ref[3] = path_dict_ref[3], path_dict_ref[1]
    assert grid44_manager.paths == path_dict_ref


def test_path_grid44_manager_discard_paths(grid44_manager):
    Crossing = _Crossing
    path_dict = {0: [4, 5, 6, 7], 1: [1, 5, 9, 13], 2: [8, 9, 10, 11, 15]}
    for _, path in path_dict.items():
        assert grid44_manager.try_add_path(path)
        assert path in grid44_manager.get_all_paths()

    path_dict_ref = grid44_manager.paths
    grid44_manager.remove_crossing_of_order_higher_than(1)
    assert grid44_manager.max_crossing_order() == 1
    assert grid44_manager.paths == path_dict_ref
    assert grid44_manager.crossings == {
        0: [Crossing(2, [9])],
        1: [Crossing(2, [5])],
        2: [Crossing(1, [5]), Crossing(0, [9])]
    }

    grid44_manager.remove_crossing_of_order_higher_than(0)
    del path_dict_ref[1]
    assert grid44_manager.max_crossing_order() == 0
    assert grid44_manager.paths == path_dict_ref
    assert grid44_manager.crossings == {0: [], 1: []}


def test_path_container_find_first_order_intersections():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 10), (10, 11), (11, 12), (12,
                                                                        5)])
    graph.add_edges_from([(3, 1), (1, 4)])
    graph.add_edges_from([(5, 6), (6, 7)])
    graph.add_edges_from([(20, 6), (6, 21), (21, 22), (22, 23), (23, 24)])
    graph.add_edges_from([(30, 1), (1, 31), (31, 32)])
    graph.add_edges_from([(40, 23), (23, 41), (41, 42), (42, 43), (43, 44)])

    Crossing = _Crossing
    manager = PathManager(graph=graph, enable_caching=False)

    path_dict = {0: [0, 1, 2, 10, 11, 12], 1: [3, 1, 4], 2: [5, 6, 7]}
    for _, path in path_dict.items():
        assert manager.try_add_path(path)
        assert path in manager.get_all_paths()

    assert manager.crossings == {
        0: [Crossing(1, [1])],
        1: [Crossing(0, [1])],
        2: []
    }
    assert _find_first_order_intersections(manager.crossings,
                                           manager.paths) == {
                                               1: {1}
                                           }

    manager.remove_path_by_id(0)
    del path_dict[0]
    path_dict[3] = [0, 1, 2, 10]
    assert manager.try_add_path(path_dict[3])
    idx1 = manager.get_all_paths().index(path_dict[1]) + 1
    assert _find_first_order_intersections(
        manager.crossings, manager.paths
    ) == {
        1: {idx1},
        # would be 1: {idx1, idx3} if
        # try_add_path was not also
        # trying to solve the
        # intersections while adding the
        # paths
    }

    path_dict[4] = [20, 6, 21, 22, 23, 24]
    assert manager.try_add_path(path_dict[4])
    assert path_dict[4] in manager.get_all_paths()
    idx1 = manager.get_all_paths().index(path_dict[1]) + 1
    idx2 = manager.get_all_paths().index(path_dict[2]) + 1
    assert _find_first_order_intersections(manager.crossings,
                                           manager.paths) == {
                                               1: {idx1},
                                               6: {idx2}
                                           }

    path_dict[5] = [30, 1, 31, 32]
    assert manager.try_add_path(path_dict[5])
    assert path_dict[5] in manager.get_all_paths()
    idx1 = manager.get_all_paths().index(path_dict[1]) + 1
    idx2 = manager.get_all_paths().index(path_dict[2]) + 1
    assert _find_first_order_intersections(manager.crossings,
                                           manager.paths) == {
                                               1: {idx1},
                                               6: {idx2}
                                           }

    path_dict[6] = [40, 23, 41, 42, 43, 44]
    assert manager.try_add_path(path_dict[6])
    assert path_dict[6] in manager.get_all_paths()
    idx1 = manager.get_all_paths().index(path_dict[1]) + 1
    idx2 = manager.get_all_paths().index(path_dict[2]) + 1
    assert _find_first_order_intersections(manager.crossings,
                                           manager.paths) == {
                                               1: {idx1},
                                               6: {idx2}
                                           }


def test_path_container_no_intersection(grid44_manager):
    path_dict = {0: [0, 1, 2, 3], 1: [5, 6, 7], 2: [4, 8, 9, 10, 11]}
    for _, path in path_dict.items():
        assert grid44_manager.try_add_path(path)
        assert path in grid44_manager.get_all_paths()
    assert grid44_manager.generate_swaps() == [(0, 1), (3, 2), (7, 6), (4, 8),
                                               (11, 10), (10, 9)]


def test_path_container_1_intersection_single_intersection():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (3, 1), (1, 4), (2, 10), (10, 11),
                          (11, 12)])

    manager = PathManager(graph=graph)

    #     3
    #     |
    # 0 - 1 - 2
    #     |             10 - 11 - 12
    #     4
    # NB: intersection at node 1
    ref_swaps = [
        [(0, 1), (12, 11)],
        [(0, 1), (10, 11)],
        [(2, 1), (12, 11)],
        [(2, 1), (10, 11)],
        [(3, 1), (12, 11)],
        [(3, 1), (10, 11)],
        [(4, 1), (12, 11)],
        [(4, 1), (10, 11)],
    ]
    paths = [[0, 1, 2], [3, 1, 4]]
    for path1, path2, in itertools.permutations(paths):
        manager.clear()
        assert manager.try_add_path(path1)
        assert not manager.try_add_path(path2)
        assert manager.try_add_path([10, 11, 12])
        assert manager.generate_swaps() in ref_swaps

    #     4
    #     |
    # 0 - 1 - 2 - 3
    #     |             10 - 11 - 12
    #     5
    # NB: intersection at node 1
    ref_swaps = [
        [(0, 1), (1, 2), (4, 1), (12, 11)],
        [(0, 1), (1, 2), (4, 1), (12, 11)],
        [(0, 1), (1, 2), (5, 1), (10, 11)],
        [(0, 1), (1, 2), (5, 1), (12, 11)],
        [(0, 1), (1, 2), (12, 11), (4, 1)],
        [(0, 1), (1, 2), (12, 11), (4, 1)],
        [(0, 1), (1, 2), (10, 11), (5, 1)],
        [(0, 1), (1, 2), (12, 11), (5, 1)],
        [(12, 11), (0, 1), (1, 2), (4, 1)],
        [(12, 11), (0, 1), (1, 2), (4, 1)],
        [(10, 11), (0, 1), (1, 2), (5, 1)],
        [(12, 11), (0, 1), (1, 2), (5, 1)],
    ]
    paths = [[0, 1, 2, 3], [4, 1, 5], [10, 11, 12]]
    for path1, path2, path3 in itertools.permutations(paths):
        manager.clear()
        assert manager.try_add_path(path1)
        assert manager.try_add_path(path2)
        assert manager.try_add_path(path3)
        assert manager.generate_swaps() in ref_swaps

    #         4
    #         |
    # 0 - 1 - 2 - 3
    #         |          10 - 11 - 12
    #         5
    # NB: intersection at node 2
    ref_swaps = [
        [(3, 2), (2, 1), (4, 2), (12, 11)],
        [(3, 2), (2, 1), (4, 2), (12, 11)],
        [(3, 2), (2, 1), (5, 2), (10, 11)],
        [(3, 2), (2, 1), (5, 2), (12, 11)],
        [(3, 2), (2, 1), (12, 11), (4, 2)],
        [(3, 2), (2, 1), (12, 11), (4, 2)],
        [(3, 2), (2, 1), (10, 11), (5, 2)],
        [(3, 2), (2, 1), (12, 11), (5, 2)],
        [(12, 11), (3, 2), (2, 1), (4, 2)],
        [(12, 11), (3, 2), (2, 1), (4, 2)],
        [(10, 11), (3, 2), (2, 1), (5, 2)],
        [(12, 11), (3, 2), (2, 1), (5, 2)],
    ]
    paths = [[0, 1, 2, 3], [4, 2, 5], [10, 11, 12]]
    for path1, path2, path3 in itertools.permutations(paths):
        manager.clear()
        assert manager.try_add_path(path1)
        assert manager.try_add_path(path2)
        assert manager.try_add_path(path3)
        assert manager.generate_swaps() in ref_swaps

    #     9
    #     |
    # 0 - 1 - 2 - 3 - 4 - 5
    #     |
    #    10             6 - 7 - 8
    #     |
    #    11
    # NB: intersection at node 1
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (9, 1),
                          (1, 10), (10, 11), (5, 6), (6, 7), (7, 8)])
    manager = PathManager(graph=graph)
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([9, 1, 10, 11])
    assert manager.try_add_path([6, 7, 8])
    assert manager.generate_swaps() == [(0, 1), (1, 2), (5, 4), (4, 3), (9, 1),
                                        (11, 10), (8, 7)]


def test_path_container_1_intersection_double_crossing_long_right():
    #         6       7
    #         |       |
    # 0 - 1 - 2 - 3 - 4 - 5
    #         |       |
    #         8       9
    #                 |
    #                10
    #                 |
    #                11
    #                 |
    #                12
    # NB: intersection at node 2
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (6, 2), (2,
                                                                           8),
                          (7, 4), (4, 9), (9, 10), (10, 11), (11, 12)])
    manager = PathManager(graph=graph)

    ref_swaps = [(7, 4), (4, 9), (12, 11), (11, 10), (0, 1), (1, 2), (2, 3),
                 (5, 4), (8, 2)]
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([6, 2, 8])
    assert manager.try_add_path([7, 4, 9, 10, 11, 12])
    assert manager.generate_swaps() == ref_swaps

    manager.clear()
    assert manager.try_add_path([6, 2, 8])
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([7, 4, 9, 10, 11, 12])
    assert manager.generate_swaps() == ref_swaps

    ref_swaps = [(5, 4), (4, 3), (3, 2), (2, 1), (7, 4), (4, 9), (12, 11),
                 (11, 10), (8, 2)]
    manager.clear()
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([7, 4, 9, 10, 11, 12])
    assert manager.try_add_path([6, 2, 8])
    assert manager.generate_swaps() == ref_swaps
    manager.clear()
    assert manager.try_add_path([6, 2, 8])
    assert manager.try_add_path([7, 4, 9, 10, 11, 12])
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.generate_swaps() == ref_swaps

    ref_swaps = [(7, 4), (4, 9), (12, 11), (11, 10), (5, 4), (4, 3), (3, 2),
                 (2, 1), (8, 2)]
    manager.clear()
    assert manager.try_add_path([7, 4, 9, 10, 11, 12])
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([6, 2, 8])
    assert manager.generate_swaps() == ref_swaps
    manager.clear()
    assert manager.try_add_path([7, 4, 9, 10, 11, 12])
    assert manager.try_add_path([6, 2, 8])
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.generate_swaps() == ref_swaps


def test_path_container_1_intersection_double_crossing_long_left():
    #     6       7
    #     |       |
    # 0 - 1 - 2 - 3 - 4 - 5
    #     |       |
    #     8       9
    #     |
    #    10
    #     |
    #    11
    #     |
    #    12
    # NB: intersection at node 3
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (6, 1), (1,
                                                                           8),
                          (8, 10), (10, 11), (11, 12), (7, 3), (3, 9)])
    manager = PathManager(graph=graph)

    ref_swaps = [(0, 1), (1, 2), (2, 3), (3, 4), (6, 1), (1, 8), (12, 11),
                 (11, 10), (9, 3)]
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([6, 1, 8, 10, 11, 12])
    assert manager.try_add_path([7, 3, 9])
    assert manager.generate_swaps() == ref_swaps
    manager.clear()
    assert manager.try_add_path([7, 3, 9])
    assert manager.try_add_path([6, 1, 8, 10, 11, 12])
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.generate_swaps() == ref_swaps

    ref_swaps = [(6, 1), (1, 8), (12, 11), (11, 10), (0, 1), (5, 4), (4, 3),
                 (3, 2), (9, 3)]
    manager.clear()
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([7, 3, 9])
    assert manager.try_add_path([6, 1, 8, 10, 11, 12])
    assert manager.generate_swaps() == ref_swaps
    manager.clear()
    assert manager.try_add_path([7, 3, 9])
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([6, 1, 8, 10, 11, 12])
    assert manager.generate_swaps() == ref_swaps

    ref_swaps = [(6, 1), (1, 8), (12, 11), (11, 10), (0, 1), (1, 2), (2, 3),
                 (3, 4), (9, 3)]
    manager.clear()
    assert manager.try_add_path([6, 1, 8, 10, 11, 12])
    assert manager.try_add_path([7, 3, 9])
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.generate_swaps() == ref_swaps
    manager.clear()
    assert manager.try_add_path([6, 1, 8, 10, 11, 12])
    assert manager.try_add_path([0, 1, 2, 3, 4, 5])
    assert manager.try_add_path([7, 3, 9])
    assert manager.generate_swaps() == ref_swaps


def test_path_container_1_intersection_double_crossing_delete_path():
    #     4   5                  4                        5
    #     |   |                  |                        |
    # 0 - 1 - 2 - 3    ->    0 - 1 - 2 - 3   or   0 - 1 - 2 - 3
    #     |   |                  |                        |
    #     6   7                  6                        7
    # NB: intersection at nodes 1 & 2
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (4, 1), (1, 6), (5, 2), (2,
                                                                           7)])
    ref_swaps = [
        [(0, 1), (1, 2), (6, 1)],
        [(0, 1), (1, 2), (4, 1)],
    ]

    manager = PathManager(graph=graph)
    assert manager.try_add_path([0, 1, 2, 3])
    assert manager.try_add_path([4, 1, 6])
    assert not manager.try_add_path([5, 2, 7])
    assert manager.generate_swaps() in ref_swaps

    ref_swaps = [
        [(3, 2), (2, 1), (7, 2)],
        [(3, 2), (2, 1), (5, 2)],
    ]

    manager.clear()
    assert manager.try_add_path([0, 1, 2, 3])
    assert manager.try_add_path([5, 2, 7])
    assert not manager.try_add_path([4, 1, 6])
    assert manager.generate_swaps() in ref_swaps


def test_path_container_1_intersection_double_crossing_delete_path2():
    #     5       6                        6
    #     |       |                        |
    # 0 - 1 - 2 - 3 - 4   ->   0 - 1 - 2 - 3 - 4
    #     |       |                        |
    #     7       8                        8
    # NB: intersection at nodes 1 & 3
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (5, 1), (1, 7), (6,
                                                                           3),
                          (3, 8)])
    manager = PathManager(graph=graph)

    ref_swaps = [
        [(0, 1), (1, 2), (4, 3), (7, 1)],
        [(0, 1), (1, 2), (4, 3), (5, 1)],
        [(0, 1), (4, 3), (3, 2), (8, 3)],
        [(0, 1), (4, 3), (3, 2), (6, 3)],
    ]

    assert manager.try_add_path([0, 1, 2, 3, 4])
    assert manager.try_add_path([5, 1, 7])
    assert not manager.try_add_path([6, 3, 8])
    assert manager.generate_swaps() in ref_swaps

    manager.clear()
    assert manager.try_add_path([0, 1, 2, 3, 4])
    assert manager.try_add_path([6, 3, 8])
    assert not manager.try_add_path([5, 1, 7])
    assert manager.generate_swaps() in ref_swaps


def test_path_container_1_intersection_double_crossing_neighbouring_nodes():
    #     5
    #     |
    #     6   7
    #     |   |
    # 0 - 1 - 2 - 3 - 4
    #     |   |
    #     8   9
    # NB: intersection at nodes 1 & 3
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (5, 6), (6, 1), (1,
                                                                           8),
                          (7, 2), (2, 9)])
    manager = PathManager(graph=graph)

    ref_swaps = [
        [(0, 1), (1, 2), (2, 3), (8, 1), (1, 6), (9, 2)],
        [(0, 1), (1, 2), (2, 3), (5, 6), (8, 1), (9, 2)],
        [(8, 1), (1, 6), (4, 3), (3, 2), (2, 1), (9, 2)],
        [(8, 1), (1, 6), (0, 1), (1, 2), (2, 3), (9, 2)],
        [(0, 1), (1, 2), (2, 3), (8, 1), (1, 6), (7, 2)],
        [(0, 1), (1, 2), (2, 3), (5, 6), (8, 1), (7, 2)],
        [(8, 1), (1, 6), (4, 3), (3, 2), (2, 1), (7, 2)],
        [(8, 1), (1, 6), (0, 1), (1, 2), (2, 3), (7, 2)],
        [(0, 1), (1, 2), (2, 3), (9, 2), (8, 1), (1, 6)],
        [(0, 1), (1, 2), (2, 3), (9, 2), (5, 6), (8, 1)],
        [(8, 1), (1, 6), (4, 3), (9, 2), (3, 2), (2, 1)],
        [(8, 1), (1, 6), (0, 1), (9, 2), (1, 2), (2, 3)],
        [(0, 1), (1, 2), (2, 3), (7, 2), (8, 1), (1, 6)],
        [(0, 1), (1, 2), (2, 3), (7, 2), (5, 6), (8, 1)],
        [(8, 1), (1, 6), (4, 3), (7, 2), (3, 2), (2, 1)],
        [(8, 1), (1, 6), (0, 1), (7, 2), (1, 2), (2, 3)],
    ]

    paths = [[0, 1, 2, 3, 4], [5, 6, 1, 8], [7, 2, 9]]

    for path1, path2, path3 in itertools.permutations(paths):
        manager.clear()
        assert manager.try_add_path(path1)
        assert manager.try_add_path(path2)
        assert manager.try_add_path(path3)
        assert manager.generate_swaps() in ref_swaps


def test_path_container_1_intersection_triple_crossing():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (9, 1),
                          (1, 10), (10, 11), (12, 1), (1, 13), (13, 14),
                          (14, 15), (5, 6), (6, 7), (7, 8)])
    manager = PathManager(graph=graph)

    #      9   13 - 14 - 15
    #      | /
    #  0 - 1 - 2 - 3 - 4 - 5
    #    / |
    # 12  10             6 - 7 - 8
    #      |
    #     11
    # NB: intersection at node 1
    manager.clear()
    paths = [[9, 1, 10, 11], [0, 1, 2, 3, 4, 5], [6, 7, 8],
             [12, 1, 13, 14, 15, 16]]
    for path in paths:
        assert manager.try_add_path(path)

    paths[3], paths[0], paths[1] \
        = paths[0], paths[1], paths[3]
    assert manager.get_all_paths() == paths

    manager.clear()
    paths = [[0, 1, 2, 3, 4, 5], [9, 1, 10, 11], [6, 7, 8],
             [12, 1, 13, 14, 15, 16]]
    for path in paths:
        assert manager.try_add_path(path)

    paths[3], paths[1] \
        = paths[1], paths[3]
    assert manager.get_all_paths() == paths

    #     4   5    10 - 11 - 12    4        10 - 11 - 12
    #     | /                      |
    # 0 - 1 - 2 - 3     ->     0 - 1 - 2 - 3
    #   / |                        |
    # 6   7                        7
    # NB: intersection at node 1
    ref_swaps = [[(0, 1), (1, 2), (4, 1), (12, 11)],
                 [(0, 1), (1, 2), (4, 1), (10, 11)],
                 [(0, 1), (1, 2), (7, 1), (12, 11)],
                 [(0, 1), (1, 2), (7, 1), (10, 11)]]
    manager.clear()
    paths = [[0, 1, 2, 3], [4, 1, 7], [10, 11, 12], [5, 1, 6]]
    assert manager.try_add_path([0, 1, 2, 3])
    assert manager.try_add_path([4, 1, 7])
    assert manager.try_add_path([10, 11, 12])
    assert not manager.try_add_path([5, 1, 6])
    assert manager.generate_swaps() in ref_swaps


def test_path_container_1_intersection_triple_crossing_complex():
    #     4
    #     |
    # 0 - 1 - 2 - 3
    #     |
    # 5 - 6 - 7
    #     |
    #     8
    # NB: intersection at nodes 1 & 3
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (2, 3), (4, 1), (1, 6), (6, 8), (5,
                                                                           6),
                          (6, 7)])
    manager = PathManager(graph=graph)

    ref_swaps = [
        [(0, 1), (1, 2), (4, 1), (8, 6)],
        [(0, 1), (1, 2), (4, 1), (1, 6)],
        [(4, 1), (1, 6), (0, 1), (1, 2)],
        [(0, 1), (3, 2), (4, 1), (1, 6)],
        [(4, 1), (8, 6), (0, 1), (3, 2)],
        [(4, 1), (1, 6), (0, 1), (3, 2)],
    ]

    assert manager.try_add_path([0, 1, 2, 3])
    assert manager.try_add_path([4, 1, 6, 8])
    assert not manager.try_add_path([5, 6, 7])
    assert manager.generate_swaps() in ref_swaps

    manager.clear()
    assert manager.try_add_path([4, 1, 6, 8])
    assert manager.try_add_path([0, 1, 2, 3])
    assert not manager.try_add_path([5, 6, 7])
    assert manager.generate_swaps() in ref_swaps

    ref_swaps = [
        [(0, 1), (1, 2), (8, 6), (6, 1), (5, 6)],
        [(0, 1), (1, 2), (8, 6), (6, 1), (7, 6)],
    ]

    manager.clear()
    assert manager.try_add_path([4, 1, 6, 8])
    assert manager.try_add_path([5, 6, 7])
    assert manager.try_add_path([0, 1, 2, 3])
    assert manager.generate_swaps() in ref_swaps

    manager.clear()
    assert manager.try_add_path([0, 1, 2, 3])
    assert manager.try_add_path([5, 6, 7])

    # With some modification to PathManager, this next line could be made not
    # to fail adding the path.
    # This would require the intersection resolving algorithm to allow the
    # creation of a new intersection for the path currently being added but not
    # for any other stored path.
    # (ie. allowing the [4], [1, 6, 8] path split, although now 1 is an
    # intersection for the new path)
    assert not manager.try_add_path([4, 1, 6, 8])
