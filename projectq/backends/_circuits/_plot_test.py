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
    Tests for projectq.backends._circuits._plot.py.
    To generate the baseline images, run the tests with '--mpl-generate-path'
    Then run the tests simply with '--mpl'
"""
import pytest
from projectq import MainEngine
from projectq.ops import *
from projectq.backends import CircuitDrawerMatplotlib

import projectq.backends._circuits._plot as _plot

@pytest.mark.mpl_image_compare
def test_draw_single_gates():
    allocate_qubit = [0,1,2,3]
    gates = [('H',0)]
    fig, ax = _plot.to_draw(gates, allocate_qubit)
    return fig

@pytest.mark.mpl_image_compare
def test_draw_multi_gates():
    allocate_qubit = [0,1,2,3]
    gates = [('H',0), ('H',0)]
    fig, ax = _plot.to_draw(gates, allocate_qubit)
    return fig

@pytest.mark.mpl_image_compare
def test_gates_position():
    allocate_qubit = [0,1,2,3]
    gates = [('H',3)]
    fig, ax = _plot.to_draw(gates, allocate_qubit)
    return fig

@pytest.mark.mpl_image_compare
def test_gates_position2():
    allocate_qubit = [0,1,2,3]
    gates = [('H',3), ('X',1,0), ('H',2), ('H',2),('H',2),('X',3,0)]
    fig, ax = _plot.to_draw(gates, allocate_qubit)
    return fig

@pytest.mark.mpl_image_compare
def test_simple_CNOT():
    allocate_qubit = [0,1]
    gates = [('X',1,0)]
    fig, ax = _plot.to_draw(gates, allocate_qubit)
    return fig

@pytest.mark.mpl_image_compare
def test_complex_CNOT():
    allocate_qubit = [0,1,2,3]
    gates = [('X',3,0)]
    fig, ax = _plot.to_draw(gates, allocate_qubit)
    return fig

@pytest.mark.mpl_image_compare
def test_complex_CNOT2():
    allocate_qubit = [0,1,2,3]
    gates = [('X',0,3)]
    fig, ax = _plot.to_draw(gates, allocate_qubit)
    return fig

@pytest.mark.mpl_image_compare
def test_qubit_numbers():
    # set up qubit numbers without quantum gates
    allocate_qureg = [0, 1, 2, 3, 4]
    gates = []
    fig, ax = _plot.to_draw(gates, allocate_qureg)
    return fig

@pytest.mark.mpl_image_compare
def test_measure_gate():
    # set up qubit numbers without quantum gates
    allocate_qureg = [0]
    gates = [('Measure',0)]
    fig, ax = _plot.to_draw(gates, allocate_qureg)
    return fig