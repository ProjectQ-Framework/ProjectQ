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
"""Tests for projectq.cengines._linearmapper.py."""
from copy import deepcopy

import pytest

from projectq.cengines import DummyEngine
from projectq.meta import LogicalQubitIDTag
from projectq.ops import (
    Allocate,
    BasicGate,
    CNOT,
    Command,
    Deallocate,
    FlushGate,
    QFT,
    X,
)
from projectq.types import WeakQubitRef

from projectq.cengines import _linearmapper as lm


def test_return_swap_depth():
    swaps = []
    assert lm.return_swap_depth(swaps) == 0
    swaps += [(0, 1), (0, 1), (1, 2)]
    assert lm.return_swap_depth(swaps) == 3
    swaps.append((2, 3))
    assert lm.return_swap_depth(swaps) == 4


def test_is_available():
    mapper = lm.LinearMapper(num_qubits=5, cyclic=False)
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


def test_return_new_mapping_too_many_qubits():
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    cmd0 = Command(None, QFT, qubits=([qb0], [qb1, qb2]))
    mapper._stored_commands = [cmd0]
    with pytest.raises(Exception):
        mapper.return_new_mapping(
            num_qubits=mapper.num_qubits,
            cyclic=mapper.cyclic,
            currently_allocated_ids=mapper._currently_allocated_ids,
            stored_commands=mapper._stored_commands,
            current_mapping=mapper.current_mapping,
        )
    cmd1 = Command(None, BasicGate(), qubits=([],))
    mapper._stored_commands = [cmd1]
    with pytest.raises(Exception):
        mapper.return_new_mapping(
            num_qubits=mapper.num_qubits,
            cyclic=mapper.cyclic,
            currently_allocated_ids=mapper._currently_allocated_ids,
            stored_commands=mapper._stored_commands,
            current_mapping=mapper.current_mapping,
        )


def test_return_new_mapping_allocate_qubits():
    mapper = lm.LinearMapper(num_qubits=2, cyclic=False)
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    mapper._currently_allocated_ids = set([4])
    cmd0 = Command(None, Allocate, ([qb0],))
    cmd1 = Command(None, Allocate, ([qb1],))
    mapper._stored_commands = [cmd0, cmd1]
    new_mapping = mapper.return_new_mapping(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        currently_allocated_ids=mapper._currently_allocated_ids,
        stored_commands=mapper._stored_commands,
        current_mapping=mapper.current_mapping,
    )
    assert mapper._currently_allocated_ids == set([4])
    assert mapper._stored_commands == [cmd0, cmd1]
    assert len(new_mapping) == 2
    assert 4 in new_mapping and 0 in new_mapping


def test_return_new_mapping_allocate_only_once():
    mapper = lm.LinearMapper(num_qubits=1, cyclic=False)
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)  # noqa: F841
    mapper._currently_allocated_ids = set()
    cmd0 = Command(None, Allocate, ([qb0],))
    cmd1 = Command(None, Deallocate, ([qb0],))
    # Test if loop stops after deallocate gate has been used.
    # This would otherwise trigger an error (test by num_qubits=2)
    cmd2 = None
    mapper._stored_commands = [cmd0, cmd1, cmd2]
    mapper.return_new_mapping(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        currently_allocated_ids=mapper._currently_allocated_ids,
        stored_commands=mapper._stored_commands,
        current_mapping=mapper.current_mapping,
    )


def test_return_new_mapping_possible_map():
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    cmd0 = Command(None, Allocate, ([qb0],))
    cmd1 = Command(None, Allocate, ([qb1],))
    cmd2 = Command(None, Allocate, ([qb2],))
    cmd3 = Command(None, CNOT, qubits=([qb0],), controls=[qb1])
    cmd4 = Command(None, CNOT, qubits=([qb2],), controls=[qb1])
    cmd5 = Command(None, X, qubits=([qb0],))
    mapper._stored_commands = [cmd0, cmd1, cmd2, cmd3, cmd4, cmd5]
    new_mapping = mapper.return_new_mapping(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        currently_allocated_ids=mapper._currently_allocated_ids,
        stored_commands=mapper._stored_commands,
        current_mapping=mapper.current_mapping,
    )
    assert new_mapping == {0: 2, 1: 1, 2: 0} or new_mapping == {0: 0, 1: 1, 2: 2}


def test_return_new_mapping_previous_error():
    mapper = lm.LinearMapper(num_qubits=2, cyclic=False)
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=3)
    cmd0 = Command(None, Allocate, ([qb0],))
    cmd1 = Command(None, Allocate, ([qb1],))
    cmd2 = Command(None, Allocate, ([qb2],))
    cmd3 = Command(None, Allocate, ([qb3],))
    cmd4 = Command(None, CNOT, qubits=([qb2],), controls=[qb3])
    mapper._stored_commands = [cmd0, cmd1, cmd2, cmd3, cmd4]
    mapper.return_new_mapping(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        currently_allocated_ids=mapper._currently_allocated_ids,
        stored_commands=mapper._stored_commands,
        current_mapping=mapper.current_mapping,
    )


def test_process_two_qubit_gate_not_in_segments_test0():
    mapper = lm.LinearMapper(num_qubits=5, cyclic=False)
    segments = [[0, 1]]
    active_qubits = set([0, 1, 4, 6])
    neighbour_ids = {0: set([1]), 1: set([0]), 4: set(), 6: set()}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=4,
        qubit1=6,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert len(segments) == 2
    assert segments[0] == [0, 1]
    assert segments[1] == [4, 6]
    assert neighbour_ids[4] == set([6])
    assert neighbour_ids[6] == set([4])
    assert active_qubits == set([0, 1, 4, 6])


def test_process_two_qubit_gate_not_in_segments_test1():
    mapper = lm.LinearMapper(num_qubits=5, cyclic=False)
    segments = []
    active_qubits = set([4, 6])
    neighbour_ids = {4: set(), 6: set()}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=5,
        qubit1=6,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert len(segments) == 0
    assert active_qubits == set([4])


@pytest.mark.parametrize("qb0, qb1", [(1, 2), (2, 1)])
def test_process_two_qubit_gate_one_qb_free_one_qb_in_segment(qb0, qb1):
    # add on the right to segment
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    segments = [[0, 1]]
    active_qubits = set([0, 1, 2])
    neighbour_ids = {0: set([1]), 1: set([0]), 2: set()}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=qb0,
        qubit1=qb1,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [[0, 1, 2]]
    assert active_qubits == set([0, 1, 2])
    assert neighbour_ids[1] == set([0, 2])
    assert neighbour_ids[2] == set([1])


@pytest.mark.parametrize("qb0, qb1", [(0, 1), (1, 0)])
def test_process_two_qubit_gate_one_qb_free_one_qb_in_segment2(qb0, qb1):
    # add on the left to segment
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    segments = [[1, 2]]
    active_qubits = set([0, 1, 2])
    neighbour_ids = {0: set([]), 1: set([2]), 2: set([1])}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=qb0,
        qubit1=qb1,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [[0, 1, 2]]
    assert active_qubits == set([0, 1, 2])
    assert neighbour_ids[1] == set([0, 2])
    assert neighbour_ids[0] == set([1])


@pytest.mark.parametrize("qb0, qb1", [(1, 2), (2, 1)])
def test_process_two_qubit_gate_one_qb_free_one_qb_in_segment_cycle(qb0, qb1):
    mapper = lm.LinearMapper(num_qubits=3, cyclic=True)
    segments = [[0, 1]]
    active_qubits = set([0, 1, 2])
    neighbour_ids = {0: set([1]), 1: set([0]), 2: set()}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=qb0,
        qubit1=qb1,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [[0, 1, 2]]
    assert active_qubits == set([0, 1, 2])
    assert neighbour_ids[1] == set([0, 2])
    assert neighbour_ids[2] == set([1, 0])


@pytest.mark.parametrize("qb0, qb1", [(1, 2), (2, 1)])
def test_process_two_qubit_gate_one_qb_free_one_qb_in_seg_cycle2(qb0, qb1):
    # not yet long enough segment for cycle
    mapper = lm.LinearMapper(num_qubits=4, cyclic=True)
    segments = [[0, 1]]
    active_qubits = set([0, 1, 2])
    neighbour_ids = {0: set([1]), 1: set([0]), 2: set()}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=qb0,
        qubit1=qb1,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [[0, 1, 2]]
    assert active_qubits == set([0, 1, 2])
    assert neighbour_ids[1] == set([0, 2])
    assert neighbour_ids[2] == set([1])


def test_process_two_qubit_gate_one_qubit_in_middle_of_segment():
    mapper = lm.LinearMapper(num_qubits=5, cyclic=False)
    segments = []
    active_qubits = set([0, 1, 2, 3])
    neighbour_ids = {0: set([1]), 1: set([0, 2]), 2: set([1]), 3: set()}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=1,
        qubit1=3,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert len(segments) == 0
    assert active_qubits == set([0, 2])


def test_process_two_qubit_gate_both_in_same_segment():
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    segments = [[0, 1, 2]]
    active_qubits = set([0, 1, 2])
    neighbour_ids = {0: set([1]), 1: set([0, 2]), 2: set([1])}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=0,
        qubit1=2,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [[0, 1, 2]]
    assert active_qubits == set([1])


def test_process_two_qubit_gate_already_connected():
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    segments = [[0, 1, 2]]
    active_qubits = set([0, 1, 2])
    neighbour_ids = {0: set([1]), 1: set([0, 2]), 2: set([1])}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=0,
        qubit1=1,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [[0, 1, 2]]
    assert active_qubits == set([0, 1, 2])


@pytest.mark.parametrize(
    "qb0, qb1, result_seg",
    [
        (0, 2, [1, 0, 2, 3]),
        (0, 3, [2, 3, 0, 1]),
        (1, 2, [0, 1, 2, 3]),
        (1, 3, [0, 1, 3, 2]),
    ],
)
def test_process_two_qubit_gate_combine_segments(qb0, qb1, result_seg):
    mapper = lm.LinearMapper(num_qubits=4, cyclic=False)
    segments = [[0, 1], [2, 3]]
    active_qubits = set([0, 1, 2, 3, 4])
    neighbour_ids = {0: set([1]), 1: set([0]), 2: set([3]), 3: set([2])}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=qb0,
        qubit1=qb1,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [result_seg] or segments == [reversed(result_seg)]
    assert qb1 in neighbour_ids[qb0]
    assert qb0 in neighbour_ids[qb1]


@pytest.mark.parametrize(
    "qb0, qb1, result_seg",
    [
        (0, 2, [1, 0, 2, 3]),
        (0, 3, [2, 3, 0, 1]),
        (1, 2, [0, 1, 2, 3]),
        (1, 3, [0, 1, 3, 2]),
    ],
)
def test_process_two_qubit_gate_combine_segments_cycle(qb0, qb1, result_seg):
    mapper = lm.LinearMapper(num_qubits=4, cyclic=True)
    segments = [[0, 1], [2, 3]]
    active_qubits = set([0, 1, 2, 3, 4])
    neighbour_ids = {0: set([1]), 1: set([0]), 2: set([3]), 3: set([2])}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=qb0,
        qubit1=qb1,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [result_seg] or segments == [reversed(result_seg)]
    assert qb1 in neighbour_ids[qb0]
    assert qb0 in neighbour_ids[qb1]
    assert result_seg[0] in neighbour_ids[result_seg[-1]]
    assert result_seg[-1] in neighbour_ids[result_seg[0]]


@pytest.mark.parametrize(
    "qb0, qb1, result_seg",
    [
        (0, 2, [1, 0, 2, 3]),
        (0, 3, [2, 3, 0, 1]),
        (1, 2, [0, 1, 2, 3]),
        (1, 3, [0, 1, 3, 2]),
    ],
)
def test_process_two_qubit_gate_combine_segments_cycle2(qb0, qb1, result_seg):
    # Not long enough segment for cyclic
    mapper = lm.LinearMapper(num_qubits=5, cyclic=True)
    segments = [[0, 1], [2, 3]]
    active_qubits = set([0, 1, 2, 3, 4])
    neighbour_ids = {0: set([1]), 1: set([0]), 2: set([3]), 3: set([2])}
    mapper._process_two_qubit_gate(
        num_qubits=mapper.num_qubits,
        cyclic=mapper.cyclic,
        qubit0=qb0,
        qubit1=qb1,
        active_qubits=active_qubits,
        segments=segments,
        neighbour_ids=neighbour_ids,
    )
    assert segments == [result_seg] or segments == [reversed(result_seg)]
    assert qb1 in neighbour_ids[qb0]
    assert qb0 in neighbour_ids[qb1]
    assert result_seg[0] not in neighbour_ids[result_seg[-1]]
    assert result_seg[-1] not in neighbour_ids[result_seg[0]]


@pytest.mark.parametrize(
    "segments, current_chain, correct_chain, allocated_qubits",
    [
        ([[0, 2, 4]], [0, 1, 2, 3, 4], [0, 2, 4, 3, 1], [0, 1, 2, 3, 4]),
        ([[0, 2, 4]], [0, 1, 2, 3, 4], [0, 2, 4, 3, None], [0, 2, 3, 4]),
        ([[1, 2], [3, 0]], [0, 1, 2, 3, 4], [None, 1, 2, 3, 0], [0, 1, 2, 3]),
        ([[1, 2], [3, 0]], [0, 1, 2, 3, 4], [1, 2, 3, 0, 4], [0, 1, 2, 3, 4]),
    ],
)
def test_return_new_mapping_from_segments(segments, current_chain, correct_chain, allocated_qubits):
    mapper = lm.LinearMapper(num_qubits=5, cyclic=False)
    current_mapping = dict()
    for pos, logical_id in enumerate(current_chain):
        current_mapping[logical_id] = pos
    mapper.current_mapping = current_mapping
    new_mapping = mapper._return_new_mapping_from_segments(
        num_qubits=mapper.num_qubits,
        segments=segments,
        allocated_qubits=allocated_qubits,
        current_mapping=mapper.current_mapping,
    )
    correct_mapping = dict()
    for pos, logical_id in enumerate(correct_chain):
        if logical_id is not None:
            correct_mapping[logical_id] = pos
    assert correct_mapping == new_mapping


@pytest.mark.parametrize(
    "old_chain, new_chain",
    [
        ([0, 1, 2, 3, 4], [4, 3, 2, 1, 0]),
        ([2, 0, 14, 44, 12], [14, 12, 44, 0, 2]),
        ([2, None, 14, 44, 12], [14, 1, 44, 0, 2]),
        ([2, None, 14, 44, 12], [14, None, 44, 0, 2]),
    ],
)
def test_odd_even_transposition_sort_swaps(old_chain, new_chain):
    mapper = lm.LinearMapper(num_qubits=5, cyclic=False)
    old_map = dict()
    new_map = dict()
    for pos, logical_id in enumerate(old_chain):
        if logical_id is not None:
            old_map[logical_id] = pos
    for pos, logical_id in enumerate(new_chain):
        if logical_id is not None:
            new_map[logical_id] = pos
    swaps = mapper._odd_even_transposition_sort_swaps(old_map, new_map)
    sorted_chain = deepcopy(old_chain)
    # Remove all ids which are not in new_chain by None
    for i in range(len(sorted_chain)):
        if sorted_chain[i] not in new_chain:
            sorted_chain[i] = None
    for i, j in swaps:
        tmp = sorted_chain[i]
        sorted_chain[i] = sorted_chain[j]
        sorted_chain[j] = tmp
    assert len(sorted_chain) == len(new_chain)
    for i in range(len(sorted_chain)):
        if sorted_chain[i] is not None:
            assert sorted_chain[i] == new_chain[i]


def test_send_possible_commands_allocate():
    mapper = lm.LinearMapper(num_qubits=4, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],), controls=[], tags=[])
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
    assert len(backend.received_commands) == 1
    assert backend.received_commands[0].gate == Allocate
    assert backend.received_commands[0].qubits[0][0].id == 3
    assert backend.received_commands[0].tags == [LogicalQubitIDTag(0)]
    assert mapper._currently_allocated_ids == set([10, 0])


def test_send_possible_commands_deallocate():
    mapper = lm.LinearMapper(num_qubits=4, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(engine=None, gate=Deallocate, qubits=([qb0],), controls=[], tags=[])
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
    assert backend.received_commands[0].gate == Deallocate
    assert backend.received_commands[0].qubits[0][0].id == 3
    assert backend.received_commands[0].tags == [LogicalQubitIDTag(0)]
    assert len(mapper._stored_commands) == 0
    assert mapper.current_mapping == dict()
    assert mapper._currently_allocated_ids == set([10])


def test_send_possible_commands_keep_remaining_gates():
    mapper = lm.LinearMapper(num_qubits=4, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],), controls=[], tags=[])
    cmd1 = Command(engine=None, gate=Deallocate, qubits=([qb0],), controls=[], tags=[])
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb1],), controls=[], tags=[])

    mapper._stored_commands = [cmd0, cmd1, cmd2]
    mapper.current_mapping = {0: 0}
    mapper._send_possible_commands()
    assert mapper._stored_commands == [cmd2]


def test_send_possible_commands_not_cyclic():
    mapper = lm.LinearMapper(num_qubits=4, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=3)
    mapper._currently_allocated_ids = set([0, 1, 2, 3])
    cmd0 = Command(None, CNOT, qubits=([qb0],), controls=[qb2])
    cmd1 = Command(None, CNOT, qubits=([qb1],), controls=[qb2])
    cmd2 = Command(None, CNOT, qubits=([qb1],), controls=[qb3])
    cmd3 = Command(None, X, qubits=([qb0],), controls=[])
    mapper._stored_commands = [cmd0, cmd1, cmd2, cmd3]
    # Following chain 0 <-> 2 <-> 3 <-> 1
    mapper.current_mapping = {0: 0, 2: 1, 3: 2, 1: 3}
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 2
    assert backend.received_commands[0] == Command(None, CNOT, qubits=([qb0],), controls=[qb1])
    assert backend.received_commands[1] == Command(None, X, qubits=([qb0],))
    # Following chain 0 <-> 2 <-> 1 <-> 3
    mapper.current_mapping = {0: 0, 2: 1, 3: 3, 1: 2}
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 4
    assert len(mapper._stored_commands) == 0


def test_send_possible_commands_cyclic():
    mapper = lm.LinearMapper(num_qubits=4, cyclic=True)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=3)
    mapper._currently_allocated_ids = set([0, 1, 2, 3])
    cmd0 = Command(None, CNOT, qubits=([qb0],), controls=[qb1])
    cmd1 = Command(None, CNOT, qubits=([qb1],), controls=[qb2])
    cmd2 = Command(None, CNOT, qubits=([qb1],), controls=[qb3])
    cmd3 = Command(None, X, qubits=([qb0],), controls=[])
    mapper._stored_commands = [cmd0, cmd1, cmd2, cmd3]
    # Following chain 0 <-> 2 <-> 3 <-> 1
    mapper.current_mapping = {0: 0, 2: 1, 3: 2, 1: 3}
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 2
    assert backend.received_commands[0] == Command(None, CNOT, qubits=([qb0],), controls=[qb3])
    assert backend.received_commands[1] == Command(None, X, qubits=([qb0],))
    # Following chain 0 <-> 2 <-> 1 <-> 3
    mapper.current_mapping = {0: 0, 2: 1, 3: 3, 1: 2}
    mapper._send_possible_commands()
    assert len(backend.received_commands) == 4
    assert len(mapper._stored_commands) == 0


def test_run_and_receive():
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1],))
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb2],))
    cmd3 = Command(None, X, qubits=([qb0],), controls=[qb1])
    cmd4 = Command(None, X, qubits=([qb1],), controls=[qb2])
    cmd5 = Command(engine=None, gate=Deallocate, qubits=([qb1],))
    mapper.receive([cmd0, cmd1, cmd2, cmd3, cmd4, cmd5])
    assert mapper._stored_commands == [cmd0, cmd1, cmd2, cmd3, cmd4, cmd5]
    qb3 = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb3],))
    mapper.receive([cmd_flush])
    assert mapper._stored_commands == []
    assert len(backend.received_commands) == 7
    assert mapper._currently_allocated_ids == set([0, 2])
    assert mapper.current_mapping == {0: 2, 2: 0} or mapper.current_mapping == {
        0: 0,
        2: 2,
    }
    cmd6 = Command(None, X, qubits=([qb0],), controls=[qb2])
    mapper.storage = 1
    mapper.receive([cmd6])
    assert mapper._currently_allocated_ids == set([0, 2])
    assert mapper._stored_commands == []
    assert len(mapper.current_mapping) == 2
    assert 0 in mapper.current_mapping
    assert 2 in mapper.current_mapping
    assert len(backend.received_commands) == 11
    for cmd in backend.received_commands:
        print(cmd)
    assert backend.received_commands[-1] == Command(
        None,
        X,
        qubits=([WeakQubitRef(engine=None, idx=mapper.current_mapping[qb0.id])],),
        controls=[WeakQubitRef(engine=None, idx=mapper.current_mapping[qb2.id])],
    )
    assert mapper.num_mappings == 1


def test_run_infinite_loop_detection():
    mapper = lm.LinearMapper(num_qubits=1, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1],))
    cmd2 = Command(None, X, qubits=([qb0],), controls=[qb1])
    qb2 = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb2],))
    with pytest.raises(RuntimeError):
        mapper.receive([cmd0, cmd1, cmd2, cmd_flush])


def test_logical_id_tags_allocate_and_deallocate():
    mapper = lm.LinearMapper(num_qubits=4, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1],))
    cmd2 = Command(None, X, qubits=([qb0],), controls=[qb1])
    cmd3 = Command(engine=None, gate=Deallocate, qubits=([qb0],))
    cmd4 = Command(engine=None, gate=Deallocate, qubits=([qb1],))
    mapper.current_mapping = {0: 0, 1: 3}
    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush],))
    mapper.receive([cmd0, cmd1, cmd2, cmd_flush])
    assert backend.received_commands[0].gate == Allocate
    assert backend.received_commands[0].qubits[0][0].id == 0
    assert backend.received_commands[0].tags == [LogicalQubitIDTag(0)]
    assert backend.received_commands[1].gate == Allocate
    assert backend.received_commands[1].qubits[0][0].id == 3
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


def test_send_possible_cmds_before_new_mapping():
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend

    def dont_call_mapping():
        raise Exception

    mapper._return_new_mapping = dont_call_mapping
    mapper.current_mapping = {0: 1}
    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],))
    qb2 = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb2],))
    mapper.receive([cmd0, cmd_flush])


def test_correct_stats():
    # Should test stats for twice same mapping but depends on heuristic
    mapper = lm.LinearMapper(num_qubits=3, cyclic=False)
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],))
    cmd1 = Command(engine=None, gate=Allocate, qubits=([qb1],))
    cmd2 = Command(engine=None, gate=Allocate, qubits=([qb2],))
    cmd3 = Command(None, X, qubits=([qb0],), controls=[qb1])
    cmd4 = Command(None, X, qubits=([qb1],), controls=[qb2])
    cmd5 = Command(None, X, qubits=([qb0],), controls=[qb2])
    cmd6 = Command(None, X, qubits=([qb2],), controls=[qb1])
    cmd7 = Command(None, X, qubits=([qb0],), controls=[qb1])
    cmd8 = Command(None, X, qubits=([qb1],), controls=[qb2])
    qb_flush = WeakQubitRef(engine=None, idx=-1)
    cmd_flush = Command(engine=None, gate=FlushGate(), qubits=([qb_flush],))
    mapper.receive([cmd0, cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7, cmd8, cmd_flush])
    assert mapper.num_mappings == 2
