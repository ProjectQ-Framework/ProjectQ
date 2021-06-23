# -*- coding: utf-8 -*-
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
"""
Mapper for a quantum circuit to a 2D square grid.

Input: Quantum circuit with 1 and 2 qubit gates on n qubits. Gates are assumed to be applied in parallel if they act
       on disjoint qubit(s) and any pair of qubits can perform a 2 qubit gate (all-to-all connectivity)
Output: Quantum circuit in which qubits are placed in 2-D square grid in which only nearest neighbour qubits can
        perform a 2 qubit gate. The mapper uses Swap gates in order to move qubits next to each other.
"""
from copy import deepcopy
import itertools
import math
import random

import networkx as nx

from projectq.meta import LogicalQubitIDTag
from projectq.ops import (
    AllocateQubitGate,
    Command,
    DeallocateQubitGate,
    FlushGate,
    Swap,
)
from projectq.types import WeakQubitRef


from ._basicmapper import BasicMapperEngine
from ._linearmapper import LinearMapper, return_swap_depth


class GridMapper(BasicMapperEngine):  # pylint: disable=too-many-instance-attributes
    """
    Mapper to a 2-D grid graph.

    Mapped qubits on the grid are numbered in row-major order. E.g. for 3 rows and 2 columns:

    0 - 1
    |   |
    2 - 3
    |   |
    4 - 5

    The numbers are the mapped qubit ids. The backend might number the qubits on the grid differently (e.g. not
    row-major), we call these backend qubit ids. If the backend qubit ids are not row-major, one can pass a dictionary
    translating from our row-major mapped ids to these backend ids.

    Note: The algorithm sorts twice inside each column and once inside each row.

    Attributes:
        current_mapping: Stores the mapping: key is logical qubit id, value is backend qubit id.
        storage(int): Number of gate it caches before mapping.
        num_rows(int): Number of rows in the grid
        num_columns(int): Number of columns in the grid
        num_qubits(int): num_rows x num_columns = number of qubits
        num_mappings (int): Number of times the mapper changed the mapping
        depth_of_swaps (dict): Key are circuit depth of swaps, value is the number of such mappings which have been
                               applied
        num_of_swaps_per_mapping (dict): Key are the number of swaps per mapping, value is the number of such mappings
                                         which have been applied

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        num_rows,
        num_columns,
        mapped_ids_to_backend_ids=None,
        storage=1000,
        optimization_function=return_swap_depth,
        num_optimization_steps=50,
    ):
        """
        Initialize a GridMapper compiler engine.

        Args:
            num_rows(int): Number of rows in the grid
            num_columns(int): Number of columns in the grid.
            mapped_ids_to_backend_ids(dict): Stores a mapping from mapped ids which are 0,...,self.num_qubits-1 in
                                             row-major order on the grid to the corresponding qubit ids of the
                                             backend. Key: mapped id. Value: corresponding backend id.  Default is
                                             None which means backend ids are identical to mapped ids.
            storage: Number of gates to temporarily store
            optimization_function: Function which takes a list of swaps and returns a cost value. Mapper chooses a
                                   permutation which minimizes this cost.  Default optimizes for circuit depth.
            num_optimization_steps(int): Number of different permutations to of the matching to try and minimize the
                                         cost.
        Raises:
            RuntimeError: if incorrect `mapped_ids_to_backend_ids` parameter
        """
        super().__init__()
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.num_qubits = num_rows * num_columns
        # Internally we use the mapped ids until sending a command.
        # Before sending we use this map to translate to backend ids:
        self._mapped_ids_to_backend_ids = mapped_ids_to_backend_ids
        if self._mapped_ids_to_backend_ids is None:
            self._mapped_ids_to_backend_ids = dict()
            for i in range(self.num_qubits):
                self._mapped_ids_to_backend_ids[i] = i
        if not (set(self._mapped_ids_to_backend_ids.keys()) == set(range(self.num_qubits))) or not (
            len(set(self._mapped_ids_to_backend_ids.values())) == self.num_qubits
        ):
            raise RuntimeError("Incorrect mapped_ids_to_backend_ids parameter")
        self._backend_ids_to_mapped_ids = dict()
        for mapped_id, backend_id in self._mapped_ids_to_backend_ids.items():
            self._backend_ids_to_mapped_ids[backend_id] = mapped_id
        # As we use internally the mapped ids which are in row-major order,
        # we have an internal current mapping which maps from logical ids to
        # these mapped ids:
        self._current_row_major_mapping = deepcopy(self.current_mapping)
        self.storage = storage
        self.optimization_function = optimization_function
        self.num_optimization_steps = num_optimization_steps
        # Randomness to pick permutations if there are too many.
        # This creates an own instance of Random in order to not influence
        # the bound methods of the random module which might be used in other
        # places.
        self._rng = random.Random(11)
        # Storing commands
        self._stored_commands = list()
        # Logical qubit ids for which the Allocate gate has already been
        # processed and sent to the next engine but which are not yet
        # deallocated:
        self._currently_allocated_ids = set()
        # Change between 2D and 1D mappings (2D is a snake like 1D chain)
        # Note it translates to our mapped ids in row major order and not
        # backend ids which might be different.
        self._map_2d_to_1d = dict()
        self._map_1d_to_2d = dict()
        for row_index in range(self.num_rows):
            for column_index in range(self.num_columns):
                if row_index % 2 == 0:
                    mapped_id = row_index * self.num_columns + column_index
                    self._map_2d_to_1d[mapped_id] = mapped_id
                    self._map_1d_to_2d[mapped_id] = mapped_id
                else:
                    mapped_id_2d = row_index * self.num_columns + column_index
                    mapped_id_1d = (row_index + 1) * self.num_columns - column_index - 1
                    self._map_2d_to_1d[mapped_id_2d] = mapped_id_1d
                    self._map_1d_to_2d[mapped_id_1d] = mapped_id_2d
        # Statistics:
        self.num_mappings = 0
        self.depth_of_swaps = dict()
        self.num_of_swaps_per_mapping = dict()

    @property
    def current_mapping(self):
        return deepcopy(self._current_mapping)

    @current_mapping.setter
    def current_mapping(self, current_mapping):
        self._current_mapping = current_mapping
        if current_mapping is None:
            self._current_row_major_mapping = None
        else:
            self._current_row_major_mapping = dict()
            for logical_id, backend_id in current_mapping.items():
                self._current_row_major_mapping[logical_id] = self._backend_ids_to_mapped_ids[backend_id]

    def is_available(self, cmd):
        """
        Only allows 1 or two qubit gates.
        """
        num_qubits = 0
        for qureg in cmd.all_qubits:
            num_qubits += len(qureg)
        return num_qubits <= 2

    def _return_new_mapping(self):
        """
        Returns a new mapping of the qubits.

        It goes through self._saved_commands and tries to find a mapping to apply these gates on a first come first
        served basis.  It reuses the function of a 1D mapper and creates a mapping for a 1D linear chain and then
        wraps it like a snake onto the square grid.

        One might create better mappings by specializing this function for a square grid.

        Returns: A new mapping as a dict. key is logical qubit id, value is mapped id
        """
        # Change old mapping to 1D in order to use LinearChain heuristic
        if self._current_row_major_mapping:
            old_mapping_1d = dict()
            for logical_id, mapped_id in self._current_row_major_mapping.items():
                old_mapping_1d[logical_id] = self._map_2d_to_1d[mapped_id]
        else:
            old_mapping_1d = self._current_row_major_mapping

        new_mapping_1d = LinearMapper.return_new_mapping(
            num_qubits=self.num_qubits,
            cyclic=False,
            currently_allocated_ids=self._currently_allocated_ids,
            stored_commands=self._stored_commands,
            current_mapping=old_mapping_1d,
        )

        new_mapping_2d = dict()
        for logical_id, mapped_id in new_mapping_1d.items():
            new_mapping_2d[logical_id] = self._map_1d_to_2d[mapped_id]
        return new_mapping_2d

    def _compare_and_swap(self, element0, element1, key):
        """
        If swapped (inplace), then return swap operation so that key(element0) < key(element1)
        """
        if key(element0) > key(element1):
            mapped_id0 = element0.current_column + element0.current_row * self.num_columns
            mapped_id1 = element1.current_column + element1.current_row * self.num_columns
            swap_operation = (mapped_id0, mapped_id1)
            # swap elements but update also current position:
            tmp_0 = element0.final_row
            tmp_1 = element0.final_column
            tmp_2 = element0.row_after_step_1
            element0.final_row = element1.final_row
            element0.final_column = element1.final_column
            element0.row_after_step_1 = element1.row_after_step_1
            element1.final_row = tmp_0
            element1.final_column = tmp_1
            element1.row_after_step_1 = tmp_2
            return swap_operation
        return None

    def _sort_within_rows(self, final_positions, key):
        swap_operations = []
        for row in range(self.num_rows):
            finished_sorting = False
            while not finished_sorting:
                finished_sorting = True
                for column in range(1, self.num_columns - 1, 2):
                    element0 = final_positions[row][column]
                    element1 = final_positions[row][column + 1]
                    swap = self._compare_and_swap(element0, element1, key=key)
                    if swap is not None:
                        finished_sorting = False
                        swap_operations.append(swap)
                for column in range(0, self.num_columns - 1, 2):
                    element0 = final_positions[row][column]
                    element1 = final_positions[row][column + 1]
                    swap = self._compare_and_swap(element0, element1, key=key)
                    if swap is not None:
                        finished_sorting = False
                        swap_operations.append(swap)
        return swap_operations

    def _sort_within_columns(self, final_positions, key):
        swap_operations = []
        for column in range(self.num_columns):
            finished_sorting = False
            while not finished_sorting:
                finished_sorting = True
                for row in range(1, self.num_rows - 1, 2):
                    element0 = final_positions[row][column]
                    element1 = final_positions[row + 1][column]
                    swap = self._compare_and_swap(element0, element1, key=key)
                    if swap is not None:
                        finished_sorting = False
                        swap_operations.append(swap)
                for row in range(0, self.num_rows - 1, 2):
                    element0 = final_positions[row][column]
                    element1 = final_positions[row + 1][column]
                    swap = self._compare_and_swap(element0, element1, key=key)
                    if swap is not None:
                        finished_sorting = False
                        swap_operations.append(swap)
        return swap_operations

    def return_swaps(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        self, old_mapping, new_mapping, permutation=None
    ):
        """
        Returns the swap operation to change mapping

        Args:
            old_mapping: dict: keys are logical ids and values are mapped qubit ids
            new_mapping: dict: keys are logical ids and values are mapped qubit ids
            permutation: list of int from 0, 1, ..., self.num_rows-1. It is used to permute the found perfect
                         matchings. Default is None which keeps the original order.
        Returns:
            List of tuples. Each tuple is a swap operation which needs to be applied. Tuple contains the two mapped
            qubit ids for the Swap.
        """
        if permutation is None:
            permutation = list(range(self.num_rows))
        swap_operations = []

        class Position:  # pylint: disable=too-few-public-methods
            """Custom Container."""

            def __init__(  # pylint: disable=too-many-arguments
                self,
                current_row,
                current_column,
                final_row,
                final_column,
                row_after_step_1=None,
            ):
                self.current_row = current_row
                self.current_column = current_column
                self.final_row = final_row
                self.final_column = final_column
                self.row_after_step_1 = row_after_step_1

        # final_positions contains info containers
        # final_position[i][j] contains info container with
        # current_row == i and current_column == j
        final_positions = [[None for i in range(self.num_columns)] for j in range(self.num_rows)]
        # move qubits which are in both mappings
        used_mapped_ids = set()
        for logical_id in old_mapping:
            if logical_id in new_mapping:
                used_mapped_ids.add(new_mapping[logical_id])
                old_column = old_mapping[logical_id] % self.num_columns
                old_row = old_mapping[logical_id] // self.num_columns
                new_column = new_mapping[logical_id] % self.num_columns
                new_row = new_mapping[logical_id] // self.num_columns
                info_container = Position(
                    current_row=old_row,
                    current_column=old_column,
                    final_row=new_row,
                    final_column=new_column,
                )
                final_positions[old_row][old_column] = info_container
        # exchange all remaining None with the not yet used mapped ids
        all_ids = set(range(self.num_qubits))
        not_used_mapped_ids = list(all_ids.difference(used_mapped_ids))
        not_used_mapped_ids = sorted(not_used_mapped_ids, reverse=True)
        for row in range(self.num_rows):
            for column in range(self.num_columns):
                if final_positions[row][column] is None:
                    mapped_id = not_used_mapped_ids.pop()
                    new_column = mapped_id % self.num_columns
                    new_row = mapped_id // self.num_columns
                    info_container = Position(
                        current_row=row,
                        current_column=column,
                        final_row=new_row,
                        final_column=new_column,
                    )
                    final_positions[row][column] = info_container
        if len(not_used_mapped_ids) > 0:  # pragma: no cover
            raise RuntimeError('Internal compiler error: len(not_used_mapped_ids) > 0')
        # 1. Assign column_after_step_1 for each element
        # Matching contains the num_columns matchings
        matchings = [None for i in range(self.num_rows)]
        # Build bipartite graph. Nodes are the current columns numbered (0, 1, ...) and the destination columns
        # numbered with an offset of self.num_columns (0 + offset, 1+offset, ...)
        graph = nx.Graph()
        offset = self.num_columns
        graph.add_nodes_from(range(self.num_columns), bipartite=0)
        graph.add_nodes_from(range(offset, offset + self.num_columns), bipartite=1)
        # Add an edge to the graph from (i, j+offset) for every element currently in column i which should go to
        # column j for the new mapping
        for row in range(self.num_rows):
            for column in range(self.num_columns):
                destination_column = final_positions[row][column].final_column
                if not graph.has_edge(column, destination_column + offset):
                    graph.add_edge(column, destination_column + offset)
                    # Keep manual track of multiple edges between nodes
                    graph[column][destination_column + offset]['num'] = 1
                else:
                    graph[column][destination_column + offset]['num'] += 1
        # Find perfect matching, remove those edges from the graph and do it again:
        for i in range(self.num_rows):
            top_nodes = range(self.num_columns)
            matching = nx.bipartite.maximum_matching(graph, top_nodes)
            matchings[i] = matching
            # Remove all edges of the current perfect matching
            for node in range(self.num_columns):
                if graph[node][matching[node]]['num'] == 1:
                    graph.remove_edge(node, matching[node])
                else:
                    graph[node][matching[node]]['num'] -= 1
        # permute the matchings:
        tmp = deepcopy(matchings)
        for i in range(self.num_rows):
            matchings[i] = tmp[permutation[i]]
        # Assign row_after_step_1
        for column in range(self.num_columns):
            for row_after_step_1 in range(self.num_rows):
                dest_column = matchings[row_after_step_1][column] - offset
                best_element = None
                for row in range(self.num_rows):
                    element = final_positions[row][column]
                    if element.row_after_step_1 is not None:
                        continue
                    if element.final_column == dest_column:
                        if best_element is None:
                            best_element = element
                        elif best_element.final_row > element.final_row:
                            best_element = element
                best_element.row_after_step_1 = row_after_step_1
        # 2. Sort inside all the rows
        swaps = self._sort_within_columns(final_positions=final_positions, key=lambda x: x.row_after_step_1)
        swap_operations += swaps
        # 3. Sort inside all the columns
        swaps = self._sort_within_rows(final_positions=final_positions, key=lambda x: x.final_column)
        swap_operations += swaps
        # 4. Sort inside all the rows
        swaps = self._sort_within_columns(final_positions=final_positions, key=lambda x: x.final_row)
        swap_operations += swaps
        return swap_operations

    def _send_possible_commands(self):  # pylint: disable=too-many-branches
        """
        Sends the stored commands possible without changing the mapping.

        Note: self._current_row_major_mapping (hence also self.current_mapping) must exist already
        """
        active_ids = deepcopy(self._currently_allocated_ids)
        for logical_id in self._current_row_major_mapping:
            # So that loop doesn't stop before AllocateGate applied
            active_ids.add(logical_id)

        new_stored_commands = []
        for i in range(len(self._stored_commands)):
            cmd = self._stored_commands[i]
            if len(active_ids) == 0:
                new_stored_commands += self._stored_commands[i:]
                break
            if isinstance(cmd.gate, AllocateQubitGate):
                if cmd.qubits[0][0].id in self._current_row_major_mapping:
                    self._currently_allocated_ids.add(cmd.qubits[0][0].id)

                    mapped_id = self._current_row_major_mapping[cmd.qubits[0][0].id]
                    qb = WeakQubitRef(engine=self, idx=self._mapped_ids_to_backend_ids[mapped_id])
                    new_cmd = Command(
                        engine=self,
                        gate=AllocateQubitGate(),
                        qubits=([qb],),
                        tags=[LogicalQubitIDTag(cmd.qubits[0][0].id)],
                    )
                    self.send([new_cmd])
                else:
                    new_stored_commands.append(cmd)
            elif isinstance(cmd.gate, DeallocateQubitGate):
                if cmd.qubits[0][0].id in active_ids:
                    mapped_id = self._current_row_major_mapping[cmd.qubits[0][0].id]
                    qb = WeakQubitRef(engine=self, idx=self._mapped_ids_to_backend_ids[mapped_id])
                    new_cmd = Command(
                        engine=self,
                        gate=DeallocateQubitGate(),
                        qubits=([qb],),
                        tags=[LogicalQubitIDTag(cmd.qubits[0][0].id)],
                    )
                    self._currently_allocated_ids.remove(cmd.qubits[0][0].id)
                    active_ids.remove(cmd.qubits[0][0].id)
                    self._current_row_major_mapping.pop(cmd.qubits[0][0].id)
                    self._current_mapping.pop(cmd.qubits[0][0].id)
                    self.send([new_cmd])
                else:
                    new_stored_commands.append(cmd)
            else:
                send_gate = True
                mapped_ids = set()
                for qureg in cmd.all_qubits:
                    for qubit in qureg:
                        if qubit.id not in active_ids:
                            send_gate = False
                            break
                        mapped_ids.add(self._current_row_major_mapping[qubit.id])
                # Check that mapped ids are nearest neighbour on 2D grid
                if len(mapped_ids) == 2:
                    qb0, qb1 = sorted(list(mapped_ids))
                    send_gate = False
                    if qb1 - qb0 == self.num_columns:
                        send_gate = True
                    elif qb1 - qb0 == 1 and qb1 % self.num_columns != 0:
                        send_gate = True
                if send_gate:
                    # Note: This sends the cmd correctly with the backend ids as it looks up the mapping in
                    #       self.current_mapping and not our internal mapping self._current_row_major_mapping
                    self._send_cmd_with_mapped_ids(cmd)
                else:
                    for qureg in cmd.all_qubits:
                        for qubit in qureg:
                            active_ids.discard(qubit.id)
                    new_stored_commands.append(cmd)
        self._stored_commands = new_stored_commands

    def _run(self):  # pylint: disable=too-many-locals.too-many-branches,too-many-statements
        """
        Creates a new mapping and executes possible gates.

        It first allocates all 0, ..., self.num_qubits-1 mapped qubit ids, if they are not already used because we
        might need them all for the swaps. Then it creates a new map, swaps all the qubits to the new map, executes
        all possible gates, and finally deallocates mapped qubit ids which don't store any information.
        """
        num_of_stored_commands_before = len(self._stored_commands)
        if not self.current_mapping:
            self.current_mapping = dict()
        else:
            self._send_possible_commands()
            if len(self._stored_commands) == 0:
                return
        new_row_major_mapping = self._return_new_mapping()
        # Find permutation of matchings with lowest cost
        swaps = None
        lowest_cost = None
        matchings_numbers = list(range(self.num_rows))
        if self.num_optimization_steps <= math.factorial(self.num_rows):
            permutations = itertools.permutations(matchings_numbers, self.num_rows)
        else:
            permutations = []
            for _ in range(self.num_optimization_steps):
                permutations.append(self._rng.sample(matchings_numbers, self.num_rows))
        for permutation in permutations:
            trial_swaps = self.return_swaps(
                old_mapping=self._current_row_major_mapping,
                new_mapping=new_row_major_mapping,
                permutation=permutation,
            )
            if swaps is None:
                swaps = trial_swaps
                lowest_cost = self.optimization_function(trial_swaps)
            elif lowest_cost > self.optimization_function(trial_swaps):
                swaps = trial_swaps
                lowest_cost = self.optimization_function(trial_swaps)
        if swaps:  # first mapping requires no swaps
            # Allocate all mapped qubit ids (which are not already allocated,
            # i.e., contained in self._currently_allocated_ids)
            mapped_ids_used = set()
            for logical_id in self._currently_allocated_ids:
                mapped_ids_used.add(self._current_row_major_mapping[logical_id])
            not_allocated_ids = set(range(self.num_qubits)).difference(mapped_ids_used)
            for mapped_id in not_allocated_ids:
                qb = WeakQubitRef(engine=self, idx=self._mapped_ids_to_backend_ids[mapped_id])
                cmd = Command(engine=self, gate=AllocateQubitGate(), qubits=([qb],))
                self.send([cmd])
            # Send swap operations to arrive at new_mapping:
            for qubit_id0, qubit_id1 in swaps:
                qb0 = WeakQubitRef(engine=self, idx=self._mapped_ids_to_backend_ids[qubit_id0])
                qb1 = WeakQubitRef(engine=self, idx=self._mapped_ids_to_backend_ids[qubit_id1])
                cmd = Command(engine=self, gate=Swap, qubits=([qb0], [qb1]))
                self.send([cmd])
            # Register statistics:
            self.num_mappings += 1
            depth = return_swap_depth(swaps)
            if depth not in self.depth_of_swaps:
                self.depth_of_swaps[depth] = 1
            else:
                self.depth_of_swaps[depth] += 1
            if len(swaps) not in self.num_of_swaps_per_mapping:
                self.num_of_swaps_per_mapping[len(swaps)] = 1
            else:
                self.num_of_swaps_per_mapping[len(swaps)] += 1
            # Deallocate all previously mapped ids which we only needed for the
            # swaps:
            mapped_ids_used = set()
            for logical_id in self._currently_allocated_ids:
                mapped_ids_used.add(new_row_major_mapping[logical_id])
            not_needed_anymore = set(range(self.num_qubits)).difference(mapped_ids_used)
            for mapped_id in not_needed_anymore:
                qb = WeakQubitRef(engine=self, idx=self._mapped_ids_to_backend_ids[mapped_id])
                cmd = Command(engine=self, gate=DeallocateQubitGate(), qubits=([qb],))
                self.send([cmd])
        # Change to new map:
        self._current_row_major_mapping = new_row_major_mapping
        new_mapping = dict()
        for logical_id, mapped_id in new_row_major_mapping.items():
            new_mapping[logical_id] = self._mapped_ids_to_backend_ids[mapped_id]
        self.current_mapping = new_mapping
        # Send possible gates:
        self._send_possible_commands()
        # Check that mapper actually made progress
        if len(self._stored_commands) == num_of_stored_commands_before:
            raise RuntimeError(
                "Mapper is potentially in an infinite loop. It is likely that the algorithm requires too"
                "many qubits. Increase the number of qubits for this mapper."
            )

    def receive(self, command_list):
        """
        Receives a command list and, for each command, stores it until we do a mapping (FlushGate or Cache of stored
        commands is full).

        Args:
            command_list (list of Command objects): list of commands to receive.
        """
        for cmd in command_list:
            if isinstance(cmd.gate, FlushGate):
                while self._stored_commands:
                    self._run()
                self.send([cmd])
            else:
                self._stored_commands.append(cmd)
            # Storage is full: Create new map and send some gates away:
            if len(self._stored_commands) >= self.storage:
                self._run()
