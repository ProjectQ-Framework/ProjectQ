#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
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

"""Tests for projectq.cengines._cmdmodifier.py."""

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import H, FastForwardingGate, ClassicalInstructionGate

from projectq.cengines import _cmdmodifier


def test_command_modifier():
    def cmd_mod_fun(cmd):
        cmd.tags = "NewTag"
        return cmd

    backend = DummyEngine(save_commands=True)
    cmd_modifier = _cmdmodifier.CommandModifier(cmd_mod_fun)
    main_engine = MainEngine(backend=backend, engine_list=[cmd_modifier])
    qubit = main_engine.allocate_qubit()
    H | qubit
    # Test if H gate was sent through forwarder_eng and tag was added
    received_commands = []
    # Remove Allocate and Deallocate gates
    for cmd in backend.received_commands:
        if not (isinstance(cmd.gate, FastForwardingGate) or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            received_commands.append(cmd)
    for cmd in received_commands:
        print(cmd)
    assert len(received_commands) == 1
    assert received_commands[0].gate == H
    assert received_commands[0].tags == "NewTag"
