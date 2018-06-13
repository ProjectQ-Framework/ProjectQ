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

"""
Tests for projectq.backends._printer.py.
"""

import pytest

from projectq import MainEngine
from projectq.cengines import (DummyEngine,
                               InstructionFilter,
                               NotYetMeasuredError)
from projectq.meta import LogicalQubitIDTag
from projectq.ops import Allocate, Command, H, Measure, NOT, T
from projectq.types import WeakQubitRef

from projectq.backends import _printer


def test_command_printer_is_available():
    inline_cmd_printer = _printer.CommandPrinter()
    cmd_printer = _printer.CommandPrinter()

    def available_cmd(self, cmd):
        return cmd.gate == H
    filter = InstructionFilter(available_cmd)
    eng = MainEngine(backend=cmd_printer,
                     engine_list=[inline_cmd_printer, filter])
    qubit = eng.allocate_qubit()
    cmd0 = Command(eng, H, (qubit,))
    cmd1 = Command(eng, T, (qubit,))
    assert inline_cmd_printer.is_available(cmd0)
    assert not inline_cmd_printer.is_available(cmd1)
    assert cmd_printer.is_available(cmd0)
    assert cmd_printer.is_available(cmd1)


def test_command_printer_accept_input(monkeypatch):
    cmd_printer = _printer.CommandPrinter()
    eng = MainEngine(backend=cmd_printer, engine_list=[DummyEngine()])
    monkeypatch.setattr(_printer, "input", lambda x: 1)
    qubit = eng.allocate_qubit()
    Measure | qubit
    assert int(qubit) == 1
    monkeypatch.setattr(_printer, "input", lambda x: 0)
    qubit = eng.allocate_qubit()
    NOT | qubit
    Measure | qubit
    assert int(qubit) == 0


def test_command_printer_no_input_default_measure():
    cmd_printer = _printer.CommandPrinter(accept_input=False)
    eng = MainEngine(backend=cmd_printer, engine_list=[DummyEngine()])
    qubit = eng.allocate_qubit()
    NOT | qubit
    Measure | qubit
    assert int(qubit) == 0


def test_command_printer_measure_mapped_qubit():
    eng = MainEngine(_printer.CommandPrinter(accept_input=False), [])
    qb1 = WeakQubitRef(engine=eng, idx=1)
    qb2 = WeakQubitRef(engine=eng, idx=2)
    cmd0 = Command(engine=eng, gate=Allocate, qubits=([qb1],))
    cmd1 = Command(engine=eng, gate=Measure, qubits=([qb1],), controls=[],
                   tags=[LogicalQubitIDTag(2)])
    with pytest.raises(NotYetMeasuredError):
        int(qb1)
    with pytest.raises(NotYetMeasuredError):
        int(qb2)
    eng.send([cmd0, cmd1])
    eng.flush()
    with pytest.raises(NotYetMeasuredError):
        int(qb1)
    assert int(qb2) == 0
