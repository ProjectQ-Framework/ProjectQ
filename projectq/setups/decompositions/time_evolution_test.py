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

"Tests for projectq.setups.decompositions.time_evolution."
import copy

import numpy
import pytest
import scipy
from scipy import sparse as sps
import scipy.sparse.linalg

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (DummyEngine, AutoReplacer, InstructionFilter,
                               InstructionFilter, DecompositionRuleSet)
from projectq.meta import Control
from projectq.ops import (QubitOperator, TimeEvolution,
                          ClassicalInstructionGate, Ph, Rx, Ry, Rz, All,
                          Measure)

from . import time_evolution as te


def test_recognize_commuting_terms():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    wavefunction = eng.allocate_qureg(5)
    op1 = QubitOperator("X1 Y2", 0.5)
    op2 = QubitOperator("Y2 X4", -0.5)
    op3 = QubitOperator((), 0.5)
    op4 = QubitOperator("X1 Y2", 0.5) + QubitOperator("X2", 1e-10)
    op5 = QubitOperator("X1 Y2", 0.5) + QubitOperator("X2", 1e-8)
    op6 = QubitOperator("X2", 1.0)
    TimeEvolution(1., op1 + op2 + op3 + op4) | wavefunction
    TimeEvolution(1., op1 + op5) | wavefunction
    TimeEvolution(1., op1 + op6) | wavefunction
    TimeEvolution(1., op1) | wavefunction

    cmd1 = saving_backend.received_commands[5]
    cmd2 = saving_backend.received_commands[6]
    cmd3 = saving_backend.received_commands[7]
    cmd4 = saving_backend.received_commands[8]

    assert te.rule_commuting_terms.gate_recognizer(cmd1)
    assert not te.rule_commuting_terms.gate_recognizer(cmd2)
    assert not te.rule_commuting_terms.gate_recognizer(cmd3)
    assert not te.rule_commuting_terms.gate_recognizer(cmd4)


def test_decompose_commuting_terms():
    saving_backend = DummyEngine(save_commands=True)

    def my_filter(self, cmd):
        if (len(cmd.qubits[0]) <= 2 or
                isinstance(cmd.gate, ClassicalInstructionGate)):
            return True
        return False

    rules = DecompositionRuleSet([te.rule_commuting_terms])
    replacer = AutoReplacer(rules)
    filter_eng = InstructionFilter(my_filter)
    eng = MainEngine(backend=saving_backend,
                     engine_list=[replacer, filter_eng])
    qureg = eng.allocate_qureg(5)
    with Control(eng, qureg[3]):
        op1 = QubitOperator("X1 Y2", 0.7)
        op2 = QubitOperator("Y2 X4", -0.8)
        op3 = QubitOperator((), 0.6)
        TimeEvolution(1.5, op1 + op2 + op3) | qureg

    cmd1 = saving_backend.received_commands[5]
    cmd2 = saving_backend.received_commands[6]
    cmd3 = saving_backend.received_commands[7]

    found = [False, False, False]
    scaled_op1 = QubitOperator("X0 Y1", 0.7)
    scaled_op2 = QubitOperator("Y0 X1", -0.8)
    for cmd in [cmd1, cmd2, cmd3]:
        if (cmd.gate == Ph(- 1.5 * 0.6) and
                cmd.qubits[0][0].id == qureg[1].id and  # 1st qubit of [1,2,4]
                cmd.control_qubits[0].id == qureg[3].id):
            found[0] = True
        elif (isinstance(cmd.gate, TimeEvolution) and
                cmd.gate.hamiltonian.isclose(scaled_op1) and
                cmd.gate.time == pytest.approx(1.5) and
                cmd.qubits[0][0].id == qureg[1].id and
                cmd.qubits[0][1].id == qureg[2].id and
                cmd.control_qubits[0].id == qureg[3].id):
            found[1] = True
        elif (isinstance(cmd.gate, TimeEvolution) and
                cmd.gate.hamiltonian.isclose(scaled_op2) and
                cmd.gate.time == pytest.approx(1.5) and
                cmd.qubits[0][0].id == qureg[2].id and
                cmd.qubits[0][1].id == qureg[4].id and
                cmd.control_qubits[0].id == qureg[3].id):
            found[2] = True
    assert all(found)


def test_recognize_individual_terms():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, engine_list=[])
    wavefunction = eng.allocate_qureg(5)
    op1 = QubitOperator("X1 Y2", 0.5)
    op2 = QubitOperator("Y2 X4", -0.5)
    op3 = QubitOperator("X2", 1.0)
    TimeEvolution(1., op1 + op2) | wavefunction
    TimeEvolution(1., op2) | wavefunction
    TimeEvolution(1., op3) | wavefunction

    cmd1 = saving_backend.received_commands[5]
    cmd2 = saving_backend.received_commands[6]
    cmd3 = saving_backend.received_commands[7]

    assert not te.rule_individual_terms.gate_recognizer(cmd1)
    assert te.rule_individual_terms.gate_recognizer(cmd2)
    assert te.rule_individual_terms.gate_recognizer(cmd3)


def test_decompose_individual_terms():
    saving_eng = DummyEngine(save_commands=True)

    def my_filter(self, cmd):
        if (isinstance(cmd.gate, TimeEvolution)):
            return False
        return True

    rules = DecompositionRuleSet([te.rule_individual_terms])
    replacer = AutoReplacer(rules)
    filter_eng = InstructionFilter(my_filter)
    eng = MainEngine(backend=Simulator(),
                     engine_list=[replacer, filter_eng, saving_eng])
    qureg = eng.allocate_qureg(5)
    # initialize in random wavefunction by applying some gates:
    Rx(0.1) | qureg[0]
    Ry(0.2) | qureg[1]
    Rx(0.45) | qureg[2]
    Rx(0.6) | qureg[3]
    Ry(0.77) | qureg[4]
    eng.flush()
    # Use cheat to get initial start wavefunction:
    qubit_to_bit_map, init_wavefunction = copy.deepcopy(eng.backend.cheat())
    # Apply one qubit gates:
    op1 = QubitOperator((), 0.6)
    op2 = QubitOperator("X2", 0.21)
    op3 = QubitOperator("Y1", 0.33)
    op4 = QubitOperator("Z3", 0.42)
    op5 = QubitOperator("X0 Y1 Z2 Z4", -0.5)
    TimeEvolution(1.1, op1) | qureg
    eng.flush()
    qbit_to_bit_map1, final_wavefunction1 = copy.deepcopy(eng.backend.cheat())
    TimeEvolution(1.2, op2) | qureg
    eng.flush()
    qbit_to_bit_map2, final_wavefunction2 = copy.deepcopy(eng.backend.cheat())
    TimeEvolution(1.3, op3) | qureg
    eng.flush()
    qbit_to_bit_map3, final_wavefunction3 = copy.deepcopy(eng.backend.cheat())
    TimeEvolution(1.4, op4) | qureg
    eng.flush()
    qbit_to_bit_map4, final_wavefunction4 = copy.deepcopy(eng.backend.cheat())
    TimeEvolution(1.5, op5) | qureg
    eng.flush()
    qbit_to_bit_map5, final_wavefunction5 = copy.deepcopy(eng.backend.cheat())
    All(Measure) | qureg
    # Check manually:

    def build_matrix(list_single_matrices):
        res = list_single_matrices[0]
        for i in range(1, len(list_single_matrices)):
            res = sps.kron(res, list_single_matrices[i])
        return res

    id_sp = sps.identity(2, format="csr", dtype=complex)
    x_sp = sps.csr_matrix([[0., 1.], [1., 0.]], dtype=complex)
    y_sp = sps.csr_matrix([[0., -1.j], [1.j, 0.]], dtype=complex)
    z_sp = sps.csr_matrix([[1., 0.], [0., -1.]], dtype=complex)

    matrix1 = (sps.identity(2**5, format="csr", dtype=complex) * 0.6 *
               1.1 * -1.0j)
    step1 = scipy.sparse.linalg.expm(matrix1).dot(init_wavefunction)
    assert numpy.allclose(step1, final_wavefunction1)

    matrix2_list = []
    for i in range(5):
        if i == qbit_to_bit_map2[qureg[2].id]:
            matrix2_list.append(x_sp)
        else:
            matrix2_list.append(id_sp)
    matrix2_list.reverse()
    matrix2 = build_matrix(matrix2_list) * 0.21 * 1.2 * -1.0j
    step2 = scipy.sparse.linalg.expm(matrix2).dot(step1)
    assert numpy.allclose(step2, final_wavefunction2)

    matrix3_list = []
    for i in range(5):
        if i == qbit_to_bit_map3[qureg[1].id]:
            matrix3_list.append(y_sp)
        else:
            matrix3_list.append(id_sp)
    matrix3_list.reverse()
    matrix3 = build_matrix(matrix3_list) * 0.33 * 1.3 * -1.0j
    step3 = scipy.sparse.linalg.expm(matrix3).dot(final_wavefunction2)
    assert numpy.allclose(step3, final_wavefunction3)

    matrix4_list = []
    for i in range(5):
        if i == qbit_to_bit_map4[qureg[3].id]:
            matrix4_list.append(z_sp)
        else:
            matrix4_list.append(id_sp)
    matrix4_list.reverse()
    matrix4 = build_matrix(matrix4_list) * 0.42 * 1.4 * -1.0j
    step4 = scipy.sparse.linalg.expm(matrix4).dot(final_wavefunction3)
    assert numpy.allclose(step4, final_wavefunction4)

    matrix5_list = []
    for i in range(5):
        if i == qbit_to_bit_map5[qureg[0].id]:
            matrix5_list.append(x_sp)
        elif i == qbit_to_bit_map5[qureg[1].id]:
            matrix5_list.append(y_sp)
        elif i == qbit_to_bit_map5[qureg[2].id]:
            matrix5_list.append(z_sp)
        elif i == qbit_to_bit_map5[qureg[4].id]:
            matrix5_list.append(z_sp)
        else:
            matrix5_list.append(id_sp)
    matrix5_list.reverse()
    matrix5 = build_matrix(matrix5_list) * -0.5 * 1.5 * -1.0j
    step5 = scipy.sparse.linalg.expm(matrix5).dot(final_wavefunction4)
    print(step5)
    print(final_wavefunction5)

    assert numpy.allclose(step5, final_wavefunction5)
