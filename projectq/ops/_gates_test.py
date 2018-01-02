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

"""Tests for projectq.ops._gates."""

import math
import cmath
import numpy as np
import pytest

from projectq.ops import (get_inverse, SelfInverseGate, BasicRotationGate,
                          ClassicalInstructionGate, FastForwardingGate,
                          BasicGate)

from projectq.ops import _gates


def test_h_gate():
    gate = _gates.HGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "H"
    assert np.array_equal(gate.matrix,
                          1. / math.sqrt(2) * np.matrix([[1, 1], [1, -1]]))
    assert isinstance(_gates.H, _gates.HGate)


def test_x_gate():
    gate = _gates.XGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "X"
    assert np.array_equal(gate.matrix, np.matrix([[0, 1], [1, 0]]))
    assert isinstance(_gates.X, _gates.XGate)
    assert isinstance(_gates.NOT, _gates.XGate)


def test_y_gate():
    gate = _gates.YGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "Y"
    assert np.array_equal(gate.matrix, np.matrix([[0, -1j], [1j, 0]]))
    assert isinstance(_gates.Y, _gates.YGate)


def test_z_gate():
    gate = _gates.ZGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "Z"
    assert np.array_equal(gate.matrix, np.matrix([[1, 0], [0, -1]]))
    assert isinstance(_gates.Z, _gates.ZGate)


def test_s_gate():
    gate = _gates.SGate()
    assert str(gate) == "S"
    assert np.array_equal(gate.matrix, np.matrix([[1, 0], [0, 1j]]))
    assert isinstance(_gates.S, _gates.SGate)
    assert isinstance(_gates.Sdag, type(get_inverse(gate)))
    assert isinstance(_gates.Sdagger, type(get_inverse(gate)))


def test_t_gate():
    gate = _gates.TGate()
    assert str(gate) == "T"
    assert np.array_equal(gate.matrix,
                          np.matrix([[1, 0],
                                     [0, cmath.exp(1j * cmath.pi / 4)]]))
    assert isinstance(_gates.T, _gates.TGate)
    assert isinstance(_gates.Tdag, type(get_inverse(gate)))
    assert isinstance(_gates.Tdagger, type(get_inverse(gate)))


def test_swap_gate():
    gate = _gates.SwapGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "Swap"
    assert gate.interchangeable_qubit_indices == [[0, 1]]
    assert np.array_equal(gate.matrix,
                          np.matrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0],
                                     [0, 0, 0, 1]]))
    assert isinstance(_gates.Swap, _gates.SwapGate)


def test_engangle_gate():
    gate = _gates.EntangleGate()
    assert str(gate) == "Entangle"
    assert isinstance(_gates.Entangle, _gates.EntangleGate)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi,
                                   4 * math.pi])
def test_rx(angle):
    gate = _gates.Rx(angle)
    expected_matrix = np.matrix([[math.cos(0.5 * angle),
                                  -1j * math.sin(0.5 * angle)],
                                 [-1j * math.sin(0.5 * angle),
                                  math.cos(0.5 * angle)]])
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi,
                                   4 * math.pi])
def test_ry(angle):
    gate = _gates.Ry(angle)
    expected_matrix = np.matrix([[math.cos(0.5 * angle),
                                  -math.sin(0.5 * angle)],
                                [math.sin(0.5 * angle),
                                 math.cos(0.5 * angle)]])
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi,
                                   4 * math.pi])
def test_rz(angle):
    gate = _gates.Rz(angle)
    expected_matrix = np.matrix([[cmath.exp(-.5 * 1j * angle), 0],
                                 [0, cmath.exp(.5 * 1j * angle)]])
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi])
def test_ph(angle):
    gate = _gates.Ph(angle)
    gate2 = _gates.Ph(angle + 2 * math.pi)
    expected_matrix = np.matrix([[cmath.exp(1j * angle), 0],
                                 [0, cmath.exp(1j * angle)]])
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)
    assert gate2.matrix.shape == expected_matrix.shape
    assert np.allclose(gate2.matrix, expected_matrix)
    assert gate == gate2


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi])
def test_r(angle):
    gate = _gates.R(angle)
    gate2 = _gates.R(angle + 2 * math.pi)
    expected_matrix = np.matrix([[1, 0], [0, cmath.exp(1j * angle)]])
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)
    assert gate2.matrix.shape == expected_matrix.shape
    assert np.allclose(gate2.matrix, expected_matrix)
    assert gate == gate2


def test_flush_gate():
    gate = _gates.FlushGate()
    assert str(gate) == ""


def test_measure_gate():
    gate = _gates.MeasureGate()
    assert str(gate) == "Measure"
    assert isinstance(_gates.Measure, _gates.MeasureGate)


def test_allocate_qubit_gate():
    gate = _gates.AllocateQubitGate()
    assert str(gate) == "Allocate"
    assert gate.get_inverse() == _gates.DeallocateQubitGate()
    assert isinstance(_gates.Allocate, _gates.AllocateQubitGate)


def test_deallocate_qubit_gate():
    gate = _gates.DeallocateQubitGate()
    assert str(gate) == "Deallocate"
    assert gate.get_inverse() == _gates.AllocateQubitGate()
    assert isinstance(_gates.Deallocate, _gates.DeallocateQubitGate)


def test_allocate_dirty_qubit_gate():
    gate = _gates.AllocateDirtyQubitGate()
    assert str(gate) == "AllocateDirty"
    assert gate.get_inverse() == _gates.DeallocateQubitGate()
    assert isinstance(_gates.AllocateDirty, _gates.AllocateDirtyQubitGate)


def test_barrier_gate():
    gate = _gates.BarrierGate()
    assert str(gate) == "Barrier"
    assert gate.get_inverse() == _gates.BarrierGate()
    assert isinstance(_gates.Barrier, _gates.BarrierGate)
