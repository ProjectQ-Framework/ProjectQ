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

"""Tests for projectq.meta._control.py"""

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import Command, H, Rx
from projectq.meta import (DirtyQubitTag,
                           ComputeTag,
                           UncomputeTag,
                           Compute,
                           Uncompute)

from projectq.meta import _control


def test_control_engine_has_compute_tag():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    test_cmd0 = Command(eng, H, (qubit,))
    test_cmd1 = Command(eng, H, (qubit,))
    test_cmd2 = Command(eng, H, (qubit,))
    test_cmd0.tags = [DirtyQubitTag(), ComputeTag(), DirtyQubitTag()]
    test_cmd1.tags = [DirtyQubitTag(), UncomputeTag(), DirtyQubitTag()]
    test_cmd2.tags = [DirtyQubitTag()]
    control_eng = _control.ControlEngine("MockEng")
    assert control_eng._has_compute_uncompute_tag(test_cmd0)
    assert control_eng._has_compute_uncompute_tag(test_cmd1)
    assert not control_eng._has_compute_uncompute_tag(test_cmd2)


def test_control():
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend, engine_list=[DummyEngine()])
    qureg = eng.allocate_qureg(2)
    with _control.Control(eng, qureg):
        qubit = eng.allocate_qubit()
        with Compute(eng):
            Rx(0.5) | qubit
        H | qubit
        Uncompute(eng)
    with _control.Control(eng, qureg[0]):
        H | qubit
    eng.flush()
    assert len(backend.received_commands) == 8
    assert len(backend.received_commands[0].control_qubits) == 0
    assert len(backend.received_commands[1].control_qubits) == 0
    assert len(backend.received_commands[2].control_qubits) == 0
    assert len(backend.received_commands[3].control_qubits) == 0
    assert len(backend.received_commands[4].control_qubits) == 2
    assert len(backend.received_commands[5].control_qubits) == 0
    assert len(backend.received_commands[6].control_qubits) == 1
    assert len(backend.received_commands[7].control_qubits) == 0
    assert backend.received_commands[4].control_qubits[0].id == qureg[0].id
    assert backend.received_commands[4].control_qubits[1].id == qureg[1].id
    assert backend.received_commands[6].control_qubits[0].id == qureg[0].id
