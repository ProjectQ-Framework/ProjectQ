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
This is a helper module for the _graphmapper.GraphMapper class.

Its main goal is to provide classes and functions to manage paths through an
arbitrary graph and eventually generate a list of swap operations to perform as
many paths as possible, by either solving conflicts (ie. crossing points and
intersections; see definitions below) or discarding paths.

Note that when generating a list of swap operations for a particular path, the
path is usually splitted into two halves in order to maximize the number of
swap operations that can be performed simultaneously.

In the context of this module, a distinction is made between a crossing point
and an intersection.

A crossing point is just as its name implies a point or node of the graph that
simultaneously belongs to one or more paths. On the other hand, an intersection
is defined as a particular crossing point of a path for which one of the
splitted sub-path halves has an endpoint. This means that a path may have at
most two intersections

This is best exemplified by some examples:

    Given the path [0, 1, 2, 3], a possible split to maximize simultaneous
    swapping operations would be:
         [[0, 1], [2, 3]] where 1 or 2 may be intersections.

    Given the path [0, 1, 2, 3, 4], possible splits would include:
         [[0, 1, 2], [3, 4]] where 2 or 3 could be intersections if they are
                             crossings
         [[0, 1], [2, 3, 4]] where 1 or 2 could be intersections if they are
                             crossings
"""

import itertools
import networkx as nx

# ==============================================================================


def _find_first_order_intersections(crossings, split_paths):
    """
    Find out which crossing nodes are intersections.

    A crossing point is considered an intersection if and only if either:
      - the end of sub-path 1 is the crossing point
      - the beginning of sub-path 2 is the crossing point

    Args:
        crossings (dict) : Dictionary containing the list of all crossing
                           points indexed by the path ID
        split_paths (dict) : Dictionary containing the two halves of each paths
                             indexed by the path ID

    Returns:
        intersections (dict) : Dictionary indexed by the intersection node
                               containing the IDs of the paths for which that
                               particular node is considered an intersection
    """
    intersections = {}

    for path_id, (subpath1, subpath2) in split_paths.items():
        for crossing in crossings[path_id]:
            if crossing.overlap[0] in (subpath1[-1], subpath2[0]):
                if crossing.overlap[0] not in intersections:
                    intersections[crossing.overlap[0]] = set((path_id, ))
                else:
                    intersections[crossing.overlap[0]].add(path_id)

    return intersections


def _try_solve_intersection(intersection_node, subpath1, subpath2,
                            subpath1_not_crossing, subpath2_not_crossing):
    """
    Attempt to solve a first order intersection by modifying sub-paths.

    Args:
        intersection_node (int) : Intersection node
        subpath1 (list) : First half of the path
        subpath2 (list) : Second half of the path
        subpath1_not_crossing (list) : Helper list of booleans indicating
                                       whether the nodes of the first subpath
                                       are crossing or not
        subpath2_not_crossing (list) : Helper list of booleans indicating
                                       whether the nodes of the second subpath
                                       are crossing or not

    Note:
        subpath1*, subpath2* arguments are modified in-place

    Returns:
        True/False depending on whether the intersection could be solved or not
    """
    if len(subpath1) + len(subpath2) < 4:
        return False

    if subpath1[-1] == intersection_node:
        # Try moving the head of subpath2 to subpath1
        if len(subpath2) > 1 \
           and subpath2_not_crossing[0] \
           and subpath2_not_crossing[1]:
            subpath1.append(subpath2[0])
            subpath1_not_crossing.append(subpath2_not_crossing[0])
            del subpath2[0]
            del subpath2_not_crossing[0]
            return True
    else:
        # Try moving the tail of subpath1 to subpath2
        if len(subpath1) > 1 \
           and subpath1_not_crossing[-1] \
           and subpath1_not_crossing[-2]:
            subpath2.insert(0, subpath1.pop())
            subpath2_not_crossing.insert(0, subpath1_not_crossing.pop())
            return True

    # Try moving the last two elements of subpath1 to subpath2
    if len(subpath1) > 2 \
       and subpath1_not_crossing[-2] \
       and subpath1_not_crossing[-3]:
        subpath2.insert(0, subpath1.pop())
        subpath2.insert(0, subpath1.pop())
        subpath2_not_crossing.insert(0, subpath1_not_crossing.pop())
        subpath2_not_crossing.insert(0, subpath1_not_crossing.pop())
        return True

    # Try moving the first two elements of subpath2 to subpath1
    if len(subpath2) > 2 \
       and subpath2_not_crossing[1] \
       and subpath2_not_crossing[2]:
        subpath1.append(subpath2[0])
        subpath1.append(subpath2[1])
        subpath1_not_crossing.append(subpath2_not_crossing[0])
        subpath1_not_crossing.append(subpath2_not_crossing[1])
        del subpath2[:2]
        del subpath2_not_crossing[:2]
        return True

    return False


def _return_swaps(split_paths):
    """
    Return a list of swap operations given a list of path halves

    Args:
        split_paths (dict): Dictionary indexed by path ID containing 2-tuples
                            of path halves

    Returns: A list of swap operations (2-tuples)
    """
    swap_operations = []

    for path_id in sorted(split_paths):
        path = split_paths[path_id]
        swap_operations.append([])
        # Add swaps operations for first half of the path
        for prev, cur in zip(path[0], path[0][1:]):
            swap_operations[-1].append((prev, cur))

        # Add swaps operations for the second half of the path
        for prev, cur in zip(path[1][::-1], path[1][-2::-1]):
            swap_operations[-1].append((prev, cur))

    return swap_operations


# ==============================================================================


class PathCacheExhaustive():
    """
    Class acting as cache for optimal paths through the graph.
    """

    def __init__(self, path_length_threshold):
        self._path_length_threshold = path_length_threshold
        self._cache = {}
        self.key_type = frozenset

    def __str__(self):
        ret = ""
        for (node0, node1), path in self._cache.items():
            ret += "{}: {}\n".format(sorted([node0, node1]), path)
        return ret

    def empty_cache(self):
        """Empty the cache."""
        self._cache = {}

    def get_path(self, start, end):
        """
        Return a path from the cache.

        Args:
            start (object): Start node for the path
            end (object): End node for the path

        Returns: Optimal path stored in cache

        Raises: KeyError if path is not present in the cache
        """
        return self._cache[self.key_type((start, end))]

    def has_path(self, start, end):
        """
        Test whether a path connecting start to end is present in the cache.

        Args:
            start (object): Start node for the path
            end (object): End node for the path

        Returns: True/False
        """
        return self.key_type((start, end)) in self._cache

    def add_path(self, path):
        """
        Add a path to the cache.

        This method also recursively adds all the subpaths that are at least
        self._path_length_threshold long to the cache.

        Args:
            path (list): Path to store inside the cache
        """
        length = len(path)
        for start in range(length - self._path_length_threshold + 1):
            node0 = path[start]
            for incr in range(length - start - 1,
                              self._path_length_threshold - 2, -1):
                end = start + incr
                self._cache[self.key_type((node0,
                                           path[end]))] = path[start:end + 1]


# ==============================================================================


class _Crossing:
    __slots__ = ['path_id', 'overlap']

    def __init__(self, path_id, overlap):
        self.path_id, self.overlap = path_id, overlap

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.path_id, self.overlap) == (other.path_id,
                                                    other.overlap)
        if isinstance(other, list):
            return self.overlap == other
        if isinstance(other, int):
            return self.overlap[0] == other
        raise NotImplementedError("Invalid comparison")

    def __str__(self):
        return '{} {}'.format(self.path_id, self.overlap)

    def __repr__(self):
        return 'Crossing({}, {})'.format(self.path_id, self.overlap)


class PathManager:
    """
    Class managing interactions between distant qubits on an arbitrary graph.

    This class essentially manages paths through an arbitrary graph, handling
    possible intersections between multiple paths through an arbitrary graph by
    resolving conflict points such as crossings and intersections.

    Attributes:
        crossings (dict) : dictionary of crossing points indexed by path ID
        cache (PathCacheExhaustive) : cache manager
        enable_caching (bool): indicates whether caching is enabled or not
        graph (networkx.Graph): Arbitrary connected graph
        paths (dict) : list of paths currently held by a path container indexed
                       by a unique ID
        paths_stats (dict) : dictionary for storing statistics indexed by
                             interactions (frozenset of pairs of qubits)
    """

    def __init__(self, graph, enable_caching=True):
        """
        Args:
            graph (networkx.Graph): an arbitrary connected graph
            enable_caching (bool): Controls whether path caching is enabled
        """
        # Make sure that we start with a valid graph
        if not nx.is_connected(graph):
            raise RuntimeError("Input graph must be a connected graph")
        elif not all([isinstance(n, int) for n in graph]):
            raise RuntimeError(
                "All nodes inside the graph needs to be integers")
        else:
            self.graph = graph

        self.paths = {}
        self.crossings = {}
        self._path_id = 0

        self.enable_caching = enable_caching
        # Path cache support
        path_length_threshold = 3
        self.cache = PathCacheExhaustive(path_length_threshold)

        # Statistics
        self.paths_stats = dict()

    #################################################################
    # Methods querying information about the state of the container #
    #################################################################

    def get_all_nodes(self):
        """
        Return a list of all nodes that are part of some path.

        Returns:
            A set of nodes that are part of at least one path.
        """
        all_nodes = []
        for row in self.paths.values():
            all_nodes.extend(row[0])
            all_nodes.extend(row[1])
        return set(all_nodes)

    def get_all_paths(self):
        """
        Return a list of all the path contained in the container.

        Returns:
            A list of paths (list of list of ints)
        """
        return [
            self.paths[k][0] + self.paths[k][1] for k in sorted(self.paths)
        ]

    def has_interaction(self, node0, node1):
        """
        Check if a path within the container already generate an interaction

        Args:
            node0 (int) : An endnode of a path
            node1 (int) : An endnode of a path

        Returns:
            True or False depending on whether the container has a path linking
            node0 to node1
        """
        for path in self.paths.values():
            if frozenset((node0, node1)) == frozenset((path[0][0],
                                                       path[1][-1])):
                return True
        return False

    def max_crossing_order(self):
        """
        Return the order of the largest crossing.

        The order of a crossing is defined as the number of paths that
        intersect

        Returns:
            An int
        """
        crossing_orders = list(
            itertools.chain.from_iterable(
                [[len(c.overlap) for c in crossing]
                 for crossing in self.crossings.values()]))
        if crossing_orders:
            return max(crossing_orders)
        return 0

    ######################################################
    # Methods for resetting the content of the container #
    ######################################################

    def clear_paths(self):
        """
        Reset the list of paths managed by this instance.

        Note:
            Does not reset path statistics or the state of the cache.
        """
        self.paths.clear()
        self.crossings.clear()

    def clear(self):
        """
        Completely reset the state of this instance.

        Note:
            Both path statistics and cache are also reset
        """
        self.clear_paths()
        self.paths_stats.clear()
        self.cache.empty_cache()

    #############################################################
    # Entry point for the mapper to extract the final path list #
    #############################################################

    def generate_swaps(self):
        """
        Generate a list of swaps to execute as many paths as possible.

        Returns:
            A list of swap operations (tuples)
        """

        self._solve_first_order_intersections(
            _find_first_order_intersections(self.crossings, self.paths))

        # By this point, we should have solved all intersections
        return list(itertools.chain.from_iterable(_return_swaps(self.paths)))

    #############################################
    # Methods for adding paths to the container #
    #############################################

    def push_interaction(self, node0, node1):
        """
        Plan an interaction between two qubit.

        Args:
            node0 (int) : backend id of the first qubit
            node1 (int) : backend id of the second qubit

        Returns:
            True if the path could be added to the container, False otherwise
        """

        # TODO: think about merging paths
        # TODO: maybe apply gates in the middle of the swaps

        interaction = frozenset((node0, node1))
        if self.has_interaction(node0, node1):
            self.paths_stats[interaction] += 1
            return True

        if not self.graph.has_edge(node0, node1):
            new_path = self._calculate_path(node0, node1)
        else:
            new_path = None

        if new_path:
            if not self.try_add_path(new_path) \
               and not self._try_alternative_paths(node0, node1):
                return False
        else:
            # Prevent adding a new path if it contains some already interacting
            # qubits
            for path in self.paths.values():
                if path[0][0] in (node0, node1) or path[1][-1] in (node0,
                                                                   node1):
                    return False

        if interaction not in self.paths_stats:
            self.paths_stats[interaction] = 1
        else:
            self.paths_stats[interaction] += 1
        return True

    def try_add_path(self, new_path):
        """
        Try adding a path to the path container.

        Args:
            new_path (list) : path to add to the container

        Returns:
            True if the path could be added to the container, False otherwise
        """
        # Prevent adding a new path if it contains some already interacting
        # qubits
        for path in self.paths.values():
            if path[0][0] in new_path or path[1][-1] in new_path:
                return False

        # Make sure each node appears only once
        if len(new_path) != len(set(new_path)):
            return False

        idx = len(new_path) >> 1
        new_subpath0, new_subpath1 = new_path[:idx], new_path[idx:]
        new_intersections = {}
        new_crossings = []
        for idx, (subpath0, subpath1) in self.paths.items():
            path_overlap = [
                node for node in new_path
                if node in subpath0 or node in subpath1
            ]
            if len(path_overlap) > 1:
                return False
            if len(path_overlap) == 1:
                new_crossings.append(_Crossing(idx, path_overlap))

                # Is this crossing point an intersection for the new path?
                if new_subpath0[-1] in path_overlap \
                   or new_subpath1[0] in path_overlap:
                    if path_overlap[0] not in new_intersections:
                        new_intersections[path_overlap[0]] = set(
                            (self._path_id, ))
                    else:
                        new_intersections[path_overlap[0]].add(self._path_id)

                # Is this crossing point an intersection for the other path?
                subpath0, subpath1 = self.paths[idx]
                if subpath0[-1] in path_overlap \
                   or subpath1[0] in path_overlap:
                    if path_overlap[0] not in new_intersections:
                        new_intersections[path_overlap[0]] = set((idx, ))
                    else:
                        new_intersections[path_overlap[0]].add(idx)

        self.paths[self._path_id] = (new_subpath0, new_subpath1)
        self.crossings[self._path_id] = new_crossings
        for crossing in new_crossings:
            path_id = crossing.path_id
            self.crossings[path_id].append(
                _Crossing(self._path_id, crossing.overlap))

        # Remove the entries where only the new path is present, as the
        # solution in those cases is to execute the new path after the other
        # paths, which is going to happen anyway as the new path is appended to
        # the list of paths
        new_intersections = {
            node: path_ids
            for node, path_ids in new_intersections.items()
            if len(path_ids) > 1 or self._path_id not in path_ids
        }

        if new_intersections:
            self._solve_first_order_intersections(new_intersections)

        if self._path_id not in self.paths:
            return False

        self._path_id += 1
        return True

    #############################################
    # Methods for adding paths to the container #
    #############################################

    def remove_path_by_id(self, path_id):
        """
        Remove a path from the path container given its ID.

        Args:
            path_id (int) : ID of path to remove

        Raises:
            KeyError if path_id is not valid
        """
        if path_id not in self.paths:
            raise KeyError(path_id)
        self.crossings = {
            k: [i for i in v if i.path_id != path_id]
            for k, v in self.crossings.items() if k != path_id
        }
        del self.paths[path_id]

    def remove_crossing_of_order_higher_than(self, order):
        """
        Remove paths that have crossings with order above a certain threshold.

        Args:
            order (int) : Maximum allowed order of crossing
        """
        number_of_crossings_per_path = {
            path_id: len([c for c in crossing if len(c.overlap) > order])
            for path_id, crossing in self.crossings.items()
        }

        path_id_list = [
            x for y, x in sorted(
                zip(number_of_crossings_per_path.values(),
                    number_of_crossings_per_path.keys())) if y
        ]

        while path_id_list and self.max_crossing_order() > order:
            path_id = path_id_list.pop()
            self.remove_path_by_id(path_id)

    def swap_paths(self, path_id1, path_id2):
        """
        Swap two path within the path container.

        Args:
            path_id1 (int) : ID of first path
            path_id2 (int) : ID of second path
        """

        if path_id1 not in self.paths:
            raise KeyError(path_id1)
        if path_id2 not in self.paths:
            raise KeyError(path_id2)

        for crossing_list in self.crossings.values():
            for crossing in crossing_list:
                if path_id1 == crossing.path_id:
                    crossing.path_id = path_id2
                elif path_id2 == crossing.path_id:
                    crossing.path_id = path_id1

        self.crossings[path_id2], self.crossings[path_id1] = self.crossings[
            path_id1], self.crossings[path_id2]
        self.paths[path_id2], self.paths[path_id1] = self.paths[
            path_id1], self.paths[path_id2]

    ##########################
    # Private helper methods #
    ##########################

    def _solve_first_order_intersections(self, intersections):
        """
        Solve all first order intersections.

        The intersections may be "solved" in two different manners:
          - Sub-path split are modified to transform intersections in simple
            crossings
          - Paths are removed from the container

        Pre-conditions:
            self.max_crossing_order() == 1

        Args:
            intersections (dict): TODO
        """

        # Get a list of the intersection nodes sorted by intersection order and
        # total number of points of all paths for that particular intersection
        def intersection_sort(crossing):
            order = len(crossing[0])
            number_of_points = sum([
                len(self.paths[path_id][0]) + len(self.paths[path_id][1])
                for path_id in crossing[0]
            ]) - order + 1
            return (order, number_of_points)

        intersection_node_list = [
            x for _, x in sorted(
                zip(intersections.values(), intersections.keys()),
                key=intersection_sort)
        ]

        # and process them
        while intersection_node_list:
            intersection_node = intersection_node_list[-1]
            node_is_not_crossing = {
                path_id: ([
                    node not in self.crossings[path_id]
                    for node in self.paths[path_id][0]
                ], [
                    node not in self.crossings[path_id]
                    for node in self.paths[path_id][1]
                ])
                for path_id in intersections[intersection_node]
            }

            if len(intersections[intersection_node]) == 1:
                # This crossing is an intersection only for one path
                # -> only need to make sure that the other paths gets
                #    processed first when generating the swaps
                path_id = list(intersections[intersection_node])[0]

                for crossing in self.crossings[path_id]:
                    if crossing.overlap[0] == intersection_node:
                        other_path_id = crossing.path_id
                        if path_id < other_path_id:
                            self.swap_paths(path_id, other_path_id)
                del intersections[intersection_node]
                del intersection_node_list[-1]
            else:
                # This crossing is an intersection for multiple paths
                #   -> find all paths concerned with this crossing
                path_id_list = [
                    x for _, x in sorted(
                        zip([
                            len(self.paths[i][0]) + len(self.paths[i][1])
                            for i in intersections[intersection_node]
                        ], intersections[intersection_node]))
                ]

                # TODO: multiple passes if failure to find an optimal solution
                path_id1 = path_id_list.pop()
                path_id2 = path_id_list.pop()

                solved = _try_solve_intersection(
                    intersection_node,
                    *(self.paths[path_id1] + node_is_not_crossing[path_id1]))

                if not solved:
                    solved = _try_solve_intersection(
                        intersection_node,
                        *(self.paths[path_id2] +
                          node_is_not_crossing[path_id2]))

                if not solved:
                    # Last resort: delete one path
                    path_id_min, path_id_max = sorted([path_id1, path_id2])
                    del node_is_not_crossing[path_id_max]
                    self.remove_path_by_id(path_id_max)
                    node_is_not_crossing[path_id_min] = ([
                        node not in self.crossings[path_id_min]
                        for node in self.paths[path_id_min][0]
                    ], [
                        node not in self.crossings[path_id_min]
                        for node in self.paths[path_id_min][1]
                    ])

                intersections = _find_first_order_intersections(
                    self.crossings, self.paths)
                intersection_node_list = [
                    x for _, x in sorted(
                        zip(intersections.values(), intersections.keys()),
                        key=intersection_sort)
                ]

    def _calculate_path(self, node0, node1):
        """
        Calculate a path between two nodes on the graph.

        Args:
            node0 (int) : backend id of the first qubit
            node1 (int) : backend id of the second qubit
        """

        if self.enable_caching:
            try:
                path = self.cache.get_path(node0, node1)
            except KeyError:
                path = nx.shortest_path(self.graph, source=node0, target=node1)
                self.cache.add_path(path)
        else:
            path = nx.shortest_path(self.graph, source=node0, target=node1)

        return path

    def _try_alternative_paths(self, node0, node1):
        """
        Attempt to find some alternative paths
        """
        for neighbour in self.graph[node0]:
            new_path = self._calculate_path(neighbour, node1)
            if new_path[-1] == neighbour:
                new_path = new_path + [node0]
            else:
                new_path = [node0] + new_path
            if self.try_add_path(new_path):
                return True
        for neighbour in self.graph[node1]:
            new_path = self._calculate_path(node0, neighbour)
            if new_path[-1] == neighbour:
                new_path = new_path + [node1]
            else:
                new_path = [node1] + new_path
            if self.try_add_path(new_path):
                return True

        return False
