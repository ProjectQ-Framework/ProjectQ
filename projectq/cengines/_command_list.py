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
"""

from copy import deepcopy
import networkx as nx

# ==============================================================================


class CommandList():
    """Class used to manage a list of ProjectQ commands"""

    def __init__(self):
        self._cmds = []
        self.partitions = [set()]
        self.interactions = [[]]

    def __len__(self):
        return len(self._cmds)

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __iter__(self):
        return self._cmds.__iter__()

    def __getitem__(self, key):
        return self._cmds[key]

    def __eq__(self, other):
        if isinstance(other, list):
            return self._cmds == other
        if isinstance(other, CommandList):
            return self._cmds == other._cmds
        raise NotImplementedError()

    @property
    def stored_commands(self):
        """
        Simple getter.
        """
        return deepcopy(self._cmds)

    def clear(self):
        """
        Remove all commands from the container.
        """
        self._cmds.clear()
        self.partitions = [set()]
        self.interactions = [[]]

    def append(self, cmd):
        """
        Append a command to the end of the container.
        """
        self._cmds.append(cmd)

        qubit_ids = {qubit.id for qureg in cmd.all_qubits for qubit in qureg}
        if len(qubit_ids) > 1:
            # Add new partition if any qubit ids are already present in the
            # current partition
            if self.partitions[-1] \
               and self.partitions[-1] & qubit_ids:
                self.partitions.append(set())
                self.interactions.append([])
            self.partitions[-1] |= qubit_ids
            self.interactions[-1].append(tuple(sorted(qubit_ids)))

    def extend(self, iterable):
        """
        Extend container by appending commands from the iterable.
        """
        for cmd in iterable:
            self.append(cmd)

    # --------------------------------------------------------------------------

    def calculate_qubit_interaction_subgraphs(self, order=2):
        """
        Calculate qubits interaction graph based on all commands stored.

        While iterating through the partitions, we create a graph whose
        vertices are logical qubit IDs and where edges represent an interaction
        between qubits.
        Additionally, we make sure that the resulting graph has no vertices
        with degree higher than a specified threshold.

        Args:
            order (int): maximum degree of the nodes in the resulting graph

        Returns:
            A list of list of graph nodes corresponding to all the connected
            components of the qubit interaction graph. Within each components,
            nodes are sorted in decreasing order of their degree.

        Note:
            The current implementation is really aimed towards handling
            two-qubit gates but should also work with higher order qubit gates.
        """
        graph = nx.Graph()
        for timestep in self.interactions:
            for interaction in timestep:
                for prev, cur in zip(interaction, interaction[1:]):
                    if prev not in graph \
                       or cur not in graph \
                       or (len(graph[prev]) < order
                           and len(graph[cur]) < order):
                        graph.add_edge(prev, cur)

        # Return value is a list of list of nodes corresponding to a list of
        # connected components of the intial graph sorted by their order
        # Each connected component is sorted in decreasing order by the degree
        # of each node in the graph
        return [
            sorted(
                graph.subgraph(g), key=lambda n: len(graph[n]), reverse=True)
            for g in sorted(
                nx.connected_components(graph),
                key=lambda c: (max(len(graph[n]) for n in c), len(c)),
                reverse=True)
        ]
