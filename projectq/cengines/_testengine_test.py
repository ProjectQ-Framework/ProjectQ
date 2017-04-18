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

"""Tests for projectq.cengines._testengine.py."""
import pytest
from projectq.types import Qubit

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import (
    CNOT, H, Rx,
    C, X, Y, Z,
    Allocate, FlushGate, Measure, BasicMathGate, Toffoli
)

from projectq.cengines import _testengine
from ._testengine import LimitedCapabilityEngine


def test_compare_engine_str():
    compare_engine = _testengine.CompareEngine()
    eng = MainEngine(backend=compare_engine, engine_list=[DummyEngine()])
    qb0 = eng.allocate_qubit()
    qb1 = eng.allocate_qubit()
    H | qb0
    CNOT | (qb0, qb1)
    eng.flush()
    expected = ("Qubit 0 : Allocate | Qubit[0], H | Qubit[0], " +
                "CX | ( Qubit[0], Qubit[1] )\nQubit 1 : Allocate | Qubit[1]," +
                " CX | ( Qubit[0], Qubit[1] )\n")
    assert str(compare_engine) == expected


def test_compare_engine_is_available():
    compare_engine = _testengine.CompareEngine()
    assert compare_engine.is_available("Anything")


def test_compare_engine_receive():
    # Test that CompareEngine would forward commands
    backend = DummyEngine(save_commands=True)
    compare_engine = _testengine.CompareEngine()
    eng = MainEngine(backend=backend, engine_list=[compare_engine])
    qubit = eng.allocate_qubit()
    H | qubit
    eng.flush()
    assert len(backend.received_commands) == 3


def test_compare_engine():
    compare_engine0 = _testengine.CompareEngine()
    compare_engine1 = _testengine.CompareEngine()
    compare_engine2 = _testengine.CompareEngine()
    compare_engine3 = _testengine.CompareEngine()
    eng0 = MainEngine(backend=compare_engine0, engine_list=[DummyEngine()])
    eng1 = MainEngine(backend=compare_engine1, engine_list=[DummyEngine()])
    eng2 = MainEngine(backend=compare_engine2, engine_list=[DummyEngine()])
    eng3 = MainEngine(backend=compare_engine3, engine_list=[DummyEngine()])
    # reference circuit
    qb00 = eng0.allocate_qubit()
    qb01 = eng0.allocate_qubit()
    qb02 = eng0.allocate_qubit()
    H | qb00
    CNOT | (qb00, qb01)
    CNOT | (qb01, qb00)
    H | qb00
    Rx(0.5) | qb01
    CNOT | (qb00, qb01)
    Rx(0.6) | qb02
    eng0.flush()
    # identical circuit:
    qb10 = eng1.allocate_qubit()
    qb11 = eng1.allocate_qubit()
    qb12 = eng1.allocate_qubit()
    H | qb10
    Rx(0.6) | qb12
    CNOT | (qb10, qb11)
    CNOT | (qb11, qb10)
    Rx(0.5) | qb11
    H | qb10
    CNOT | (qb10, qb11)
    eng1.flush()
    # mistake in CNOT circuit:
    qb20 = eng2.allocate_qubit()
    qb21 = eng2.allocate_qubit()
    qb22 = eng2.allocate_qubit()
    H | qb20
    Rx(0.6) | qb22
    CNOT | (qb21, qb20)
    CNOT | (qb20, qb21)
    Rx(0.5) | qb21
    H | qb20
    CNOT | (qb20, qb21)
    eng2.flush()
    # test other branch to fail
    qb30 = eng3.allocate_qubit()
    qb31 = eng3.allocate_qubit()
    qb32 = eng3.allocate_qubit()
    eng3.flush()
    assert compare_engine0 == compare_engine1
    assert compare_engine1 != compare_engine2
    assert compare_engine1 != compare_engine3
    assert not compare_engine0 == DummyEngine()


def test_dummy_engine():
    dummy_eng = _testengine.DummyEngine(save_commands=True)
    eng = MainEngine(backend=dummy_eng, engine_list=[])
    assert dummy_eng.is_available("Anything")
    qubit = eng.allocate_qubit()
    H | qubit
    eng.flush()
    assert len(dummy_eng.received_commands) == 3
    assert dummy_eng.received_commands[0].gate == Allocate
    assert dummy_eng.received_commands[1].gate == H
    assert dummy_eng.received_commands[2].gate == FlushGate()


def test_limited_capability_engine_default():
    eng = LimitedCapabilityEngine()
    m = MainEngine(backend=DummyEngine(), engine_list=[eng])
    q = m.allocate_qureg(2)

    assert eng.is_available(Measure.generate_command(q))
    assert not eng.is_available(H.generate_command(q))
    assert not eng.is_available(Z.generate_command(q))
    assert not eng.is_available(CNOT.generate_command(tuple(q)))


def test_limited_capability_engine_classes():
    eng = LimitedCapabilityEngine(allow_classes=[H.__class__, X.__class__],
                                  ban_classes=[X.__class__, Y.__class__])
    m = MainEngine(backend=DummyEngine(), engine_list=[eng])
    q = m.allocate_qureg(5)

    assert eng.is_available(Measure.generate_command(q))  # Default.
    assert eng.is_available(H.generate_command(q))  # Allowed.
    assert not eng.is_available(X.generate_command(q))  # Ban overrides allow.
    assert not eng.is_available(Y.generate_command(q))  # Banned.
    assert not eng.is_available(Z.generate_command(q))  # Not mentioned.


def test_limited_capability_engine_arithmetic():
    default_eng = LimitedCapabilityEngine()
    eng = LimitedCapabilityEngine(allow_arithmetic=True)
    m = MainEngine(backend=DummyEngine(), engine_list=[eng])
    q = m.allocate_qureg(5)

    inc = BasicMathGate(lambda x: x + 1)
    assert not default_eng.is_available(inc.generate_command(q))
    assert eng.is_available(inc.generate_command(q))


def test_limited_capability_engine_classical_instructions():
    default_eng = LimitedCapabilityEngine()
    eng = LimitedCapabilityEngine(allow_classical_instructions=False,
                                  allow_classes=[FlushGate])
    m = MainEngine(backend=DummyEngine(), engine_list=[eng])
    with pytest.raises(ValueError):
        _ = m.allocate_qubit()
    q = Qubit(m, 0)

    assert default_eng.is_available(Measure.generate_command(q))
    assert not eng.is_available(Measure.generate_command(q))


def test_limited_capability_engine_allow_toffoli():
    default_eng = LimitedCapabilityEngine()
    eng = LimitedCapabilityEngine(allow_toffoli=True)
    m = MainEngine(backend=DummyEngine(), engine_list=[eng])
    q = m.allocate_qureg(4)
    CCCNOT = C(Toffoli)

    assert not default_eng.is_available(Z.generate_command(q))
    assert not default_eng.is_available(X.generate_command(q))
    assert not default_eng.is_available(CNOT.generate_command(tuple(q)))
    assert not default_eng.is_available(Toffoli.generate_command(tuple(q)))
    assert not default_eng.is_available(CCCNOT.generate_command(tuple(q)))

    assert not eng.is_available(Z.generate_command(q))
    assert eng.is_available(X.generate_command(q))
    assert eng.is_available(CNOT.generate_command(tuple(q)))
    assert eng.is_available(Toffoli.generate_command(tuple(q)))
    assert not eng.is_available(CCCNOT.generate_command(tuple(q)))
