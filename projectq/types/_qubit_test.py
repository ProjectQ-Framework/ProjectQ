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

"""Tests for projectq.types._qubits."""

from copy import copy, deepcopy

import pytest

from projectq import MainEngine
from projectq.cengines import BasicEngine, DummyEngine
from projectq.ops import Deallocate
from projectq.types import _qubit


@pytest.mark.parametrize("qubit_id", [0, 1])
def test_basic_qubit_str(qubit_id):
    fake_engine = "Fake"
    qubit = _qubit.BasicQubit(fake_engine, qubit_id)
    assert str(qubit) == str(qubit_id)


def test_basic_qubit_measurement():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit0 = eng.allocate_qubit()[0]
    qubit1 = eng.allocate_qubit()[0]
    eng.set_measurement_result(qubit0, False)
    eng.set_measurement_result(qubit1, True)
    assert not bool(qubit0)
    assert not qubit0
    assert bool(qubit1)
    assert qubit1
    assert int(qubit0) == 0
    assert int(qubit1) == 1
    # Testing functions for python 2 and python 3
    assert not qubit0.__bool__()
    assert not qubit0.__nonzero__()
    assert qubit1.__bool__()
    assert qubit1.__nonzero__()


@pytest.mark.parametrize("id0, id1, expected", [(0, 0, True), (0, 1, False)])
def test_basic_qubit_comparison(id0, id1, expected):
    fake_engine = "Fake"
    fake_engine2 = "Fake2"
    qubit0 = _qubit.BasicQubit(fake_engine, id0)
    qubit1 = _qubit.BasicQubit(fake_engine, id1)
    qubit2 = _qubit.BasicQubit(fake_engine2, id0)
    # Different engines
    assert not (qubit2 == qubit0)
    assert not (qubit2 == qubit1)
    assert qubit2 != qubit0
    assert qubit2 != qubit1
    # Same engines
    assert (qubit0 == qubit1) == expected


def test_basic_qubit_hash():
    fake_engine = "Fake"
    a = _qubit.BasicQubit(fake_engine, 1)
    b = _qubit.BasicQubit(fake_engine, 1)
    c = _qubit.WeakQubitRef(fake_engine, 1)
    assert a == b and hash(a) == hash(b)
    assert a == c and hash(a) == hash(c)

    # For performance reasons, low ids should not collide.
    assert len(set(hash(_qubit.BasicQubit(fake_engine, e))
                   for e in range(100))) == 100

    # Important that weakref.WeakSet in projectq.cengines._main.py works.
    # When id is -1, expect reference equality.
    x = _qubit.BasicQubit(fake_engine, -1)
    y = _qubit.BasicQubit(fake_engine, -1)
    # Note hash(x) == hash(y) isn't technically a failure, but it's surprising.
    assert x != y and hash(x) != hash(y)


@pytest.fixture
def mock_main_engine():
    class MockMainEngine(object):
        def __init__(self):
            self.num_calls = 0

        def deallocate_qubit(self, qubit):
            self.num_calls += 1
            self.qubit_id = qubit.id

    return MockMainEngine()


def test_qubit_del(mock_main_engine):
    qubit = _qubit.Qubit(mock_main_engine, 10)
    assert qubit.id == 10
    qubit.__del__()
    assert qubit.id == -1
    assert mock_main_engine.num_calls == 1
    # We need hand coded mock here as mock.Mock cannot check qubit_id
    # (it would save the call argument which is a qubit but id would be
    #  reset to -1 as qubits only have references)
    assert mock_main_engine.qubit_id == 10


def test_qubit_not_copyable():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qubit = _qubit.Qubit(eng, 10)
    qubit_copy = copy(qubit)
    assert id(qubit) == id(qubit_copy)
    qubit_deepcopy = deepcopy(qubit)
    assert id(qubit) == id(qubit_deepcopy)


def test_weak_qubit_ref():
    # Test that there is no deallocate gate
    qubit = _qubit.WeakQubitRef("Engine without deallocate_qubit()", 0)
    with pytest.raises(AttributeError):
        qubit.__del__()


def test_qureg_str():
    assert str(_qubit.Qureg([])) == 'Qureg[]'
    eng = MainEngine(backend=DummyEngine(), engine_list=[])
    a = eng.allocate_qureg(10)
    b = eng.allocate_qureg(50)
    c = eng.allocate_qubit()
    d = eng.allocate_qubit()
    e = eng.allocate_qubit()
    assert str(a) == 'Qureg[0-9]'
    assert str(b) == 'Qureg[10-59]'
    assert str(c) == 'Qureg[60]'
    assert str(d) == 'Qureg[61]'
    assert str(e) == 'Qureg[62]'
    assert str(_qubit.Qureg(c + e)) == 'Qureg[60, 62]'
    assert str(_qubit.Qureg(a + b)) == 'Qureg[0-59]'
    assert str(_qubit.Qureg(a + b + c)) == 'Qureg[0-60]'
    assert str(_qubit.Qureg(a + b + d)) == 'Qureg[0-59, 61]'
    assert str(_qubit.Qureg(a + b + e)) == 'Qureg[0-59, 62]'
    assert str(_qubit.Qureg(b + a)) == 'Qureg[10-59, 0-9]'
    assert str(_qubit.Qureg(e + b + a)) == 'Qureg[62, 10-59, 0-9]'


def test_qureg_measure_if_qubit():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qureg0 = _qubit.Qureg(eng.allocate_qubit())
    qureg1 = _qubit.Qureg(eng.allocate_qubit())
    eng.set_measurement_result(qureg0[0], False)
    eng.set_measurement_result(qureg1[0], True)
    assert not bool(qureg0)
    assert not qureg0
    assert bool(qureg1)
    assert qureg1
    assert int(qureg0) == 0
    assert int(qureg1) == 1
    # Testing functions for python 2 and python 3
    assert not qureg0.__bool__()
    assert not qureg0.__nonzero__()
    assert qureg1.__bool__()
    assert qureg1.__nonzero__()


def test_qureg_measure_exception():
    eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qureg = _qubit.Qureg()
    for qubit_id in [0, 1]:
        qubit = _qubit.Qubit(eng, qubit_id)
        qureg.append(qubit)
    with pytest.raises(Exception):
        qureg.__bool__()
    with pytest.raises(Exception):
        qureg.__nonzero__()
    with pytest.raises(Exception):
        qureg.__int__()


def test_qureg_engine():
    eng1 = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    eng2 = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
    qureg = _qubit.Qureg([_qubit.Qubit(eng1, 0), _qubit.Qubit(eng1, 1)])
    assert eng1 == qureg.engine
    qureg.engine = eng2
    assert qureg[0].engine == eng2 and qureg[1].engine == eng2


def test_idempotent_del():
    rec = DummyEngine(save_commands=True)
    eng = MainEngine(backend=rec, engine_list=[])
    q = eng.allocate_qubit()[0]
    rec.received_commands = []
    assert len(rec.received_commands) == 0
    q.__del__()
    assert len(rec.received_commands) == 1
    q.__del__()
    assert len(rec.received_commands) == 1


def test_idempotent_del_on_failure():
    class InjectedBugEngine(BasicEngine):
        def receive(self, cmds):
            for cmd in cmds:
                if cmd.gate == Deallocate:
                    raise ValueError()

    eng = MainEngine(backend=InjectedBugEngine(), engine_list=[])
    q = eng.allocate_qubit()[0]

    # First call to __del__ triggers the bug.
    try:
        q.__del__()
        assert False
    except ValueError:
        pass

    # Later calls to __del__ do nothing.
    assert q.id == -1
    q.__del__()
