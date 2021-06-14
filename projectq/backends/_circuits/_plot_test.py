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
    Tests for projectq.backends._circuits._plot.py.

    To generate the baseline images,
    run the tests with '--mpl-generate-path=baseline'

    Then run the tests simply with '--mpl'
"""
import pytest
from copy import deepcopy
import projectq.backends._circuits._plot as _plot

# ==============================================================================


class PseudoCanvas(object):
    def __init__(self):
        pass

    def draw(self):
        pass

    def get_renderer(self):
        return


class PseudoFigure(object):
    def __init__(self):
        self.canvas = PseudoCanvas()
        self.dpi = 1


class PseudoBBox(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height


class PseudoText(object):
    def __init__(self, text):
        self.text = text
        self.figure = PseudoFigure()

    def get_window_extent(self, *args):
        return PseudoBBox(len(self.text), 1)

    def remove(self):
        pass


class PseudoTransform(object):
    def __init__(self):
        pass

    def inverted(self):
        return self

    def transform_bbox(self, bbox):
        return bbox


class PseudoAxes(object):
    def __init__(self):
        self.figure = PseudoFigure()
        self.transData = PseudoTransform()

    def add_patch(self, x):
        return x

    def text(self, x, y, text, *args, **kwargse):
        return PseudoText(text)


# ==============================================================================


@pytest.fixture(scope="module")
def plot_params():
    params = deepcopy(_plot._DEFAULT_PLOT_PARAMS)
    params.update([('units_per_inch', 1)])
    return params


@pytest.fixture
def axes():
    return PseudoAxes()


# ==============================================================================


@pytest.mark.parametrize('gate_str', ['X', 'Swap', 'Measure', 'Y', 'Rz(1.00)'])
def test_gate_width(axes, gate_str, plot_params):
    width = _plot.gate_width(axes, gate_str, plot_params)
    if gate_str == 'X':
        assert width == 2 * plot_params['not_radius'] / plot_params['units_per_inch']
    elif gate_str == 'Swap':
        assert width == 2 * plot_params['swap_delta'] / plot_params['units_per_inch']
    elif gate_str == 'Measure':
        assert width == plot_params['mgate_width']
    else:
        assert width == len(gate_str) + 2 * plot_params['gate_offset']


def test_calculate_gate_grid(axes, plot_params):
    qubit_lines = {0: [('X', [0], []), ('X', [0], []), ('X', [0], []), ('X', [0], [])]}

    gate_grid = _plot.calculate_gate_grid(axes, qubit_lines, plot_params)
    assert len(gate_grid) == 5
    assert gate_grid[0] > plot_params['labels_margin']
    width = [gate_grid[i + 1] - gate_grid[i] for i in range(4)]

    # Column grid is given by:
    # |---*---|---*---|---*---|---*---|
    #     |-- w --|-- w --|-- w --|.5w|

    column_spacing = plot_params['column_spacing']
    ref_width = _plot.gate_width(axes, 'X', plot_params)

    for w in width[:-1]:
        assert ref_width + column_spacing == pytest.approx(w)
    assert 0.5 * ref_width + column_spacing == pytest.approx(width[-1])


def test_create_figure(plot_params):
    fig, axes = _plot.create_figure(plot_params)


def test_draw_single_gate(axes, plot_params):
    with pytest.raises(RuntimeError):
        _plot.draw_gate(axes, 'MyGate', 2, [0, 0, 0], [0, 1, 3], [], plot_params)
    _plot.draw_gate(axes, 'MyGate', 2, [0, 0, 0], [0, 1, 2], [], plot_params)


def test_draw_simple(plot_params):
    qubit_lines = {
        0: [
            ('X', [0], []),
            ('Z', [0], []),
            ('Z', [0], [1]),
            ('Swap', [0, 1], []),
            ('Measure', [0], []),
        ],
        1: [None, None, None, None, None],
    }
    fig, axes = _plot.to_draw(qubit_lines)

    units_per_inch = plot_params['units_per_inch']
    not_radius = plot_params['not_radius']
    control_radius = plot_params['control_radius']
    swap_delta = plot_params['swap_delta']
    wire_height = plot_params['wire_height'] * units_per_inch
    mgate_width = plot_params['mgate_width']

    labels = []
    text_gates = []
    measure_gates = []
    for text in axes.texts:
        if text.get_text() == '$|0\\rangle$':
            labels.append(text)
        elif text.get_text() == '   ':
            measure_gates.append(text)
        else:
            text_gates.append(text)

    assert all(label.get_position()[0] == pytest.approx(plot_params['x_offset']) for label in labels)
    assert abs(labels[1].get_position()[1] - labels[0].get_position()[1]) == pytest.approx(wire_height)

    # X gate
    x_gate = [obj for obj in axes.collections if obj.get_label() == 'NOT'][0]
    #   find the filled circles
    assert x_gate.get_paths()[0].get_extents().width == pytest.approx(2 * not_radius)
    assert x_gate.get_paths()[0].get_extents().height == pytest.approx(2 * not_radius)
    #   find the vertical bar
    x_vertical = x_gate.get_paths()[1]
    assert len(x_vertical) == 2
    assert x_vertical.get_extents().width == 0.0
    assert x_vertical.get_extents().height == pytest.approx(2 * plot_params['not_radius'])

    # Z gate
    assert len(text_gates) == 1
    assert text_gates[0].get_text() == 'Z'
    assert text_gates[0].get_position()[1] == pytest.approx(2 * wire_height)

    # CZ gate
    cz_gate = [obj for obj in axes.collections if obj.get_label() == 'CZ'][0]
    #   find the filled circles
    for control in cz_gate.get_paths()[:-1]:
        assert control.get_extents().width == pytest.approx(2 * control_radius)
        assert control.get_extents().height == pytest.approx(2 * control_radius)
    #   find the vertical bar
    cz_vertical = cz_gate.get_paths()[-1]
    assert len(cz_vertical) == 2
    assert cz_vertical.get_extents().width == 0.0
    assert cz_vertical.get_extents().height == pytest.approx(wire_height)

    # Swap gate
    swap_gate = [obj for obj in axes.collections if obj.get_label() == 'SWAP'][0]
    #   find the filled circles
    for qubit in swap_gate.get_paths()[:-1]:
        assert qubit.get_extents().width == pytest.approx(2 * swap_delta)
        assert qubit.get_extents().height == pytest.approx(2 * swap_delta)
    #   find the vertical bar
    swap_vertical = swap_gate.get_paths()[-1]
    assert len(swap_vertical) == 2
    assert swap_vertical.get_extents().width == 0.0
    assert swap_vertical.get_extents().height == pytest.approx(wire_height)

    # Measure gate
    measure_gate = [obj for obj in axes.collections if obj.get_label() == 'Measure'][0]

    assert measure_gate.get_paths()[0].get_extents().width == pytest.approx(mgate_width)
    assert measure_gate.get_paths()[0].get_extents().height == pytest.approx(0.9 * mgate_width)


def test_draw_advanced(plot_params):
    qubit_lines = {0: [('X', [0], []), ('Measure', [0], [])], 1: [None, None]}

    with pytest.raises(RuntimeError):
        _plot.to_draw(qubit_lines, qubit_labels={1: 'qb1', 2: 'qb2'})

    with pytest.raises(RuntimeError):
        _plot.to_draw(qubit_lines, drawing_order={0: 0, 1: 2})

    with pytest.raises(RuntimeError):
        _plot.to_draw(qubit_lines, drawing_order={1: 1, 2: 0})

    # --------------------------------------------------------------------------

    _, axes = _plot.to_draw(qubit_lines)
    for text in axes.texts:
        assert text.get_text() == r'$|0\rangle$'

    # NB numbering of wire starts from bottom.
    _, axes = _plot.to_draw(qubit_lines, qubit_labels={0: 'qb0', 1: 'qb1'}, drawing_order={0: 0, 1: 1})
    assert [axes.texts[qubit_id].get_text() for qubit_id in range(2)] == ['qb0', 'qb1']

    positions = [axes.texts[qubit_id].get_position() for qubit_id in range(2)]
    assert positions[1][1] > positions[0][1]

    _, axes = _plot.to_draw(qubit_lines, qubit_labels={0: 'qb2', 1: 'qb3'}, drawing_order={0: 1, 1: 0})

    assert [axes.texts[qubit_id].get_text() for qubit_id in range(2)] == ['qb2', 'qb3']

    positions = [axes.texts[qubit_id].get_position() for qubit_id in range(2)]
    assert positions[1][1] < positions[0][1]
