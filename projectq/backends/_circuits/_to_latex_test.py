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

import pytest
import builtins

from projectq import MainEngine
from projectq.cengines import LastEngineException
from projectq.ops import (BasicGate,
                          H,
                          X,
                          CNOT,
                          Measure,
                          Z,
                          Swap,
                          C)
from projectq.meta import Control
from projectq.backends import CircuitDrawer

import projectq.backends._circuits._to_latex as _to_latex
import projectq.backends._circuits._drawer as _drawer


def test_tolatex():
    old_header = _to_latex._header
    old_body = _to_latex._body
    old_footer = _to_latex._footer

    _to_latex._header = lambda x: "H"
    _to_latex._body = lambda x, y: x
    _to_latex._footer = lambda x: "F"

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
    settings = {'gate_shadow': False, 'control': {'shadow': False, 'size': 0},
                'gates': {'MeasureGate': {'height': 0, 'width': 0},
                          'XGate': {'height': 1, 'width': .5}
                          },
                'lines': {'style': 'my_style'}}
    header = _to_latex._header(settings)

    assert 'minimum' in header
    assert not 'basicshadow' in header
    assert 'minimum height=0.5' in header
    assert not 'minimum height=1cm' in header
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
    _drawer.to_latex = lambda x: x

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
    _drawer.to_latex = lambda x: x

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

    del qubit1
    eng.flush()

    circuit_lines = drawer.get_latex()
    _drawer.to_latex = old_tolatex

    settings = _to_latex.get_default_settings()
    settings['gates']['AllocateQubitGate']['draw_id'] = True
    code = _to_latex._body(circuit_lines, settings)

    assert code.count("swapstyle") == 6  # swap draws 2 nodes + 2 lines each
    # CZ is two phases plus 2 from CNOTs + 1 from cswap
    assert code.count("phase") == 5
    assert code.count("{{{}}}".format(str(H))) == 2  # 2 hadamard gates
    assert code.count("{$\Ket{0}") == 3  # 3 qubits allocated
    assert code.count("xstyle") == 3  # 1 cnot, 1 not gate
    assert code.count("measure") == 1  # 1 measurement
    assert code.count("{{{}}}".format(str(Z))) == 1  # 1 Z gate
    assert code.count("{red}") == 3


def test_qubit_lines_classicalvsquantum1():
    drawer = _drawer.CircuitDrawer()
    eng = MainEngine(drawer, [])
    old_tolatex = _drawer.to_latex
    _drawer.to_latex = lambda x: x

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
