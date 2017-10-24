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
Tests for projectq.backends._sim._simulator.py, using both the Python
and the C++ simulator as backends.
"""

import copy
import math
import numpy
import pytest
import random
import scipy
import scipy.sparse
import scipy.sparse.linalg

from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.ops import (H,
                          X,
                          Y,
                          Z,
                          S,
                          Rx,
                          Ry,
                          Rz,
                          CNOT,
                          Toffoli,
                          Measure,
                          BasicGate,
                          BasicMathGate,
                          QubitOperator,
                          TimeEvolution,
                          All)
from projectq.meta import Control, Dagger

from projectq.backends import Simulator


def test_is_cpp_simulator_present():
    import projectq.backends._sim._cppsim
    assert projectq.backends._sim._cppsim


def get_available_simulators():
    result = ["py_simulator"]
    try:
        import projectq.backends._sim._cppsim as _
        result.append("cpp_simulator")
    except ImportError:
        # The C++ simulator was either not installed or is misconfigured. Skip.
        pass
    return result


@pytest.fixture(params=get_available_simulators())
def sim(request):
    if request.param == "cpp_simulator":
        from projectq.backends._sim._cppsim import Simulator as CppSim
        sim = Simulator(gate_fusion=True)
        sim._simulator = CppSim(1)
        return sim
    if request.param == "py_simulator":
        from projectq.backends._sim._pysim import Simulator as PySim
        sim = Simulator()
        sim._simulator = PySim(1)
        return sim


class Mock1QubitGate(BasicGate):
        def __init__(self):
            BasicGate.__init__(self)
            self.cnt = 0

        @property
        def matrix(self):
            self.cnt += 1
            return [[0, 1], [1, 0]]


class Mock6QubitGate(BasicGate):
        def __init__(self):
            BasicGate.__init__(self)
            self.cnt = 0

        @property
        def matrix(self):
            self.cnt += 1
            return numpy.eye(2 ** 6)


class MockNoMatrixGate(BasicGate):
        def __init__(self):
            BasicGate.__init__(self)
            self.cnt = 0

        @property
        def matrix(self):
            self.cnt += 1
            raise AttributeError


def test_simulator_is_available(sim):
    backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend, [])
    qubit = eng.allocate_qubit()
    Measure | qubit
    BasicMathGate(lambda x: x) | qubit
    del qubit
    assert len(backend.received_commands) == 4

    # Test that allocate, measure, basic math, and deallocate are available.
    for cmd in backend.received_commands:
        assert sim.is_available(cmd)

    new_cmd = backend.received_commands[-1]

    new_cmd.gate = Mock1QubitGate()
    assert sim.is_available(new_cmd)
    assert new_cmd.gate.cnt == 1

    new_cmd.gate = Mock6QubitGate()
    assert not sim.is_available(new_cmd)
    assert new_cmd.gate.cnt == 1

    new_cmd.gate = MockNoMatrixGate()
    assert not sim.is_available(new_cmd)
    assert new_cmd.gate.cnt == 1


def test_simulator_cheat(sim):
    # cheat function should return a tuple
    assert isinstance(sim.cheat(), tuple)
    # first entry is the qubit mapping.
    # should be empty:
    assert len(sim.cheat()[0]) == 0
    # state vector should only have 1 entry:
    assert len(sim.cheat()[1]) == 1

    eng = MainEngine(sim, [])
    qubit = eng.allocate_qubit()

    # one qubit has been allocated
    assert len(sim.cheat()[0]) == 1
    assert sim.cheat()[0][0] == 0
    assert len(sim.cheat()[1]) == 2
    assert 1. == pytest.approx(abs(sim.cheat()[1][0]))

    del qubit
    # should be empty:
    assert len(sim.cheat()[0]) == 0
    # state vector should only have 1 entry:
    assert len(sim.cheat()[1]) == 1


def test_simulator_functional_measurement(sim):
    eng = MainEngine(sim, [])
    qubits = eng.allocate_qureg(5)
    # entangle all qubits:
    H | qubits[0]
    for qb in qubits[1:]:
        CNOT | (qubits[0], qb)

    Measure | qubits

    bit_value_sum = sum([int(qubit) for qubit in qubits])
    assert bit_value_sum == 0 or bit_value_sum == 5


class Plus2Gate(BasicMathGate):
    def __init__(self):
        BasicMathGate.__init__(self, lambda x: (x+2,))


def test_simulator_emulation(sim):
    eng = MainEngine(sim, [])
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()

    with Control(eng, qubit3):
        Plus2Gate() | (qubit1 + qubit2)

    assert 1. == pytest.approx(sim.cheat()[1][0])

    X | qubit3
    with Control(eng, qubit3):
        Plus2Gate() | (qubit1 + qubit2)
    assert 1. == pytest.approx(sim.cheat()[1][6])

    Measure | (qubit1 + qubit2 + qubit3)


def test_simulator_kqubit_gate(sim):
    m1 = Rx(0.3).matrix
    m2 = Rx(0.8).matrix
    m3 = Ry(0.1).matrix
    m4 = Rz(0.9).matrix.dot(Ry(-0.1).matrix)
    m = numpy.kron(m4, numpy.kron(m3, numpy.kron(m2, m1)))

    class KQubitGate(BasicGate):
        @property
        def matrix(self):
            return m

    eng = MainEngine(sim, [])
    qureg = eng.allocate_qureg(4)
    qubit = eng.allocate_qubit()
    Rx(-0.3) | qureg[0]
    Rx(-0.8) | qureg[1]
    Ry(-0.1) | qureg[2]
    Rz(-0.9) | qureg[3]
    Ry(0.1) | qureg[3]
    X | qubit
    with Control(eng, qubit):
        KQubitGate() | qureg
    X | qubit
    with Control(eng, qubit):
        with Dagger(eng):
            KQubitGate() | qureg
    assert sim.get_amplitude('0' * 5, qubit + qureg) == pytest.approx(1.)

    class LargerGate(BasicGate):
        @property
        def matrix(self):
            return numpy.eye(2 ** 6)

    with pytest.raises(Exception):
        LargerGate() | (qureg + qubit)


def test_simulator_kqubit_exception(sim):
    m1 = Rx(0.3).matrix
    m2 = Rx(0.8).matrix
    m3 = Ry(0.1).matrix
    m4 = Rz(0.9).matrix.dot(Ry(-0.1).matrix)
    m = numpy.kron(m4, numpy.kron(m3, numpy.kron(m2, m1)))

    class KQubitGate(BasicGate):
        @property
        def matrix(self):
            return m

    eng = MainEngine(sim, [])
    qureg = eng.allocate_qureg(3)
    with pytest.raises(Exception):
        KQubitGate() | qureg
    with pytest.raises(Exception):
        H | qureg


def test_simulator_probability(sim):
    eng = MainEngine(sim)
    qubits = eng.allocate_qureg(6)
    All(H) | qubits
    eng.flush()
    bits = [0, 0, 1, 0, 1, 0]
    for i in range(6):
        assert (eng.backend.get_probability(bits[:i], qubits[:i]) ==
                pytest.approx(0.5**i))
    extra_qubit = eng.allocate_qubit()
    with pytest.raises(RuntimeError):
        eng.backend.get_probability([0], extra_qubit)
    del extra_qubit
    All(H) | qubits
    Ry(2 * math.acos(math.sqrt(0.3))) | qubits[0]
    eng.flush()
    assert eng.backend.get_probability([0], [qubits[0]]) == pytest.approx(0.3)
    Ry(2 * math.acos(math.sqrt(0.4))) | qubits[2]
    eng.flush()
    assert eng.backend.get_probability([0], [qubits[2]]) == pytest.approx(0.4)
    assert (eng.backend.get_probability([0, 0], qubits[:3:2]) ==
            pytest.approx(0.12))
    assert (eng.backend.get_probability([0, 1], qubits[:3:2]) ==
            pytest.approx(0.18))
    assert (eng.backend.get_probability([1, 0], qubits[:3:2]) ==
            pytest.approx(0.28))
    Measure | qubits


def test_simulator_amplitude(sim):
    eng = MainEngine(sim)
    qubits = eng.allocate_qureg(6)
    All(X) | qubits
    All(H) | qubits
    eng.flush()
    bits = [0, 0, 1, 0, 1, 0]
    assert eng.backend.get_amplitude(bits, qubits) == pytest.approx(1. / 8.)
    bits = [0, 0, 0, 0, 1, 0]
    assert eng.backend.get_amplitude(bits, qubits) == pytest.approx(-1. / 8.)
    bits = [0, 1, 1, 0, 1, 0]
    assert eng.backend.get_amplitude(bits, qubits) == pytest.approx(-1. / 8.)
    All(H) | qubits
    All(X) | qubits
    Ry(2 * math.acos(0.3)) | qubits[0]
    eng.flush()
    bits = [0] * 6
    assert eng.backend.get_amplitude(bits, qubits) == pytest.approx(0.3)
    bits[0] = 1
    assert (eng.backend.get_amplitude(bits, qubits) ==
            pytest.approx(math.sqrt(0.91)))
    Measure | qubits
    # raises if not all qubits are in the list:
    with pytest.raises(RuntimeError):
        eng.backend.get_amplitude(bits, qubits[:-1])
    # doesn't just check for length:
    with pytest.raises(RuntimeError):
        eng.backend.get_amplitude(bits, qubits[:-1] + [qubits[0]])
    extra_qubit = eng.allocate_qubit()
    eng.flush()
    # there is a new qubit now!
    with pytest.raises(RuntimeError):
        eng.backend.get_amplitude(bits, qubits)


def test_simulator_expectation(sim):
    eng = MainEngine(sim, [])
    qureg = eng.allocate_qureg(3)
    op0 = QubitOperator('Z0')
    expectation = sim.get_expectation_value(op0, qureg)
    assert 1. == pytest.approx(expectation)
    X | qureg[0]
    expectation = sim.get_expectation_value(op0, qureg)
    assert -1. == pytest.approx(expectation)
    H | qureg[0]
    op1 = QubitOperator('X0')
    expectation = sim.get_expectation_value(op1, qureg)
    assert -1. == pytest.approx(expectation)
    Z | qureg[0]
    expectation = sim.get_expectation_value(op1, qureg)
    assert 1. == pytest.approx(expectation)
    X | qureg[0]
    S | qureg[0]
    Z | qureg[0]
    X | qureg[0]
    op2 = QubitOperator('Y0')
    expectation = sim.get_expectation_value(op2, qureg)
    assert 1. == pytest.approx(expectation)
    Z | qureg[0]
    expectation = sim.get_expectation_value(op2, qureg)
    assert -1. == pytest.approx(expectation)

    op_sum = QubitOperator('Y0 X1 Z2') + QubitOperator('X1')
    H | qureg[1]
    X | qureg[2]
    expectation = sim.get_expectation_value(op_sum, qureg)
    assert 2. == pytest.approx(expectation)

    op_sum = QubitOperator('Y0 X1 Z2') + QubitOperator('X1')
    X | qureg[2]
    expectation = sim.get_expectation_value(op_sum, qureg)
    assert 0. == pytest.approx(expectation)

    op_id = .4 * QubitOperator(())
    expectation = sim.get_expectation_value(op_id, qureg)
    assert .4 == pytest.approx(expectation)


def test_simulator_expectation_exception(sim):
    eng = MainEngine(sim, [])
    qureg = eng.allocate_qureg(3)
    op = QubitOperator('Z2')
    sim.get_expectation_value(op, qureg)
    op2 = QubitOperator('Z3')
    with pytest.raises(Exception):
        sim.get_expectation_value(op2, qureg)
    op3 = QubitOperator('Z1') + QubitOperator('X1 Y3')
    with pytest.raises(Exception):
        sim.get_expectation_value(op3, qureg)


def test_simulator_applyqubitoperator_exception(sim):
    eng = MainEngine(sim, [])
    qureg = eng.allocate_qureg(3)
    op = QubitOperator('Z2')
    sim.apply_qubit_operator(op, qureg)
    op2 = QubitOperator('Z3')
    with pytest.raises(Exception):
        sim.apply_qubit_operator(op2, qureg)
    op3 = QubitOperator('Z1') + QubitOperator('X1 Y3')
    with pytest.raises(Exception):
        sim.apply_qubit_operator(op3, qureg)


def test_simulator_applyqubitoperator(sim):
    eng = MainEngine(sim, [])
    qureg = eng.allocate_qureg(3)
    op = QubitOperator('X0 Y1 Z2')
    sim.apply_qubit_operator(op, qureg)
    X | qureg[0]
    Y | qureg[1]
    Z | qureg[2]
    assert sim.get_amplitude('000', qureg) == pytest.approx(1.)

    H | qureg[0]
    op_H = 1. / math.sqrt(2.) * (QubitOperator('X0') + QubitOperator('Z0'))
    sim.apply_qubit_operator(op_H, [qureg[0]])
    assert sim.get_amplitude('000', qureg) == pytest.approx(1.)

    op_Proj0 = 0.5 * (QubitOperator('') + QubitOperator('Z0'))
    op_Proj1 = 0.5 * (QubitOperator('') - QubitOperator('Z0'))
    H | qureg[0]
    sim.apply_qubit_operator(op_Proj0, [qureg[0]])
    assert sim.get_amplitude('000', qureg) == pytest.approx(1. / math.sqrt(2.))
    sim.apply_qubit_operator(op_Proj1, [qureg[0]])
    assert sim.get_amplitude('000', qureg) == pytest.approx(0.)


def test_simulator_time_evolution(sim):
    N = 9  # number of qubits
    time_to_evolve = 1.1  # time to evolve for
    eng = MainEngine(sim, [])
    qureg = eng.allocate_qureg(N)
    # initialize in random wavefunction by applying some gates:
    for qb in qureg:
        Rx(random.random()) | qb
        Ry(random.random()) | qb
    eng.flush()
    # Use cheat to get initial start wavefunction:
    qubit_to_bit_map, init_wavefunction = copy.deepcopy(eng.backend.cheat())
    Qop = QubitOperator
    op = 0.3 * Qop("X0 Y1 Z2 Y3 X4")
    op += 1.1 * Qop(())
    op += -1.4 * Qop("Y0 Z1 X3 Y5")
    op += -1.1 * Qop("Y1 X2 X3 Y4")
    TimeEvolution(time_to_evolve, op) | qureg
    eng.flush()
    qbit_to_bit_map, final_wavefunction = copy.deepcopy(eng.backend.cheat())
    Measure | qureg
    # Check manually:

    def build_matrix(list_single_matrices):
        res = list_single_matrices[0]
        for i in range(1, len(list_single_matrices)):
            res = scipy.sparse.kron(res, list_single_matrices[i])
        return res
    id_sp = scipy.sparse.identity(2, format="csr", dtype=complex)
    x_sp = scipy.sparse.csr_matrix([[0., 1.], [1., 0.]], dtype=complex)
    y_sp = scipy.sparse.csr_matrix([[0., -1.j], [1.j, 0.]], dtype=complex)
    z_sp = scipy.sparse.csr_matrix([[1., 0.], [0., -1.]], dtype=complex)
    gates = [x_sp, y_sp, z_sp]

    res_matrix = 0
    for t, c in op.terms.items():
        matrix = [id_sp] * N
        for idx, gate in t:
            matrix[qbit_to_bit_map[qureg[idx].id]] = gates[ord(gate) -
                                                           ord('X')]
        matrix.reverse()
        res_matrix += build_matrix(matrix) * c
    res_matrix *= -1j * time_to_evolve

    init_wavefunction = numpy.array(init_wavefunction, copy=False)
    final_wavefunction = numpy.array(final_wavefunction, copy=False)
    res = scipy.sparse.linalg.expm_multiply(res_matrix, init_wavefunction)
    assert numpy.allclose(res, final_wavefunction)


def test_simulator_set_wavefunction(sim):
    eng = MainEngine(sim)
    qubits = eng.allocate_qureg(2)
    wf = [0., 0., math.sqrt(0.2), math.sqrt(0.8)]
    with pytest.raises(RuntimeError):
        eng.backend.set_wavefunction(wf, qubits)
    eng.flush()
    eng.backend.set_wavefunction(wf, qubits)
    assert pytest.approx(eng.backend.get_probability('1', [qubits[0]])) == .8
    assert pytest.approx(eng.backend.get_probability('01', qubits)) == .2
    assert pytest.approx(eng.backend.get_probability('1', [qubits[1]])) == 1.
    Measure | qubits


def test_simulator_set_wavefunction_always_complex(sim):
    """ Checks that wavefunction is always complex """
    eng = MainEngine(sim)
    qubit = eng.allocate_qubit()
    eng.flush()
    wf = [1., 0]
    eng.backend.set_wavefunction(wf, qubit)
    Y | qubit
    eng.flush()
    assert eng.backend.get_amplitude('1', qubit) == pytest.approx(1j)


def test_simulator_collapse_wavefunction(sim):
    eng = MainEngine(sim)
    qubits = eng.allocate_qureg(4)
    # unknown qubits: raises
    with pytest.raises(RuntimeError):
        eng.backend.collapse_wavefunction(qubits, [0] * 4)
    eng.flush()
    eng.backend.collapse_wavefunction(qubits, [0] * 4)
    assert pytest.approx(eng.backend.get_probability([0] * 4, qubits)) == 1.
    All(H) | qubits[1:]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability([0] * 4, qubits)) == .125
    # impossible outcome: raises
    with pytest.raises(RuntimeError):
        eng.backend.collapse_wavefunction(qubits, [1] + [0] * 3)
    eng.backend.collapse_wavefunction(qubits[:-1], [0, 1, 0])
    probability = eng.backend.get_probability([0, 1, 0, 1], qubits)
    assert probability == pytest.approx(.5)
    eng.backend.set_wavefunction([1.] + [0.] * 15, qubits)
    H | qubits[0]
    CNOT | (qubits[0], qubits[1])
    eng.flush()
    eng.backend.collapse_wavefunction([qubits[0]], [1])
    probability = eng.backend.get_probability([1, 1], qubits[0:2])
    assert probability == pytest.approx(1.)


def test_simulator_no_uncompute_exception(sim):
    eng = MainEngine(sim, [])
    qubit = eng.allocate_qubit()
    H | qubit
    with pytest.raises(RuntimeError):
        qubit[0].__del__()
    # If you wanted to keep using the qubit, you shouldn't have deleted it.
    assert qubit[0].id == -1


class MockSimulatorBackend(object):
    def __init__(self):
        self.run_cnt = 0

    def run(self):
        self.run_cnt += 1


def test_simulator_flush():
    sim = Simulator()
    sim._simulator = MockSimulatorBackend()

    eng = MainEngine(sim)
    eng.flush()

    assert sim._simulator.run_cnt == 1


def test_simulator_send():
    sim = Simulator()
    backend = DummyEngine(save_commands=True)

    eng = MainEngine(backend, [sim])

    qubit = eng.allocate_qubit()
    H | qubit
    Measure | qubit
    del qubit
    eng.flush()

    assert len(backend.received_commands) == 5


def test_simulator_functional_entangle(sim):
    eng = MainEngine(sim, [])
    qubits = eng.allocate_qureg(5)
    # entangle all qubits:
    H | qubits[0]
    for qb in qubits[1:]:
        CNOT | (qubits[0], qb)

    # check the state vector:
    assert .5 == pytest.approx(abs(sim.cheat()[1][0])**2)
    assert .5 == pytest.approx(abs(sim.cheat()[1][31])**2)
    for i in range(1, 31):
        assert 0. == pytest.approx(abs(sim.cheat()[1][i]))

    # unentangle all except the first 2
    for qb in qubits[2:]:
        CNOT | (qubits[0], qb)

    # entangle using Toffolis
    for qb in qubits[2:]:
        Toffoli | (qubits[0], qubits[1], qb)

    # check the state vector:
    assert .5 == pytest.approx(abs(sim.cheat()[1][0])**2)
    assert .5 == pytest.approx(abs(sim.cheat()[1][31])**2)
    for i in range(1, 31):
        assert 0. == pytest.approx(abs(sim.cheat()[1][i]))

    # uncompute using multi-controlled NOTs
    with Control(eng, qubits[0:-1]):
        X | qubits[-1]
    with Control(eng, qubits[0:-2]):
        X | qubits[-2]
    with Control(eng, qubits[0:-3]):
        X | qubits[-3]
    CNOT | (qubits[0], qubits[1])
    H | qubits[0]

    # check the state vector:
    assert 1. == pytest.approx(abs(sim.cheat()[1][0])**2)
    for i in range(1, 32):
        assert 0. == pytest.approx(abs(sim.cheat()[1][i]))

    Measure | qubits
