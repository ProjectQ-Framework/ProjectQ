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
Registers decomposition for the TimeEvolution gates.

An exact straight forward decomposition of a TimeEvolution gate is possible
if the hamiltonian has only one term or if all the terms commute with each
other in which case one can implement each term individually.
"""
import math

from projectq.cengines import DecompositionRule
from projectq.meta import Control, Compute, Uncompute
from projectq.ops import TimeEvolution, QubitOperator, H, Y, CNOT, Rz, Rx, Ry


def _recognize_time_evolution_commuting_terms(cmd):
    """
    Recognize all TimeEvolution gates with >1 terms but which all commute.
    """
    hamiltonian = cmd.gate.hamiltonian
    if len(hamiltonian.terms) == 1:
        return False
    else:
        id_op = QubitOperator((), 0.0)
        for term in hamiltonian.terms:
            test_op = QubitOperator(term, hamiltonian.terms[term])
            for other in hamiltonian.terms:
                other_op = QubitOperator(other, hamiltonian.terms[other])
                commutator = test_op * other_op - other_op * test_op
                if not commutator.isclose(id_op,
                                          rel_tol=1e-9,
                                          abs_tol=1e-9):
                    return False
    return True


def _decompose_time_evolution_commuting_terms(cmd):
    qureg = cmd.qubits
    eng = cmd.engine
    hamiltonian = cmd.gate.hamiltonian
    time = cmd.gate.time
    with Control(eng, cmd.control_qubits):
        for term in hamiltonian.terms:
            ind_operator = QubitOperator(term, hamiltonian.terms[term])
            TimeEvolution(time, ind_operator) | qureg


def _recognize_time_evolution_individual_terms(cmd):
    return len(cmd.gate.hamiltonian.terms) == 1


def _decompose_time_evolution_individual_terms(cmd):
    """
    Implements a TimeEvolution gate with a hamiltonian having only one term.

    To implement exp(-i * t * hamiltonian), where the hamiltonian is only one
    term, e.g., hamiltonian = X0 x Y1 X Z2, we first perform local
    transformations to in order that all Pauli operators in the hamiltonian
    are Z. We then implement  exp(-i * t * (Z1 x Z2 x Z3) and transform the
    basis back to the original. For more details see, e.g.,

    James D. Whitfield, Jacob Biamonte & Aspuru-Guzik
    Simulation of electronic structure Hamiltonians using quantum computers,
    Molecular Physics, 109:5, 735-750 (2011).

    or

    Nielsen and Chuang, Quantum Computation and Information.
    """
    assert len(cmd.qubits) == 1
    qureg = cmd.qubits[0]
    eng = cmd.engine
    time = cmd.gate.time
    hamiltonian = cmd.gate.hamiltonian
    assert len(hamiltonian.terms) == 1
    term = list(hamiltonian.terms)[0]
    coefficient = hamiltonian.terms[term]
    check_indices = set()

    # Check that hamiltonian is not identity term,
    # Previous __or__ operator should have apply a global phase instead:
    assert not term == ()

    # hamiltonian has only a single local operator
    if len(term) == 1:
        with Control(eng, cmd.control_qubits):
            if term[0][1] == 'X':
                Rx(time * coefficient * 2.) | qureg[term[0][0]]
            elif term[0][1] == 'Y':
                Ry(time * coefficient * 2.) | qureg[term[0][0]]
            else:
                Rz(time * coefficient * 2.) | qureg[term[0][0]]
    # hamiltonian has more than one local operator
    else:
        with Control(eng, cmd.control_qubits):
            with Compute(eng):
                # Apply local basis rotations
                for index, action in term:
                    check_indices.add(index)
                    if action == 'X':
                        H | qureg[index]
                    elif action == 'Y':
                        Rx(math.pi / 2.) | qureg[index]
                # Check that qureg had exactly as many qubits as indices:
                assert check_indices == set((range(len(qureg))))
                # Compute parity
                for i in range(len(qureg)-1):
                    CNOT | (qureg[i], qureg[i+1])
            Rz(time * coefficient * 2.) | qureg[-1]
            # Uncompute parity and basis change
            Uncompute(eng)


rule_commuting_terms = DecompositionRule(
    gate_class=TimeEvolution,
    gate_decomposer=_decompose_time_evolution_commuting_terms,
    gate_recognizer=_recognize_time_evolution_commuting_terms)

rule_individual_terms = DecompositionRule(
    gate_class=TimeEvolution,
    gate_decomposer=_decompose_time_evolution_individual_terms,
    gate_recognizer=_recognize_time_evolution_individual_terms)


all_defined_decomposition_rules = [rule_commuting_terms,
                                   rule_individual_terms]
