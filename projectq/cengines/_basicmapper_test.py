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
"""Tests for projectq.cengines._basicmapper.py."""

from projectq.cengines import DummyEngine
from projectq.meta import LogicalQubitIDTag
from projectq.ops import Allocate, BasicGate, Command, Deallocate, FlushGate, Measure
from projectq.types import WeakQubitRef

from projectq.cengines import _basicmapper


def test_basic_mapper_engine_send_cmd_with_mapped_ids():
    mapper = _basicmapper.BasicMapperEngine()
    mapper.current_mapping = {0: 3, 1: 2, 2: 1, 3: 0}
    backend = DummyEngine(save_commands=True)
    backend.is_last_engine = True
    mapper.next_engine = backend
    # generate a few commands
    qb0 = WeakQubitRef(engine=None, idx=0)
    qb1 = WeakQubitRef(engine=None, idx=1)
    qb2 = WeakQubitRef(engine=None, idx=2)
    qb3 = WeakQubitRef(engine=None, idx=3)
    cmd0 = Command(engine=None, gate=Allocate, qubits=([qb0],), controls=[], tags=[])
    cmd1 = Command(engine=None, gate=Deallocate, qubits=([qb1],), controls=[], tags=[])
    cmd2 = Command(engine=None, gate=Measure, qubits=([qb2],), controls=[], tags=["SomeTag"])
    cmd3 = Command(
        engine=None,
        gate=BasicGate(),
        qubits=([qb0, qb1], [qb2]),
        controls=[qb3],
        tags=[],
    )
    cmd4 = Command(None, FlushGate(), ([WeakQubitRef(None, -1)],))
    mapper._send_cmd_with_mapped_ids(cmd0)
    mapper._send_cmd_with_mapped_ids(cmd1)
    mapper._send_cmd_with_mapped_ids(cmd2)
    mapper._send_cmd_with_mapped_ids(cmd3)
    mapper._send_cmd_with_mapped_ids(cmd4)
    rcmd0 = backend.received_commands[0]
    rcmd1 = backend.received_commands[1]
    rcmd2 = backend.received_commands[2]
    rcmd3 = backend.received_commands[3]
    rcmd4 = backend.received_commands[4]
    assert rcmd0.gate == Allocate
    assert rcmd0.qubits == ([qb3],)
    assert rcmd1.gate == Deallocate
    assert rcmd1.qubits == ([qb2],)
    assert rcmd2.gate == Measure
    assert rcmd2.qubits == ([qb1],)
    assert rcmd2.tags == ["SomeTag", LogicalQubitIDTag(2)]
    assert rcmd3.gate == BasicGate()
    assert rcmd3.qubits == ([qb3, qb2], [qb1])
    assert rcmd3.control_qubits == [qb0]
    assert len(rcmd4.qubits) == 1
    assert len(rcmd4.qubits[0]) == 1
    assert rcmd4.qubits[0][0].id == -1
