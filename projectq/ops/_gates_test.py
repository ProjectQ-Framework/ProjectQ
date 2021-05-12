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
"""Tests for projectq.ops._gates."""

import math
import cmath
import numpy as np
import pytest

from projectq import MainEngine
from projectq.ops import (
    All,
    FlipBits,
    get_inverse,
    Measure,
)

from projectq.ops import _gates


def test_h_gate():
    gate = _gates.HGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "H"
    assert np.array_equal(gate.matrix, 1.0 / math.sqrt(2) * np.matrix([[1, 1], [1, -1]]))
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
    assert np.array_equal(gate.matrix, np.matrix([[1, 0], [0, cmath.exp(1j * cmath.pi / 4)]]))
    assert isinstance(_gates.T, _gates.TGate)
    assert isinstance(_gates.Tdag, type(get_inverse(gate)))
    assert isinstance(_gates.Tdagger, type(get_inverse(gate)))


def test_sqrtx_gate():
    gate = _gates.SqrtXGate()
    assert str(gate) == "SqrtX"
    assert np.array_equal(gate.matrix, np.matrix([[0.5 + 0.5j, 0.5 - 0.5j], [0.5 - 0.5j, 0.5 + 0.5j]]))
    assert np.array_equal(gate.matrix * gate.matrix, np.matrix([[0j, 1], [1, 0]]))
    assert isinstance(_gates.SqrtX, _gates.SqrtXGate)


def test_swap_gate():
    gate = _gates.SwapGate()
    assert gate == gate.get_inverse()
    assert str(gate) == "Swap"
    assert gate.interchangeable_qubit_indices == [[0, 1]]
    assert np.array_equal(gate.matrix, np.matrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]))
    assert isinstance(_gates.Swap, _gates.SwapGate)


def test_sqrtswap_gate():
    sqrt_gate = _gates.SqrtSwapGate()
    swap_gate = _gates.SwapGate()
    assert str(sqrt_gate) == "SqrtSwap"
    assert np.array_equal(sqrt_gate.matrix * sqrt_gate.matrix, swap_gate.matrix)
    assert np.array_equal(
        sqrt_gate.matrix,
        np.matrix(
            [
                [1, 0, 0, 0],
                [0, 0.5 + 0.5j, 0.5 - 0.5j, 0],
                [0, 0.5 - 0.5j, 0.5 + 0.5j, 0],
                [0, 0, 0, 1],
            ]
        ),
    )
    assert isinstance(_gates.SqrtSwap, _gates.SqrtSwapGate)


def test_engangle_gate():
    gate = _gates.EntangleGate()
    assert str(gate) == "Entangle"
    assert isinstance(_gates.Entangle, _gates.EntangleGate)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi, 4 * math.pi])
def test_rx(angle):
    gate = _gates.Rx(angle)
    expected_matrix = np.matrix(
        [
            [math.cos(0.5 * angle), -1j * math.sin(0.5 * angle)],
            [-1j * math.sin(0.5 * angle), math.cos(0.5 * angle)],
        ]
    )
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi, 4 * math.pi])
def test_ry(angle):
    gate = _gates.Ry(angle)
    expected_matrix = np.matrix(
        [
            [math.cos(0.5 * angle), -math.sin(0.5 * angle)],
            [math.sin(0.5 * angle), math.cos(0.5 * angle)],
        ]
    )
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi, 4 * math.pi])
def test_rz(angle):
    gate = _gates.Rz(angle)
    expected_matrix = np.matrix([[cmath.exp(-0.5 * 1j * angle), 0], [0, cmath.exp(0.5 * 1j * angle)]])
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi, 4 * math.pi])
def test_rxx(angle):
    gate = _gates.Rxx(angle)
    expected_matrix = np.matrix(
        [
            [cmath.cos(0.5 * angle), 0, 0, -1j * cmath.sin(0.5 * angle)],
            [0, cmath.cos(0.5 * angle), -1j * cmath.sin(0.5 * angle), 0],
            [0, -1j * cmath.sin(0.5 * angle), cmath.cos(0.5 * angle), 0],
            [-1j * cmath.sin(0.5 * angle), 0, 0, cmath.cos(0.5 * angle)],
        ]
    )
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi, 4 * math.pi])
def test_ryy(angle):
    gate = _gates.Ryy(angle)
    expected_matrix = np.matrix(
        [
            [cmath.cos(0.5 * angle), 0, 0, 1j * cmath.sin(0.5 * angle)],
            [0, cmath.cos(0.5 * angle), -1j * cmath.sin(0.5 * angle), 0],
            [0, -1j * cmath.sin(0.5 * angle), cmath.cos(0.5 * angle), 0],
            [1j * cmath.sin(0.5 * angle), 0, 0, cmath.cos(0.5 * angle)],
        ]
    )
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi, 4 * math.pi])
def test_rzz(angle):
    gate = _gates.Rzz(angle)
    expected_matrix = np.matrix(
        [
            [cmath.exp(-0.5 * 1j * angle), 0, 0, 0],
            [0, cmath.exp(0.5 * 1j * angle), 0, 0],
            [0, 0, cmath.exp(0.5 * 1j * angle), 0],
            [0, 0, 0, cmath.exp(-0.5 * 1j * angle)],
        ]
    )
    assert gate.matrix.shape == expected_matrix.shape
    assert np.allclose(gate.matrix, expected_matrix)


@pytest.mark.parametrize("angle", [0, 0.2, 2.1, 4.1, 2 * math.pi])
def test_ph(angle):
    gate = _gates.Ph(angle)
    gate2 = _gates.Ph(angle + 2 * math.pi)
    expected_matrix = np.matrix([[cmath.exp(1j * angle), 0], [0, cmath.exp(1j * angle)]])
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


def test_flip_bits_equality_and_hash():
    gate1 = _gates.FlipBits([1, 0, 0, 1])
    gate2 = _gates.FlipBits([1, 0, 0, 1])
    gate3 = _gates.FlipBits([0, 1, 0, 1])
    assert gate1 == gate2
    assert hash(gate1) == hash(gate2)
    assert gate1 != gate3
    assert gate1 != _gates.X


def test_flip_bits_str():
    gate1 = _gates.FlipBits([0, 0, 1])
    assert str(gate1) == "FlipBits(4)"


def test_error_on_tuple_input():
    with pytest.raises(ValueError):
        _gates.FlipBits(2) | (None, None)


flip_bits_testdata = [
    ([0, 1, 0, 1], '0101'),
    ([1, 0, 1, 0], '1010'),
    ([False, True, False, True], '0101'),
    ('0101', '0101'),
    ('1111', '1111'),
    ('0000', '0000'),
    (8, '0001'),
    (11, '1101'),
    (1, '1000'),
    (-1, '1111'),
    (-2, '0111'),
    (-3, '1011'),
]


@pytest.mark.parametrize("bits_to_flip, result", flip_bits_testdata)
def test_simulator_flip_bits(bits_to_flip, result):
    eng = MainEngine()
    qubits = eng.allocate_qureg(4)
    FlipBits(bits_to_flip) | qubits
    eng.flush()
    assert pytest.approx(eng.backend.get_probability(result, qubits)) == 1.0
    All(Measure) | qubits


def test_flip_bits_can_be_applied_to_various_qubit_qureg_formats():
    eng = MainEngine()
    qubits = eng.allocate_qureg(4)
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0000', qubits)) == 1.0
    FlipBits([0, 1, 1, 0]) | qubits
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0110', qubits)) == 1.0
    FlipBits([1]) | qubits[0]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('1110', qubits)) == 1.0
    FlipBits([1]) | (qubits[0],)
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0110', qubits)) == 1.0
    FlipBits([1, 1]) | [qubits[0], qubits[1]]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('1010', qubits)) == 1.0
    FlipBits(-1) | qubits
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0101', qubits)) == 1.0
    FlipBits(-4) | [qubits[0], qubits[1], qubits[2], qubits[3]]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0110', qubits)) == 1.0
    FlipBits(2) | [qubits[0]] + [qubits[1], qubits[2]]
    eng.flush()
    assert pytest.approx(eng.backend.get_probability('0010', qubits)) == 1.0
    All(Measure) | qubits
