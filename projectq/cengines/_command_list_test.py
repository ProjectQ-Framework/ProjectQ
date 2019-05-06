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
"""Tests for projectq.cengines._command_list.py."""

from projectq.cengines._command_list import CommandList

from copy import deepcopy
import pytest
from projectq.ops import (Allocate, Command, X)
from projectq.types import WeakQubitRef

# ==============================================================================


def allocate_all_qubits_cmd(num_qubits):
    qb = []
    allocate_cmds = []
    for i in range(num_qubits):
        qb.append(WeakQubitRef(engine=None, idx=i))
        allocate_cmds.append(
            Command(engine=None, gate=Allocate, qubits=([qb[i]], )))
    return qb, allocate_cmds


# ==============================================================================


@pytest.fixture
def command_list():
    return CommandList()


# ==============================================================================


def test_empty_command_list(command_list):
    assert not command_list
    assert command_list._cmds == []
    assert command_list.partitions == [set()]


def test_append_single_qubit_gate(command_list):
    assert not command_list

    qb0 = WeakQubitRef(engine=None, idx=0)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0], ))
    command_list.append(cmd0)
    assert command_list._cmds == [cmd0]
    assert command_list.interactions == [[]]

    cmd1 = Command(engine=None, gate=X, qubits=([qb0], ))
    command_list.append(cmd1)
    assert command_list._cmds == [cmd0, cmd1]
    assert command_list.partitions == [set()]
    assert command_list.interactions == [[]]

    assert command_list
    command_list.clear()
    assert not command_list
    assert command_list._cmds == []
    assert command_list.partitions == [set()]
    assert command_list.interactions == [[]]


def test_append_two_qubit_gate(command_list):
    assert not command_list

    qb, allocate_cmds = allocate_all_qubits_cmd(4)
    for cmd in allocate_cmds:
        command_list.append(cmd)
    assert command_list._cmds == allocate_cmds
    assert command_list.partitions == [set()]
    assert command_list.interactions == [[]]

    cmd0 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]])
    command_list.append(cmd0)
    assert command_list._cmds == allocate_cmds + [cmd0]
    assert command_list.partitions == [{0, 1}]
    assert command_list.interactions == [[(0, 1)]]

    cmd1 = Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]])
    command_list.append(cmd1)
    assert command_list._cmds == allocate_cmds + [cmd0, cmd1]
    assert command_list.partitions == [{0, 1, 2, 3}]
    assert command_list.interactions == [[(0, 1), (2, 3)]]

    cmd2 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]])
    command_list.append(cmd2)
    assert command_list._cmds == allocate_cmds + [cmd0, cmd1, cmd2]
    assert command_list.partitions == [{0, 1, 2, 3}, {0, 2}]
    assert command_list.interactions == [[(0, 1), (2, 3)], [(0, 2)]]

    assert command_list
    command_list.clear()
    assert not command_list
    assert command_list._cmds == []
    assert command_list.partitions == [set()]
    assert command_list.interactions == [[]]


def test_extend(command_list):
    assert not command_list

    qb, allocate_cmds = allocate_all_qubits_cmd(4)
    command_list.extend(allocate_cmds)
    assert command_list._cmds == allocate_cmds
    assert command_list.partitions == [set()]

    cmd0 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]])
    cmd1 = Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]])
    cmd2 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]])
    cmd3 = Command(engine=None, gate=X, qubits=([qb[1]], ))
    command_list.extend((cmd0, cmd1, cmd2, cmd3))
    assert command_list._cmds == allocate_cmds + [cmd0, cmd1, cmd2, cmd3]
    assert command_list.partitions == [{0, 1, 2, 3}, {0, 2}]
    assert command_list.interactions == [[(0, 1), (2, 3)], [(0, 2)]]


def test_iadd():
    command_list_ref = CommandList()
    command_list = CommandList()
    assert not command_list
    assert not command_list_ref

    qb, allocate_cmds = allocate_all_qubits_cmd(4)
    command_list_ref.extend(allocate_cmds)
    command_list += allocate_cmds

    assert command_list._cmds == command_list_ref._cmds
    assert command_list.partitions == command_list_ref.partitions
    assert command_list.interactions == command_list_ref.interactions

    cmd0 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]])
    cmd1 = Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]])
    cmd2 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]])
    cmd3 = Command(engine=None, gate=X, qubits=([qb[1]], ))
    command_list_ref.extend((cmd0, cmd1, cmd2, cmd3))
    command_list += (cmd0, cmd1, cmd2, cmd3)
    assert command_list._cmds == command_list_ref._cmds
    assert command_list.partitions == command_list_ref.partitions
    assert command_list.interactions == command_list_ref.interactions


def test_iter(command_list):
    assert not command_list

    for cmd in command_list:
        raise RuntimeError('ERROR')

    qb, allocate_cmds = allocate_all_qubits_cmd(4)
    command_list.extend(allocate_cmds)

    cmd0 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]])
    cmd1 = Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]])
    cmd2 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]])
    cmd3 = Command(engine=None, gate=X, qubits=([qb[1]], ))
    command_list.extend((cmd0, cmd1, cmd2, cmd3))

    for cmd, cmd_ref in zip(command_list, command_list.stored_commands):
        assert cmd == cmd_ref


def test_getitem(command_list):
    assert not command_list

    qb, allocate_cmds = allocate_all_qubits_cmd(4)
    command_list.extend(allocate_cmds)

    cmd0 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]])
    cmd1 = Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]])
    cmd2 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]])
    cmd3 = Command(engine=None, gate=X, qubits=([qb[1]], ))
    command_list.extend((cmd0, cmd1, cmd2, cmd3))

    ref_list = allocate_cmds + [cmd0, cmd1, cmd2, cmd3]
    for i in range(len(command_list)):
        assert command_list[i] == ref_list[i]

    assert command_list[4:] == ref_list[4:]


def test_eq(command_list):
    assert not command_list
    qb, allocate_cmds = allocate_all_qubits_cmd(4)
    command_list.extend(allocate_cmds)

    cmd0 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]])
    cmd1 = Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]])
    cmd2 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]])
    cmd3 = Command(engine=None, gate=X, qubits=([qb[1]], ))
    command_list.extend((cmd0, cmd1, cmd2, cmd3))

    with pytest.raises(NotImplementedError):
        assert command_list == 2
    with pytest.raises(NotImplementedError):
        assert command_list == 2.
    with pytest.raises(NotImplementedError):
        assert command_list == 'asr'

    assert command_list == allocate_cmds + [cmd0, cmd1, cmd2, cmd3]
    assert command_list != allocate_cmds

    other_list = deepcopy(command_list)
    assert command_list == other_list
    other_list.append(cmd0)
    assert command_list != other_list


def test_generate_qubit_interaction_graph(command_list):
    assert not command_list

    qb, allocate_cmds = allocate_all_qubits_cmd(9)
    command_list.extend(allocate_cmds)

    cmd0 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[1]])
    cmd1 = Command(engine=None, gate=X, qubits=([qb[2]], ), controls=[qb[3]])
    cmd2 = Command(engine=None, gate=X, qubits=([qb[0]], ), controls=[qb[2]])
    cmd3 = Command(engine=None, gate=X, qubits=([qb[1]], ))
    command_list.extend((cmd0, cmd1, cmd2, cmd3))

    subgraphs = command_list.calculate_qubit_interaction_subgraphs(order=2)
    assert len(subgraphs) == 1
    assert len(subgraphs[0]) == 4
    assert all([n in subgraphs[0] for n in [0, 1, 2, 3]])
    assert subgraphs[0][-2:] in ([1, 3], [3, 1])

    # --------------------------------------------------------------------------

    cmd4 = Command(engine=None, gate=X, qubits=([qb[4]], ), controls=[qb[5]])
    cmd5 = Command(engine=None, gate=X, qubits=([qb[5]], ), controls=[qb[6]])
    command_list.extend((cmd4, cmd5))

    subgraphs = command_list.calculate_qubit_interaction_subgraphs(order=2)
    assert len(subgraphs) == 2
    assert len(subgraphs[0]) == 4

    assert all([n in subgraphs[0] for n in [0, 1, 2, 3]])
    assert subgraphs[0][-2:] in ([1, 3], [3, 1])
    assert subgraphs[1] in ([5, 4, 6], [5, 6, 4])

    # --------------------------------------------------------------------------

    cmd6 = Command(engine=None, gate=X, qubits=([qb[6]], ), controls=[qb[7]])
    cmd7 = Command(engine=None, gate=X, qubits=([qb[7]], ), controls=[qb[8]])
    command_list.extend((cmd6, cmd7))

    subgraphs = command_list.calculate_qubit_interaction_subgraphs(order=2)

    assert len(subgraphs) == 2
    assert len(subgraphs[0]) == 5
    assert all([n in subgraphs[0] for n in [4, 5, 6, 7, 8]])
    assert subgraphs[0][-2:] in ([4, 8], [8, 4])
    assert len(subgraphs[1]) == 4
    assert all([n in subgraphs[1] for n in [0, 1, 2, 3]])
    assert subgraphs[1][-2:] in ([1, 3], [3, 1])

    # --------------------------------------------------------------------------

    command_list.append(
        Command(engine=None, gate=X, qubits=([qb[3]], ), controls=[qb[0]]))
    subgraphs = command_list.calculate_qubit_interaction_subgraphs(order=3)

    assert len(subgraphs) == 2
    assert len(subgraphs[0]) == 4
    assert all([n in subgraphs[0] for n in [0, 1, 2, 3]])
    assert subgraphs[0][0] == 0
    assert subgraphs[0][-2:] in ([1, 3], [3, 1])
    assert len(subgraphs[1]) == 5
    assert all([n in subgraphs[1] for n in [4, 5, 6, 7, 8]])
    assert subgraphs[1][-2:] in ([4, 8], [8, 4])
