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

Its main goal is to store possible paths through the graph and then generate a
list of swap operations to perform as many paths as possible, by either solving
conflicts (ie. crossing points and intersections; see definitions below) or
discarding paths.
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
    for path in split_paths.values():
        swap_operations.append([])
        # Add swaps operations for first half of the path
        for prev, cur in zip(path[0], path[0][1:]):
            swap_operations[-1].append((prev, cur))

        # Add swaps operations for the second half of the path
        for prev, cur in zip(path[1][::-1], path[1][-2::-1]):
            swap_operations[-1].append((prev, cur))

    return swap_operations


# ==============================================================================


class PathContainer:
    """
    Container for paths through a graph.

    Allows the resolution of conflict points such as crossings and
    intersections.

    Attributes:
        paths (dict) : list of paths currently held by a path container indexed
                       by a unique ID
        crossings (dict) : dictionary of crossing points indexed by path ID
    """

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

    def __init__(self):
        self.paths = {}
        self.crossings = {}
        self._path_id = 0

    #################################################################
    # Methods querying information about the state of the container #
    #################################################################

    def get_all_nodes(self):
        """
        Return a list of all nodes that are part of some path.

        Returns:
            A set of nodes that are part of at least one path.
        """
        return set(itertools.chain.from_iterable(self.paths.values()))

    def get_all_paths(self):
        """
        Return a list of all the path contained in the container.

        Returns:
            A list of paths (list of list of ints)
        """
        return [v for _, v in self.paths.items()]

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
            if frozenset((node0, node1)) == frozenset((path[0], path[-1])):
                return True
        return False

    def max_crossing_order(self):
        """
        Return the order of the highest order intersection.

        The intersection order is given by the number of paths that consider a
        particular crossing point as an intersection

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

    ##################################################
    # Methods modifying the content of the container #
    ##################################################

    def clear(self):
        """
        Reset the state of the container.
        """
        self.paths = {}
        self.crossings = {}
        self._path_id = 0

    def try_add_path(self, new_path):
        """
        Try adding a path to the path container.

        Args:
            new_path (list) : path to add to the container

        Returns:
            True if the path could be added to the container, False otherwise
        """
        # Prevent adding a path to the container if the start or the end
        # qubit is already interacting with another one
        # Also make sure the new path does not contain interacting qubits
        for path in self.paths.values():
            if path[0] in new_path or path[-1] in new_path:
                return False

        new_crossings = []
        for idx, path in self.paths.items():
            path_overlap = [node for node in new_path if node in path]
            if len(path_overlap) > 1:
                return False
            if len(path_overlap) == 1:
                new_crossings.append(
                    PathContainer._Crossing(idx, path_overlap))

        self.paths[self._path_id] = new_path
        self.crossings[self._path_id] = new_crossings
        for crossing in new_crossings:
            self.crossings[crossing.path_id].append(
                PathContainer._Crossing(self._path_id, crossing.overlap))
        self._path_id += 1
        return True

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

    def generate_swaps(self):
        """
        Generate a list of swaps to execute as many paths as possible.

        Returns:
            A list of swap operations (tuples)
        """
        # TODO: think about merging paths
        # TODO: maybe apply gates in the middle of the swaps

        max_crossing_order = self.max_crossing_order()

        split_paths = self._split_paths()

        if max_crossing_order > 0:
            # Some paths have first order crossing points (ie. at most one
            # point is common). Try to re-arrange the path splitting to remove
            # the intersection points
            self._solve_first_order_intersections(split_paths)

        # By this point, we should have solved all intersections

        return list(itertools.chain.from_iterable(_return_swaps(split_paths)))

    def _split_paths(self):
        """
        Split all paths into pairs of equal or almost equal length sub-paths.

        Returns:
            Dictionary indexed by path ID containing 2-tuples with each path
            halves
        """
        split_paths = {}
        for path_id, path in self.paths.items():
            idx = len(path) >> 1
            split_paths[path_id] = (path[:idx], path[idx:])
        return split_paths

    def _solve_first_order_intersections(self, split_paths):
        """
        Solve all first order intersections.

        The intersections may be "solved" in two different manners:
          - Sub-path split are modified to transform intersections in simple
            crossings
          - Paths are removed from the container

        Pre-conditions:
            self.max_crossing_order() == 1

        Args:
            split_paths (dict): Dictionary indexed by path ID containing
                                2-tuples of path halvesx
        """
        # Get all the intersections
        intersections = _find_first_order_intersections(
            self.crossings, split_paths)

        # Get a list of the intersection nodes sorted by intersection order and
        # total number of points of all paths for that particular intersection
        def intersection_sort(crossing):
            order = len(crossing[0])
            number_of_points = sum(
                [len(self.paths[path_id])
                 for path_id in crossing[0]]) - order + 1
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
                    for node in split_paths[path_id][0]
                ], [
                    node not in self.crossings[path_id]
                    for node in split_paths[path_id][1]
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
                            split_paths[0], split_paths[1] = split_paths[
                                1], split_paths[0]
                del intersections[intersection_node]
                del intersection_node_list[-1]
            else:
                # This crossing is an intersection for multiple paths
                #   -> find all paths concerned with this crossing
                path_id_list = [
                    x for _, x in sorted(
                        zip([
                            len(self.paths[i])
                            for i in intersections[intersection_node]
                        ], intersections[intersection_node]))
                ]

                # TODO: multiple passes if failure to find an optimal solution
                path_id1 = path_id_list.pop()
                path_id2 = path_id_list.pop()

                solved = _try_solve_intersection(
                    intersection_node,
                    *(split_paths[path_id1] + node_is_not_crossing[path_id1]))

                if not solved:
                    solved = _try_solve_intersection(
                        intersection_node,
                        *(split_paths[path_id2] +
                          node_is_not_crossing[path_id2]))

                if not solved:
                    # Last resort: delete one path
                    path_id_min, path_id_max = sorted([path_id1, path_id2])
                    del split_paths[path_id_max]
                    del node_is_not_crossing[path_id_max]
                    self.remove_path_by_id(path_id_max)
                    node_is_not_crossing[path_id_min] = ([
                        node not in self.crossings[path_id_min]
                        for node in split_paths[path_id_min][0]
                    ], [
                        node not in self.crossings[path_id_min]
                        for node in split_paths[path_id_min][1]
                    ])

                intersections = _find_first_order_intersections(
                    self.crossings, split_paths)
                intersection_node_list = [
                    x for _, x in sorted(
                        zip(intersections.values(), intersections.keys()),
                        key=intersection_sort)
                ]
