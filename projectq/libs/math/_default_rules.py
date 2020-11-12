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
Registers a few default replacement rules for Shor's algorithm to work
(see Examples).
"""

from projectq.meta import Control, Dagger
from projectq.cengines import DecompositionRule

from ._gates import (AddConstant,
                     SubConstant,
                     AddConstantModN,
                     SubConstantModN,
                     MultiplyByConstantModN,
                     AddQuantum,
                     SubtractQuantum,
                     Comparator,)

from ._constantmath import (add_constant,
                            add_constant_modN,
                            mul_by_constant_modN,)

from ._quantummath import (add_quantum,
                           subtract_quantum,
                           comparator,)


def _replace_addconstant(cmd):
    eng = cmd.engine
    c = cmd.gate.a
    quint = cmd.qubits[0]

    with Control(eng, cmd.control_qubits):
        add_constant(eng, c, quint)


def _replace_addconstmodN(cmd):
    eng = cmd.engine
    c = cmd.gate.a
    N = cmd.gate.N
    quint = cmd.qubits[0]

    with Control(eng, cmd.control_qubits):
        add_constant_modN(eng, c, N, quint)


def _replace_multiplybyconstantmodN(cmd):
    eng = cmd.engine
    c = cmd.gate.a
    N = cmd.gate.N
    quint = cmd.qubits[0]

    with Control(eng, cmd.control_qubits):
        mul_by_constant_modN(eng, c, N, quint)


def _replace_addquantum(cmd):
    
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]
    c = cmd.qubits[2]

    with Control(eng, cmd.control_qubits):
        add_quantum(eng, quint_a, quint_b, c)


def _replace_subtractquantum(cmd):
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]

    with Control(eng, cmd.control_qubits):
        subtract_quantum(eng, quint_a, quint_b)

def _replace_comparator(cmd):
    eng = cmd.engine
    quint_a = cmd.qubits[0]
    quint_b = cmd.qubits[1]
    c = cmd.qubits[2]

    with Control(eng, cmd.control_qubits):
        comparator(eng, quint_a, quint_b, c)

all_defined_decomposition_rules = [
    DecompositionRule(AddConstant, _replace_addconstant),
    DecompositionRule(AddConstantModN, _replace_addconstmodN),
    DecompositionRule(MultiplyByConstantModN, _replace_multiplybyconstantmodN),
    DecompositionRule(AddQuantum, _replace_addquantum),
    DecompositionRule(SubtractQuantum, _replace_subtractquantum),
    DecompositionRule(Comparator, _replace_comparator),
]
