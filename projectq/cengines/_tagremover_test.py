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

"""Tests for projectq.cengines._tagremover.py."""

from projectq import MainEngine
from projectq.meta import ComputeTag, UncomputeTag
from projectq.ops import Command, H
from projectq.cengines import DummyEngine

from projectq.cengines import _tagremover


def test_tagremover_default():
    tag_remover = _tagremover.TagRemover()
    assert tag_remover._tags == [ComputeTag, UncomputeTag]


def test_tagremover():
    backend = DummyEngine(save_commands=True)
    tag_remover = _tagremover.TagRemover([type("")])
    eng = MainEngine(backend=backend, engine_list=[tag_remover])
    # Create a command_list and check if "NewTag" is removed
    qubit = eng.allocate_qubit()
    cmd0 = Command(eng, H, (qubit,))
    cmd0.tags = ["NewTag"]
    cmd1 = Command(eng, H, (qubit,))
    cmd1.tags = [1, 2, "NewTag", 3]
    cmd_list = [cmd0, cmd1, cmd0]
    assert len(backend.received_commands) == 1  # AllocateQubitGate
    tag_remover.receive(cmd_list)
    assert len(backend.received_commands) == 4
    assert backend.received_commands[1].tags == []
    assert backend.received_commands[2].tags == [1, 2, 3]
