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
"""Tests for projectq.cengines._graph_path_container.py."""
import pytest
from projectq.cengines._graph_path_container import PathContainer, _find_first_order_intersections


def test_path_container_crossing_class():
    Crossing = PathContainer._Crossing
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


def test_path_container_has_interaction():
    container = PathContainer()

    path_dict = {0: [4, 5, 6, 7], 1: [1, 5, 9, 13], 2: [8, 9, 10, 11, 15]}
    container.paths = path_dict

    assert container.has_interaction(4, 7)
    assert container.has_interaction(7, 4)
    assert container.has_interaction(8, 15)
    assert container.has_interaction(15, 8)
    assert not container.has_interaction(4, 8)
    assert not container.has_interaction(8, 4)


def test_path_container_add_path():
    Crossing = PathContainer._Crossing
    container = PathContainer()

    assert container.try_add_path([4, 5, 6, 7])
    assert container.paths == {0: [4, 5, 6, 7]}
    assert container.crossings == {0: []}

    assert not container.try_add_path([4, 8, 12])
    assert not container.try_add_path([0, 1, 2, 3, 7])
    assert not container.try_add_path([1, 5, 6, 10])
    assert container.paths == {0: [4, 5, 6, 7]}
    assert container.crossings == {0: []}

    assert container.try_add_path([1, 5, 9, 13])
    assert container.paths == {0: [4, 5, 6, 7], 1: [1, 5, 9, 13]}
    assert container.crossings == {
        0: [Crossing(1, [5])],
        1: [Crossing(0, [5])]
    }

    assert container.try_add_path([10, 6, 9, 14])
    assert container.paths == {
        0: [4, 5, 6, 7],
        1: [1, 5, 9, 13],
        2: [10, 6, 9, 14]
    }
    assert container.crossings == {
        0: [Crossing(1, [5]), Crossing(2, [6])],
        1: [Crossing(0, [5]), Crossing(2, [9])],
        2: [Crossing(0, [6]), Crossing(1, [9])],
    }


def test_path_container_remove_path():
    Crossing = PathContainer._Crossing
    container = PathContainer()
    assert container.try_add_path([4, 5, 6, 7])
    assert container.try_add_path([1, 5, 9, 13])
    assert container.try_add_path([8, 9, 10, 11, 15])

    with pytest.raises(KeyError):
        container.remove_path_by_id(10)

    container.remove_path_by_id(2)
    assert container.paths == {0: [4, 5, 6, 7], 1: [1, 5, 9, 13]}
    assert container.crossings == {
        0: [Crossing(1, [5])],
        1: [Crossing(0, [5])]
    }

    container.remove_path_by_id(0)
    assert container.paths == {1: [1, 5, 9, 13]}
    assert container.crossings == {1: []}

    assert container.try_add_path([8, 9, 10, 11, 15])
    assert container.paths == {1: [1, 5, 9, 13], 3: [8, 9, 10, 11, 15]}
    assert container.crossings == {
        1: [Crossing(3, [9])],
        3: [Crossing(1, [9])]
    }


def test_path_container_swap_paths():
    Crossing = PathContainer._Crossing
    container = PathContainer()

    path_dict = {0: [4, 5, 6, 7], 1: [1, 5, 9, 13], 2: [8, 9, 10, 11, 15]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict

    with pytest.raises(KeyError):
        container.swap_paths(10, 0)
    with pytest.raises(KeyError):
        container.swap_paths(0, 10)

    container.swap_paths(0, 1)
    path_dict[0], path_dict[1] = path_dict[1], path_dict[0]
    assert container.paths == path_dict
    assert container.crossings == {
        0: [Crossing(1, [5]), Crossing(2, [9])],
        1: [Crossing(0, [5])],
        2: [Crossing(0, [9])]
    }

    path_dict[3] = [20, 21, 6, 22, 23, 10, 24, 25]
    assert container.try_add_path(path_dict[3])

    assert container.paths == path_dict
    assert container.crossings == {
        0: [Crossing(1, [5]), Crossing(2, [9])],
        1: [Crossing(0, [5]), Crossing(3, [6])],
        2: [Crossing(0, [9]), Crossing(3, [10])],
        3: [Crossing(1, [6]), Crossing(2, [10])]
    }

    container.swap_paths(1, 3)
    path_dict[1], path_dict[3] = path_dict[3], path_dict[1]
    assert container.paths == path_dict

    assert container.crossings == {
        0: [Crossing(3, [5]), Crossing(2, [9])],
        1: [Crossing(3, [6]), Crossing(2, [10])],
        2: [Crossing(0, [9]), Crossing(1, [10])],
        3: [Crossing(0, [5]), Crossing(1, [6])]
    }


def test_path_container_clear():
    container = PathContainer()
    assert container.try_add_path([4, 5, 6, 7])
    assert container.try_add_path([1, 5, 9, 13])
    assert container.try_add_path([8, 9, 10, 11, 15])

    assert container.paths
    assert container.crossings

    container.clear()
    assert not container.paths
    assert not container.crossings


def test_path_container_max_order():
    container = PathContainer()
    assert container.max_crossing_order() == 0

    assert container.try_add_path([4, 5, 6, 7])
    assert container.max_crossing_order() == 0

    assert container.try_add_path([1, 5, 9, 13])
    assert container.max_crossing_order() == 1


def test_path_container_discard_paths():
    Crossing = PathContainer._Crossing
    container = PathContainer()
    path_dict = {0: [4, 5, 6, 7], 1: [1, 5, 9, 13], 2: [8, 9, 10, 11, 15]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict

    container.remove_crossing_of_order_higher_than(1)
    assert container.max_crossing_order() == 1
    assert container.paths == path_dict
    assert container.crossings == {
        0: [Crossing(1, [5])],
        1: [Crossing(0, [5]), Crossing(2, [9])],
        2: [Crossing(1, [9])]
    }

    container.remove_crossing_of_order_higher_than(0)
    del path_dict[1]
    assert container.max_crossing_order() == 0
    assert container.paths == path_dict
    assert container.crossings == {0: [], 2: []}


def test_path_container_get_path_data():
    container = PathContainer()
    path_dict = {0: [4, 5, 6, 7], 1: [1, 5, 9, 13], 2: [8, 9, 10, 11, 15]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)

    assert container.get_all_paths() == [[4, 5, 6, 7], [1, 5, 9, 13],
                                         [8, 9, 10, 11, 15]]
    assert container.get_all_nodes() == set(
        [1, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15])


def test_path_container_find_first_order_intersections():
    Crossing = PathContainer._Crossing
    container = PathContainer()

    path_dict = {0: [0, 1, 2, 10, 11, 12], 1: [3, 1, 4], 2: [5, 6, 7]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict

    assert container.crossings == {
        0: [Crossing(1, [1])],
        1: [Crossing(0, [1])],
        2: []
    }
    assert _find_first_order_intersections(container.crossings,
                                           container._split_paths()) == {
                                               1: {1}
                                           }

    container.remove_path_by_id(0)
    del path_dict[0]
    path_dict[3] = [0, 1, 2, 10]
    assert container.try_add_path(path_dict[3])
    assert container.paths == path_dict
    assert _find_first_order_intersections(container.crossings,
                                           container._split_paths()) == {
                                               1: {1, 3},
                                           }

    path_dict[4] = [11, 6, 12, 14, 15, 16]
    assert container.try_add_path(path_dict[4])
    assert container.paths == path_dict
    assert _find_first_order_intersections(container.crossings,
                                           container._split_paths()) == {
                                               1: {1, 3},
                                               6: {2}
                                           }

    path_dict[5] = [21, 1, 22, 24, 25, 26]
    assert container.try_add_path(path_dict[5])
    assert container.paths == path_dict
    assert _find_first_order_intersections(container.crossings,
                                           container._split_paths()) == {
                                               1: {1, 3},
                                               6: {2}
                                           }

    path_dict[6] = [30, 15, 32, 33, 34, 35]
    assert container.try_add_path(path_dict[6])
    assert container.paths == path_dict
    assert _find_first_order_intersections(container.crossings,
                                           container._split_paths()) == {
                                               1: {1, 3},
                                               6: {2}
                                               # The 15 node should not appear
                                           }


def test_path_container_no_intersection():
    container = PathContainer()
    path_dict = {0: [0, 1, 2, 3], 1: [4, 5, 6], 2: [7, 8, 9, 10, 11]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(0, 1), (3, 2), (6, 5), (7, 8),
                                          (11, 10), (10, 9)]
    assert container.paths == path_dict


def test_path_container_1_intersection_single_intersection():
    container = PathContainer()

    #     3
    #     |
    # 0 - 1 - 2
    #     |             10 - 11 - 12
    #     4
    # NB: intersection at node 1
    path_dict = {0: [0, 1, 2], 1: [3, 1, 4], 2: [10, 11, 12]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(2, 1), (12, 11)]
    # Make sure that path 1 gets deleted or we risk running an infinite loop
    del path_dict[1]
    assert container.paths == path_dict

    #     4
    #     |
    # 0 - 1 - 2 - 3
    #     |             10 - 11 - 12
    #     5
    # NB: intersection at node 1
    container.clear()
    path_dict = {0: [0, 1, 2, 3], 1: [4, 1, 5], 2: [10, 11, 12]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(0, 1), (1, 2), (5, 1), (12, 11)]

    #     4
    #     |
    # 0 - 1 - 2 - 3
    #     |             10 - 11 - 12
    #     5
    # NB: intersection at node 1
    container.clear()
    path_dict = {0: [4, 1, 5], 1: [0, 1, 2, 3], 2: [10, 11, 12]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(0, 1), (1, 2), (5, 1), (12, 11)]

    #         4
    #         |
    # 0 - 1 - 2 - 3
    #         |          10 - 11 - 12
    #         5
    # NB: intersection at node 2
    container.clear()
    path_dict = {0: [0, 1, 2, 3], 1: [4, 2, 5], 2: [10, 11, 12]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(3, 2), (2, 1), (5, 2), (12, 11)]

    #     9
    #     |
    # 0 - 1 - 2 - 3 - 4 - 5
    #     |
    #    10             6 - 7 - 8
    #     |
    #    11
    # NB: intersection at node 1
    container.clear()
    path_dict = {0: [9, 1, 10, 11], 1: [0, 1, 2, 3, 4, 5], 2: [6, 7, 8]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict

    container.generate_swaps()
    path_dict[0], path_dict[1] = path_dict[1], path_dict[0]
    assert container.paths == path_dict


def test_path_container_1_intersection_double_crossing():
    container = PathContainer()

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
    container.clear()
    path_dict = {0: [0, 1, 2, 3, 4, 5], 1: [6, 2, 8], 2: [7, 4, 9, 10, 11, 12]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(5, 4), (4, 3), (3, 2), (2, 1), (8,
                                                                           2),
                                          (7, 4), (4, 9), (12, 11), (11, 10)]

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
    container.clear()
    path_dict = {0: [0, 1, 2, 3, 4, 5], 1: [7, 3, 9], 2: [6, 1, 8, 10, 11, 12]}

    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(0, 1), (1, 2), (2, 3), (3, 4), (9,
                                                                           3),
                                          (6, 1), (1, 8), (12, 11), (11, 10)]

    #     4   5                  4                        5
    #     |   |                  |                        |
    # 0 - 1 - 2 - 3    ->    0 - 1 - 2 - 3   or   0 - 1 - 2 - 3
    #     |   |                  |                        |
    #     6   7                  6                        7
    # NB: intersection at nodes 1 & 2
    container.clear()
    path_dict = {
        0: [0, 1, 2, 3],
        1: [4, 1, 6],
        2: [5, 2, 7],
    }
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    swaps = container.generate_swaps()
    assert swaps == [(0, 1), (1, 2), (6, 1)] \
        or swaps == [(3, 2), (2, 1), (7, 2)]
    assert container.paths[0] == path_dict[0]
    assert (1 in container.paths and container.paths[1] == path_dict[1]) \
        + (2 in container.paths and container.paths[2] == path_dict[2]) == 1

    #     5       6                        6
    #     |       |                        |
    # 0 - 1 - 2 - 3 - 4   ->   0 - 1 - 2 - 3 - 4
    #     |       |                        |
    #     7       8                        8
    # NB: intersection at nodes 1 & 3
    container.clear()
    path_dict = {
        0: [0, 1, 2, 3, 4],
        1: [5, 1, 7],
        2: [6, 3, 8],
    }
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    swaps = container.generate_swaps()
    assert container.generate_swaps() == [(0, 1), (4, 3), (3, 2), (8, 3)]
    del path_dict[1]
    assert container.paths == path_dict

    #     5
    #     |
    #     6   7
    #     |   |
    # 0 - 1 - 2 - 3 - 4
    #     |   |
    #     8   9
    # NB: intersection at nodes 1 & 3
    container.clear()
    path_dict = {
        0: [0, 1, 2, 3, 4],
        1: [5, 6, 1, 8],
        2: [7, 2, 9],
    }
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(0, 1), (1, 2), (2, 3), (5, 6), (8,
                                                                           1),
                                          (9, 2)]
    assert container.paths == path_dict


def test_path_container_1_intersection_triple_crossing():
    container = PathContainer()

    #      9   13 - 14 - 15
    #      | /
    #  0 - 1 - 2 - 3 - 4 - 5
    #    / |
    # 12  10             6 - 7 - 8
    #      |
    #     11
    # NB: intersection at node 1
    container.clear()
    path_dict = {
        0: [9, 1, 10, 11],
        1: [0, 1, 2, 3, 4, 5],
        2: [6, 7, 8],
        3: [12, 1, 13, 14, 15, 16]
    }
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict

    container.generate_swaps()
    path_dict[1], path_dict[3], path_dict[0] \
        = path_dict[0], path_dict[1], path_dict[3]
    assert container.paths == path_dict

    #     6       7   8                6           8
    #     |       |   |                |           |
    # 0 - 1 - 2 - 3 - 4 - 5   ->   0 - 1 - 2 - 3 - 4 - 5
    #     |       |   |                |           |
    #     9      10  11                8          10
    #     |           |                |           |
    #    12          13               12          13
    #     |           |                |           |
    #    14          15               14          15
    #     |           |                |           |
    #    16          17               16          17
    # NB: intersection at node 3
    container.clear()
    path_dict = {
        0: [0, 1, 2, 3, 4, 5],
        1: [6, 1, 9, 12, 14, 16],
        2: [7, 3, 10],
        3: [8, 4, 11, 13, 15, 17]
    }
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(0, 1), (1, 2), (5, 4), (4, 3), (6,
                                                                           1),
                                          (1, 9), (16, 14), (14, 12), (8, 4),
                                          (4, 11), (17, 15), (15, 13)]
    del path_dict[2]
    assert container.paths == path_dict

    #     4   5    10 - 11 - 12    4        10 - 11 - 12
    #     | /                      |
    # 0 - 1 - 2 - 3     ->     0 - 1 - 2 - 3
    #   / |                        |
    # 6   7                        7
    # NB: intersection at node 1
    container.clear()
    path_dict = {0: [0, 1, 2, 3], 1: [4, 1, 7], 2: [10, 11, 12], 3: [5, 1, 6]}
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict
    assert container.generate_swaps() == [(0, 1), (1, 2), (7, 1), (12, 11)]


@pytest.mark.xfail
def test_path_container_1_intersection_triple_crossing_complex():
    container = PathContainer()
    #     4
    #     |
    # 0 - 1 - 2 - 3
    #     |
    # 5 - 6 - 7
    #     |
    #     8
    # NB: intersection at nodes 1 & 3
    container.clear()
    path_dict = {
        0: [0, 1, 2, 3],
        1: [4, 1, 6, 8],
        2: [5, 6, 7],
    }
    for _, path in path_dict.items():
        assert container.try_add_path(path)
    assert container.paths == path_dict

    # Ideally this situation should be solved without deleting any paths
    assert container.generate_swaps() == [(0, 1), (1, 2), (8, 6), (6, 1), (7,
                                                                           6)]
    path_dict[1], path_dict[2] = path_dict[2], path_dict[1]
    assert container.paths == path_dict
