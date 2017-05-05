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

from projectq import MainEngine
from projectq.ops import X, C, BasicMathGate
from ._classical_simulator import ClassicalSimulator


def test_simulator_read_write():
    sim = ClassicalSimulator()
    eng = MainEngine(sim, [])
    a = eng.allocate_qureg(32)
    b = eng.allocate_qureg(32)

    assert sim.read_register(a) == 0
    assert sim.read_register(b) == 0
    assert sim.read_bit(a[0]) == 0
    assert sim.read_bit(b[0]) == 0

    sim.write_register(a, 123)
    sim.write_register(b, 456)
    assert sim.read_register(a) == 123
    assert sim.read_register(b) == 456
    assert sim.read_bit(a[0]) == 1
    assert sim.read_bit(b[0]) == 0

    sim.write_bit(b[0], 1)
    assert sim.read_register(a) == 123
    assert sim.read_register(b) == 457
    assert sim.read_bit(a[0]) == 1
    assert sim.read_bit(b[0]) == 1


def test_simulator_triangle_increment_cycle():
    sim = ClassicalSimulator()
    eng = MainEngine(sim, [])

    a = eng.allocate_qureg(6)
    for t in range(1 << 6):
        assert sim.read_register(a) == t
        for i in range(6)[::-1]:
            C(X, i) | (a[:i], a[i])
    assert sim.read_register(a) == 0


def test_simulator_bit_repositioning():
    sim = ClassicalSimulator()
    eng = MainEngine(sim, [])
    a = eng.allocate_qureg(4)
    b = eng.allocate_qureg(5)
    c = eng.allocate_qureg(6)
    sim.write_register(a, 9)
    sim.write_register(b, 17)
    sim.write_register(c, 33)
    for q in b:
        eng.deallocate_qubit(q)
    assert sim.read_register(a) == 9
    assert sim.read_register(c) == 33


def test_simulator_arithmetic():
    class Offset(BasicMathGate):
        def __init__(self, amount):
            BasicMathGate.__init__(self, lambda x: (x+amount,))

    class Sub(BasicMathGate):
        def __init__(self):
            BasicMathGate.__init__(self, lambda x, y: (x, y-x))

    sim = ClassicalSimulator()
    eng = MainEngine(sim, [])
    a = eng.allocate_qureg(4)
    b = eng.allocate_qureg(5)
    sim.write_register(a, 9)
    sim.write_register(b, 17)

    Offset(2) | a
    assert sim.read_register(a) == 11
    assert sim.read_register(b) == 17

    Offset(3) | b
    assert sim.read_register(a) == 11
    assert sim.read_register(b) == 20

    Offset(32 + 5) | b
    assert sim.read_register(a) == 11
    assert sim.read_register(b) == 25

    Sub() | (a, b)
    assert sim.read_register(a) == 11
    assert sim.read_register(b) == 14

    Sub() | (a, b)
    Sub() | (a, b)
    assert sim.read_register(a) == 11
    assert sim.read_register(b) == 24
