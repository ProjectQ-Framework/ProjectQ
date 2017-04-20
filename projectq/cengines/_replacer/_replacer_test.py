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

"""Tests for projectq.cengines._replacer._replacer.py."""

import pytest

from projectq import MainEngine
from projectq.cengines import (DummyEngine,
                               DecompositionRuleSet,
                               DecompositionRule)
from projectq.ops import H, X, Command, S, Rx, NotInvertible, Ry, BasicGate

from projectq.cengines._replacer import _replacer


def test_filter_engine():
    def my_filter(self, cmd):
        if cmd.gate == H:
            return True
        return False
    filter_eng = _replacer.InstructionFilter(my_filter)
    eng = MainEngine(backend=DummyEngine(), engine_list=[filter_eng])
    qubit = eng.allocate_qubit()
    cmd = Command(eng, H, (qubit,))
    cmd2 = Command(eng, X, (qubit,))
    assert eng.is_available(cmd)
    assert not eng.is_available(cmd2)
    assert filter_eng.is_available(cmd)
    assert not filter_eng.is_available(cmd2)


class TestGate(BasicGate):
    """ Test gate class """


TestGate = TestGate()


def make_decomposition_rule_set():
    result = DecompositionRuleSet()
    # BasicGate with no get_inverse used for testing:
    with pytest.raises(NotInvertible):
        TestGate.get_inverse()

    # Loading of decomposition rules:
    def decompose_test1(cmd):
        qb = cmd.qubits
        X | qb

    def recognize_test(cmd):
        return True

    result.add_decomposition_rule(
        DecompositionRule(TestGate.__class__, decompose_test1,
                          recognize_test))

    def decompose_test2(cmd):
        qb = cmd.qubits
        H | qb

    result.add_decomposition_rule(
        DecompositionRule(TestGate.__class__, decompose_test2,
                          recognize_test))

    assert len(result.decompositions[TestGate.__class__.__name__]) == 2
    return result

rule_set = make_decomposition_rule_set()


@pytest.fixture()
def fixture_gate_filter():
    # Filter which doesn't allow TestGate
    def test_gate_filter_func(self, cmd):
        if cmd.gate == TestGate:
            return False
        return True
    return _replacer.InstructionFilter(test_gate_filter_func)


def test_auto_replacer_default_chooser(fixture_gate_filter):
    # Test that default decomposition_chooser takes always first rule.
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_replacer.AutoReplacer(rule_set),
                                  fixture_gate_filter])
    assert len(rule_set.decompositions[TestGate.__class__.__name__]) == 2
    assert len(backend.received_commands) == 0
    qb = eng.allocate_qubit()
    TestGate | qb
    eng.flush()
    assert len(backend.received_commands) == 3
    assert backend.received_commands[1].gate == X


def test_auto_replacer_decomposition_chooser(fixture_gate_filter):
    # Supply a decomposition chooser which always chooses last rule.
    def test_decomp_chooser(cmd, decomposition_list):
        return decomposition_list[-1]
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_replacer.AutoReplacer(rule_set,
                                                         test_decomp_chooser),
                                  fixture_gate_filter])
    assert len(rule_set.decompositions[TestGate.__class__.__name__]) == 2
    assert len(backend.received_commands) == 0
    qb = eng.allocate_qubit()
    TestGate | qb
    eng.flush()
    assert len(backend.received_commands) == 3
    assert backend.received_commands[1].gate == H


def test_auto_replacer_no_rule_found():
    # Check that exception is thrown if no rule is found
    # For both the cmd and it's inverse (which exists)
    def h_filter(self, cmd):
        if cmd.gate == H:
            return False
        return True
    h_filter = _replacer.InstructionFilter(h_filter)
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_replacer.AutoReplacer(rule_set), h_filter])
    qubit = eng.allocate_qubit()
    with pytest.raises(_replacer.NoGateDecompositionError):
        H | qubit
    eng.flush()


def test_auto_replacer_use_inverse_decomposition():
    # Check that if there is no decomposition for the gate, that
    # AutoReplacer runs the decomposition for the inverse gate in reverse

    # Create test gate and inverse
    class NoMagicGate(BasicGate):
        pass

    class MagicGate(BasicGate):
        def get_inverse(self):
            return NoMagicGate()

    def decompose_no_magic_gate(cmd):
        qb = cmd.qubits
        Rx(0.6) | qb
        H | qb

    def recognize_no_magic_gate(cmd):
        return True

    rule_set.add_decomposition_rule(DecompositionRule(NoMagicGate,
                                                      decompose_no_magic_gate,
                                                      recognize_no_magic_gate))

    def magic_filter(self, cmd):
        if cmd.gate == MagicGate():
            return False
        return True

    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_replacer.AutoReplacer(rule_set),
                                  _replacer.InstructionFilter(magic_filter)])
    assert len(backend.received_commands) == 0
    qb = eng.allocate_qubit()
    MagicGate() | qb
    eng.flush()
    for cmd in backend.received_commands:
        print(cmd)
    assert len(backend.received_commands) == 4
    assert backend.received_commands[1].gate == H
    assert backend.received_commands[2].gate == Rx(-0.6)


def test_auto_replacer_adds_tags(fixture_gate_filter):
    # Test that AutoReplacer puts back the tags
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=backend,
                     engine_list=[_replacer.AutoReplacer(rule_set),
                                  fixture_gate_filter])
    assert len(rule_set.decompositions[TestGate.__class__.__name__]) == 2
    assert len(backend.received_commands) == 0
    qb = eng.allocate_qubit()
    cmd = Command(eng, TestGate, (qb,))
    cmd.tags = ["AddedTag"]
    eng.send([cmd])
    eng.flush()
    assert len(backend.received_commands) == 3
    assert backend.received_commands[1].gate == X
    assert len(backend.received_commands[1].tags) == 1
    assert backend.received_commands[1].tags[0] == "AddedTag"
