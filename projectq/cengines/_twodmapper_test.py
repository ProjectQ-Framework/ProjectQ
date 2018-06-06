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

"""Tests for projectq.cengines._2dmapper.py."""

from copy import deepcopy
import itertools
import random

import pytest

from projectq.cengines import DummyEngine
from projectq.ops import (Allocate, BasicGate, Command, Deallocate, FlushGate,
                          X)
from projectq.types import WeakQubitRef

from projectq.cengines import _twodmapper as two_d


def test_is_available():
    mapper = two_d.SquareGridMapper(num_rows=2, num_columns=2)
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    cmd0 = Command(None, BasicGate(), qubits=([qb0],))
    assert mapper.is_available(cmd0)
    cmd1 = Command(None, BasicGate(), qubits=([qb0],), controls=[qb1])
    assert mapper.is_available(cmd1)
    cmd2 = Command(None, BasicGate(), qubits=([qb0], [qb1, qb2]))
    assert not mapper.is_available(cmd2)
    cmd3 = Command(None, BasicGate(), qubits=([qb0], [qb1]), controls=[qb2])
    assert not mapper.is_available(cmd3)


def test_return_new_mapping():
    mapper = two_d.SquareGridMapper(num_rows=4, num_columns=3)
    linear_chain_ids = [33, 22, 11, 2, 3, 0, 6, 7, 9, 12, 4, 88]
    mapper._stored_commands = []
    for i in range(12):
        qb = WeakQubitRef(engine=None, idx=linear_chain_ids[i])
        cmd = Command(None, Allocate, ([qb],))
        mapper._stored_commands.append(cmd)
    for i in range(11):
        qb0 = WeakQubitRef(engine=None, idx=linear_chain_ids[i])
        qb1 = WeakQubitRef(engine=None, idx=linear_chain_ids[i+1])
        cmd = Command(None, X, qubits=([qb0],), controls=[qb1])
        mapper._stored_commands.append(cmd)
    new_mapping = mapper._return_new_mapping()
    possible_solution_1 = {33: 0, 22: 1, 11: 2, 2: 5, 3: 4, 0: 3, 6: 6, 7: 7,
                           9: 8, 12: 11, 4: 10, 88: 9}
    possible_solution_2 = {88: 0, 4: 1, 12: 2, 9: 5, 7: 4, 6: 3, 0: 6, 3: 7,
                           2: 8, 11: 11, 22: 10, 33: 9}
    assert (new_mapping == possible_solution_1 or
            new_mapping == possible_solution_2)


@pytest.mark.parametrize("num_rows, num_columns, seed, none_old, none_new",
                         [(2, 2, 0, 0, 0), (3, 4, 1, 0, 0), (4, 3, 2, 0, 0),
                          (5, 5, 3, 0, 0), (5, 3, 4, 3, 0), (4, 4, 5, 0, 3),
                          (6, 6, 7, 2, 3)])
def test_return_swaps_random(num_rows, num_columns, seed, none_old, none_new):
    random.seed(seed)
    num_qubits = num_rows * num_columns
    old_chain = random.sample(range(num_qubits), num_qubits)
    new_chain = random.sample(range(num_qubits), num_qubits)
    old_mapping = dict()
    new_mapping = dict()
    for i in range(num_qubits):
        old_mapping[old_chain[i]] = i
        new_mapping[new_chain[i]] = i
    # Remove certain elements from mappings:
    old_none_ids = set(random.sample(range(num_qubits), none_old))
    if none_old != 0:
        for logical_id in old_none_ids:
            old_mapping.pop(logical_id)
    new_none_ids = set(random.sample(range(num_qubits), none_new))
    if none_new != 0:
        for logical_id in new_none_ids:
            new_mapping.pop(logical_id)

    mapper = two_d.SquareGridMapper(num_rows=num_rows,
                                    num_columns=num_columns)
    swaps = mapper.return_swaps(old_mapping, new_mapping)
    # Check that Swaps are allowed
    all_allowed_swaps = set()
    for row in range(num_rows):
        for column in range(num_columns-1):
            qb_id = row * num_columns + column
            all_allowed_swaps.add((qb_id, qb_id + 1))
    for row in range(num_rows-1):
        for column in range(num_columns):
            qb_id = row * num_columns + column
            all_allowed_swaps.add((qb_id, qb_id + num_columns))

    for swap in swaps:
        assert swap in all_allowed_swaps
    test_chain = deepcopy(old_chain)
    for pos0, pos1 in swaps:
        tmp = test_chain[pos0]
        test_chain[pos0] = test_chain[pos1]
        test_chain[pos1] = tmp
    assert len(test_chain) == len(new_chain)
    for i in range(len(new_chain)):
        if new_chain[i] in old_mapping and new_chain[i] in new_mapping:
            assert test_chain[i] == new_chain[i]


def test_send_possible_commands():
    mapper = two_d.SquareGridMapper(num_rows=2, num_columns=4)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    # mapping is identical except 5 <-> 0
    mapper.current_mapping = {5: 0, 1: 1, 2: 2, 3: 3, 4: 4, 0: 5, 6: 6, 7: 7}
    neighbours = [(5, 1), (1, 2), (2, 3), (4, 0), (0, 6), (6, 7),
                  (5, 4), (1, 0), (2, 6), (3, 7)]
    for qb0_id, qb1_id in neighbours:
        qb0 = WeakQubitRef(engine=None, idx=qb0_id)
        qb1 = WeakQubitRef(engine=None, idx=qb1_id)
        cmd1 = Command(None, X, qubits=([qb0],), controls=[qb1])
        cmd2 = Command(None, X, qubits=([qb1],), controls=[qb0])
        mapper._stored_commands = [cmd1, cmd2]
        mapper._send_possible_commands()
        assert len(mapper._stored_commands) == 0
    for qb0_id, qb1_id in itertools.permutations(range(8), 2):
        if ((qb0_id, qb1_id) not in neighbours and
                (qb1_id, qb0_id) not in neighbours):
            qb0 = WeakQubitRef(engine=None, idx=qb0_id)
            qb1 = WeakQubitRef(engine=None, idx=qb1_id)
            cmd = Command(None, X, qubits=([qb0],), controls=[qb1])
            mapper._stored_commands = [cmd]
            mapper._send_possible_commands()
            assert len(mapper._stored_commands) == 1


def test_send_possible_commands_allocate():
    mapper = two_d.SquareGridMapper(num_rows=3, num_columns=2)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],), controls=[],
                   tags=[])
    mapper._stored_commands = [cmd0]
    mapper._currently_allocated_ids = set([10])
    # not in mapping:
    mapper.current_mapping = dict()
    assert len(backend.received_commands) == 0
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 0
    assert mapper._stored_commands == [cmd0]
    # in mapping:
    mapper.current_mapping[0] = 3
    mapper._send_possible_commands()
    assert len(mapper._stored_commands) == 0
    # Only self._run() sends Allocate gates
    assert len(backend.received_commands) == 0
    assert mapper._currently_allocated_ids == set([10, 0])


def test_send_possible_commands_deallocate():
    mapper = two_d.SquareGridMapper(num_rows=3, num_columns=2)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(engine=None, gate=Deallocate, qubits=([qb0],), controls=[],
                   tags=[])
    mapper._stored_commands = [cmd0]
    mapper.current_mapping = dict()
    mapper._currently_allocated_ids = set([10])
    # not yet allocated:
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 0
    assert mapper._stored_commands == [cmd0]
    # allocated:
    mapper.current_mapping[0] = 3
    mapper._currently_allocated_ids.add(0)
    mapper._send_possible_commands()
    # Only self._run() send Deallocate gates
    assert len(backend.received_commands) == 0
    assert len(mapper._stored_commands) == 0
    assert mapper.current_mapping == dict()
    assert mapper._currently_allocated_ids == set([10])


def test_send_possible_commands_keep_remaining_gates():
    mapper = two_d.SquareGridMapper(num_rows=3, num_columns=2)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],), controls=[],
                   tags=[])
    cmd1 = Command(engine=None, gate=Deallocate, qubits=([qb0],), controls=[],
                   tags=[])
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb1],), controls=[],
                   tags=[])

    mapper._stored_commands = [cmd0, cmd1, cmd2]
    mapper.current_mapping = {0: 0}
    mapper._send_possible_commands()
    assert mapper._stored_commands == [cmd2]


def test_send_possible_commands_one_inactive_qubit():
    mapper = two_d.SquareGridMapper(num_rows=3, num_columns=2)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],), controls=[],
                   tags=[])
    cmd1 = Command(engine=None, gate=X, qubits=([qb0],), controls=[qb1])
    mapper._stored_commands = [cmd0, cmd1]
    mapper.current_mapping = {0: 0}
    mapper._send_possible_commands()
    assert mapper._stored_commands == [cmd1]

@pytest.mark.parametrize("num_optimization_steps", [1, 10])
def test_run_and_receive(num_optimization_steps):
    def choose_last_permutation(swaps):
        choose_last_permutation.counter -= 1
        return choose_last_permutation.counter
    choose_last_permutation.counter = 100
    mapper = two_d.SquareGridMapper(
        num_rows=2,
        num_columns=2,
        optimization_function=choose_last_permutation,
        num_optimization_steps=num_optimization_steps)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=3)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1],))
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb2],))
    cmd3 = Command(engine=None, gate=Allocate, qubits=([qb3],))
    cmd4 = Command(None, X, qubits=([qb0],), controls=[qb1])
    cmd5 = Command(None, X, qubits=([qb1],), controls=[qb3])
    cmd6 = Command(None, X, qubits=([qb3],), controls=[qb2])
    cmd7 = Command(None, X, qubits=([qb0],), controls=[qb2])
    cmd8 = Command(engine=None, gate=Deallocate, qubits=([qb1],))
    all_cmd = [cmd0, cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7, cmd8]
    mapper.receive(all_cmd)
    assert mapper._stored_commands == all_cmd
    qb4 = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb4],))
    mapper.receive([cmd_flush])
    assert mapper._stored_commands == []
    assert len(backend.received_commands) == 10
    assert mapper._currently_allocated_ids == set([0, 2, 3])
    assert (mapper.current_mapping == {0: 0, 2: 2, 3: 3} or
            mapper.current_mapping == {0: 1, 2: 3, 3: 0} or
            mapper.current_mapping == {0: 2, 2: 0, 3: 1} or
            mapper.current_mapping == {0: 3, 2: 1, 3: 2})
    cmd9 = Command(None, X, qubits=([qb0],), controls=[qb2])
    mapper.storage = 1
    mapper.receive([cmd9])
    assert mapper._currently_allocated_ids == set([0, 2, 3])
    assert mapper._stored_commands == []
    assert len(mapper.current_mapping) == 3
    assert 0 in mapper.current_mapping
    assert 2 in mapper.current_mapping
    assert 3 in mapper.current_mapping
    assert mapper.num_mappings == 2
    assert mapper.depth_of_swaps[0] == 1
    assert mapper.num_of_swaps_per_mapping[0] == 1


def test_run_infinite_loop_detection():
    mapper = two_d.SquareGridMapper(num_rows=2, num_columns=2)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=3)
    qb4 = WeakQubitRef(engine=None, idx=4)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1],))
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb2],))
    cmd3 = Command(engine=None, gate=Allocate, qubits=([qb3],))
    cmd4 = Command(engine=None, gate=Allocate, qubits=([qb4],))
    cmd5 = Command(None, X, qubits=([qb0],), controls=[qb1])
    qb2 = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb2],))
    with pytest.raises(RuntimeError):
        mapper.receive([cmd0, cmd1, cmd2, cmd3, cmd4, cmd5, cmd_flush])
