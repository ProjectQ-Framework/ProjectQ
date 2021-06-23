# -*- coding: utf-8 -*-
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
Tests for projectq.backends._circuits._to_latex.py.
"""

import copy

import pytest

from projectq import MainEngine
from projectq.ops import (
    BasicGate,
    H,
    X,
    CNOT,
    Measure,
    Z,
    Swap,
    SqrtX,
    SqrtSwap,
    C,
    get_inverse,
)
from projectq.meta import Control

import projectq.backends._circuits._to_latex as _to_latex
import projectq.backends._circuits._drawer as _drawer


def test_tolatex():
    old_header = _to_latex._header
    old_body = _to_latex._body
    old_footer = _to_latex._footer

    _to_latex._header = lambda x: "H"
    _to_latex._body = lambda x, settings, drawing_order, draw_gates_in_parallel: x
    _to_latex._footer = lambda: "F"

    latex = _to_latex.to_latex("B")
    assert latex == "HBF"

    _to_latex._header = old_header
    _to_latex._body = old_body
    _to_latex._footer = old_footer


def test_default_settings():
    settings = _to_latex.get_default_settings()
    assert isinstance(settings, dict)
    assert 'gate_shadow' in settings
    assert 'lines' in settings
    assert 'gates' in settings
    assert 'control' in settings


def test_header():
    settings = {
        'gate_shadow': False,
        'control': {'shadow': False, 'size': 0},
        'gates': {
            'MeasureGate': {'height': 0, 'width': 0},
            'XGate': {'height': 1, 'width': 0.5},
        },
        'lines': {'style': 'my_style'},
    }
    header = _to_latex._header(settings)

    assert 'minimum' in header
    assert 'basicshadow' not in header
    assert 'minimum height=0.5' in header
    assert 'minimum height=1cm' not in header
    assert 'minimum height=0cm' in header

    settings['control']['shadow'] = True
    settings['gates']['XGate']['width'] = 1
    header = _to_latex._header(settings)

    assert 'minimum' in header
    assert 'basicshadow' in header
    assert 'minimum height=1cm' in header
    assert 'minimum height=0cm' in header

    settings['control']['shadow'] = True
    settings['gate_shadow'] = True
    header = _to_latex._header(settings)

    assert 'minimum' in header
    assert 'white,basicshadow' in header
    assert 'minimum height=1cm' in header
    assert 'minimum height=0cm' in header


def test_large_gates():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x, drawing_order, draw_gates_in_parallel: x

    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()

    class MyLargeGate(BasicGate):
        def __str__(self):
            return "large_gate"

    H | qubit2
    MyLargeGate() | (qubit1, qubit3)
    H | qubit2
    eng.flush()

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex

    settings = _to_latex.get_default_settings()
    settings['gates']['AllocateQubitGate']['draw_id'] = True
    code = _to_latex._body(circuit_lines, settings)

    assert code.count("large_gate") == 1  # 1 large gate was applied
    # check that large gate draws lines, also for qubits it does not act upon
    assert code.count("edge[") == 5
    assert code.count("{H};") == 2


def test_body():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x, drawing_order, draw_gates_in_parallel: x

    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()
    H | qubit1
    H | qubit2
    CNOT | (qubit1, qubit2)
    X | qubit2
    Measure | qubit2
    CNOT | (qubit2, qubit1)
    Z | qubit2
    C(Z) | (qubit1, qubit2)
    C(Swap) | (qubit1, qubit2, qubit3)
    SqrtX | qubit1
    SqrtSwap | (qubit1, qubit2)
    get_inverse(SqrtX) | qubit1
    C(SqrtSwap) | (qubit1, qubit2, qubit3)
    get_inverse(SqrtSwap) | (qubit1, qubit2)
    C(Swap) | (qubit3, qubit1, qubit2)
    C(SqrtSwap) | (qubit3, qubit1, qubit2)

    del qubit1
    eng.flush()

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex

    settings = _to_latex.get_default_settings()
    settings['gates']['AllocateQubitGate']['draw_id'] = True
    code = _to_latex._body(circuit_lines, settings)

    # swap draws 2 nodes + 2 lines each, so is sqrtswap gate, csqrtswap,
    # inv(sqrt_swap), and cswap.
    assert code.count("swapstyle") == 36
    # CZ is two phases plus 2 from CNOTs + 2 from cswap + 2 from csqrtswap
    assert code.count("phase") == 8
    assert code.count("{{{}}}".format(str(H))) == 2  # 2 hadamard gates
    assert code.count("{$\\Ket{0}") == 3  # 3 qubits allocated
    # 1 cnot, 1 not gate, 3 SqrtSwap, 1 inv(SqrtSwap)
    assert code.count("xstyle") == 7
    assert code.count("measure") == 1  # 1 measurement
    assert code.count("{{{}}}".format(str(Z))) == 1  # 1 Z gate
    assert code.count("{red}") == 3


@pytest.mark.parametrize('gate, n_qubits', ((SqrtSwap, 3), (Swap, 3), (X, 2)), ids=str)
def test_invalid_number_of_qubits(gate, n_qubits):
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x, drawing_order, draw_gates_in_parallel: x

    qureg = eng.allocate_qureg(n_qubits)

    gate | (*qureg,)
    eng.flush()

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex
    settings = _to_latex.get_default_settings()
    settings['gates']['AllocateQubitGate']['draw_id'] = True

    with pytest.raises(RuntimeError):
        _to_latex._body(circuit_lines, settings)


def test_body_with_drawing_order_and_gates_parallel():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x, drawing_order, draw_gates_in_parallel: x

    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()

    H | qubit1
    H | qubit2
    H | qubit3
    CNOT | (qubit1, qubit3)

    # replicates the above order: first the 3 allocations, then the 3 Hadamard and 1 CNOT gates
    order = [0, 1, 2, 0, 1, 2, 0]

    del qubit1
    eng.flush()

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex

    settings = _to_latex.get_default_settings()
    settings['gates']['AllocateQubitGate']['draw_id'] = True
    code = _to_latex._body(circuit_lines, settings, drawing_order=order, draw_gates_in_parallel=True)

    # there are three Hadamards in parallel
    assert code.count("node[pos=.5] {H}") == 3

    # line1_gate0 is initialisation
    # line1_gate1 is empty
    # line1_gate2 is for Hadamard on line1
    # line1_gate3 is empty
    # XOR of CNOT is node[xstyle] (line1_gate4)
    assert code.count("node[xstyle] (line2_gate4)") == 1

    # and the CNOT is at position 1.4, because of the offsets
    assert code.count("node[phase] (line0_gate4) at (1.4") == 1
    assert code.count("node[xstyle] (line2_gate4) at (1.4") == 1


def test_body_with_drawing_order_and_gates_not_parallel():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x, drawing_order, draw_gates_in_parallel: x

    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()

    H | qubit1
    H | qubit2
    H | qubit3
    CNOT | (qubit1, qubit3)

    # replicates the above order: first the 3 allocations, then the 3 Hadamard and 1 CNOT gates
    order = [0, 1, 2, 0, 1, 2, 0]

    del qubit1
    eng.flush()

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex

    settings = _to_latex.get_default_settings()
    settings['gates']['AllocateQubitGate']['draw_id'] = True
    code = _to_latex._body(circuit_lines, settings, drawing_order=order, draw_gates_in_parallel=False)

    # and the CNOT is at position 4.0, because of the offsets
    # which are 0.5 * 3 * 2 (due to three Hadamards) + the initialisations
    assert code.count("node[phase] (line0_gate4) at (4.0,-0)") == 1
    assert code.count("node[xstyle] (line2_gate4) at (4.0,-2)") == 1


def test_body_without_drawing_order_and_gates_not_parallel():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x, drawing_order, draw_gates_in_parallel: x

    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()

    H | qubit1
    H | qubit2
    H | qubit3
    CNOT | (qubit1, qubit3)

    del qubit1
    eng.flush()

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex

    settings = _to_latex.get_default_settings()
    settings['gates']['AllocateQubitGate']['draw_id'] = True
    code = _to_latex._body(circuit_lines, settings, draw_gates_in_parallel=False)

    # line1_gate1 is after the cnot line2_gate_4
    idx1 = code.find("node[xstyle] (line2_gate4)")
    idx2 = code.find("node[none] (line1_gate1)")
    assert idx1 < idx2


def test_qubit_allocations_at_zero():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x, drawing_order, draw_gates_in_parallel: x

    a = eng.allocate_qureg(4)

    CNOT | (a[0], a[2])
    CNOT | (a[0], a[3])
    CNOT | (a[0], a[2])
    CNOT | (a[1], a[3])

    del a
    eng.flush()

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex

    settings = _to_latex.get_default_settings()
    settings['gates']['AllocateQubitGate']['allocate_at_zero'] = True
    code = _to_latex._body(copy.deepcopy(circuit_lines), settings)
    assert code.count("gate0) at (0") == 4

    settings['gates']['AllocateQubitGate']['allocate_at_zero'] = False
    code = _to_latex._body(copy.deepcopy(circuit_lines), settings)
    assert code.count("gate0) at (0") == 3

    del settings['gates']['AllocateQubitGate']['allocate_at_zero']
    code = _to_latex._body(copy.deepcopy(circuit_lines), settings)
    assert code.count("gate0) at (0") == 3


def test_qubit_lines_classicalvsquantum1():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x, drawing_order, draw_gates_in_parallel: x

    qubit1 = eng.allocate_qubit()

    H | qubit1
    Measure | qubit1
    X | qubit1

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex

    settings = _to_latex.get_default_settings()
    code = _to_latex._body(circuit_lines, settings)

    assert code.count("edge[") == 4


def test_qubit_lines_classicalvsquantum2():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])

    controls = eng.allocate_qureg(3)
    action = eng.allocate_qubit()

    with Control(eng, controls):
        H | action

    code = drawer.get_latex()
    assert code.count("{{{}}}".format(str(H))) == 1  # 1 Hadamard
    assert code.count("{$") == 4  # four allocate gates
    assert code.count("node[phase]") == 3  # 3 controls


def test_qubit_lines_classicalvsquantum3():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])

    control0 = eng.allocate_qureg(2)
    action1 = eng.allocate_qubit()
    control1 = eng.allocate_qureg(2)
    action2 = eng.allocate_qubit()
    control2 = eng.allocate_qubit()

    with Control(eng, control0 + control1 + control2):
        H | (action1, action2)

    code = drawer.get_latex()
    assert code.count("{{{}}}".format(str(H))) == 1  # 1 Hadamard
    assert code.count("{$") == 7  # 8 allocate gates
    assert code.count("node[phase]") == 3  # 1 control
    # (other controls are within the gate -> are not drawn)
    assert code.count("edge[") == 10  # 7 qubit lines + 3 from controls


def test_quantum_lines_cnot():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])

    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()

    Measure | qubit1
    Measure | qubit2

    CNOT | (qubit2, qubit1)

    del qubit1, qubit2
    code = drawer.get_latex()
    assert code.count("edge[") == 12  # all lines are classical

    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])

    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()

    Measure | qubit1  # qubit1 is classical

    CNOT | (qubit2, qubit1)  # now it is quantum

    del qubit1, qubit2
    code = drawer.get_latex()
    assert code.count("edge[") == 7  # all lines are quantum
