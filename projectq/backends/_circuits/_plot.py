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
This module provides the basic functionality required to plot a quantum
circuit in a matplotlib figure.
It is mainly used by the CircuitDrawerMatplotlib compiler engine.

Currently, it supports all single-qubit gates, including their controlled
versions to an arbitrary number of control qubits. It also supports
multi-target qubit gates under some restrictions. Namely that the target
qubits must be neighbours in the output figure (which cannot be determined
durinng compilation at this time).
"""

from copy import deepcopy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Arc, Rectangle

# Important note on units for the plot parameters.
# The following entries are in inches:
#   - column_spacing
#   - labels_margin
#   - wire_height
#
# The following entries are in data units (matplotlib)
#   - control_radius
#   - gate_offset
#   - mgate_width
#   - not_radius
#   - swap_delta
#   - x_offset
#
# The rest have misc. units (as defined by matplotlib)
_DEFAULT_PLOT_PARAMS = dict(fontsize=14.0,
                            column_spacing=.5,
                            control_radius=0.015,
                            labels_margin=1,
                            linewidth=1.0,
                            not_radius=0.03,
                            gate_offset=.05,
                            mgate_width=0.1,
                            swap_delta=0.02,
                            x_offset=.05,
                            wire_height=1)

# ==============================================================================


def to_draw(qubit_lines, qubit_labels=None, drawing_order=None, **kwargs):
    """
    Translates a given circuit to a matplotlib figure.

    Args:
        qubit_lines (dict): list of gates for each qubit axis
        qubit_labels (dict): label to print in front of the qubit wire for
            each qubit ID
        drawing_order (dict): index of the wire for each qubit ID to be drawn.
        **kwargs (dict): additional parameters are used to update the default
            plot parameters

    Returns:
        A tuple with (figure, axes)

    Note:
        Numbering of qubit wires starts at 0 at the bottom and increases
        vertically.

    Note:
        Additional keyword arguments can be passed to this
        function in order to further customize the figure output
        by matplotlib (default value in parentheses):

          - fontsize (14): Font size in pt
          - column_spacing (.5): Vertical spacing between two
            neighbouring gates (roughly in inches)
          - control_radius (.015): Radius of the circle for controls
          - labels_margin (1): Margin between labels and begin of
            wire (roughly in inches)
          - linewidth (1): Width of line
          - not_radius (.03): Radius of the circle for X/NOT gates
          - gate_offset (.05): Inner margins for gates with a text
            representation
          - mgate_width (.1): Width of the measurement gate
          - swap_delta (.02): Half-size of the SWAP gate
          - x_offset (.05): Absolute X-offset for drawing within the axes
          - wire_height (1): Vertical spacing between two qubit
            wires (roughly in inches)
    """
    if qubit_labels is None:
        qubit_labels = {qubit_id: r'$|0\rangle$' for qubit_id in qubit_lines}
    else:
        if list(qubit_labels) != list(qubit_lines):
            raise RuntimeError('Qubit IDs in qubit_labels do not match '
                               + 'qubit IDs in qubit_lines!')

    if drawing_order is None:
        n_qubits = len(qubit_lines)
        drawing_order = {
            qubit_id: n_qubits - qubit_id - 1
            for qubit_id in list(qubit_lines)
        }
    else:
        if list(drawing_order) != list(qubit_lines):
            raise RuntimeError('Qubit IDs in drawing_order do not match '
                               + 'qubit IDs in qubit_lines!')
        if (list(sorted(drawing_order.values())) != list(
                range(len(drawing_order)))):
            raise RuntimeError(
                'Indices of qubit wires in drawing_order '
                + 'must be between 0 and {}!'.format(len(drawing_order)))

    plot_params = deepcopy(_DEFAULT_PLOT_PARAMS)
    plot_params.update(kwargs)

    n_labels = len(list(qubit_lines))

    wire_height = plot_params['wire_height']
    # Grid in inches
    wire_grid = np.arange(wire_height, (n_labels + 1) * wire_height,
                          wire_height,
                          dtype=float)

    fig, axes = create_figure(plot_params)

    # Grid in inches
    gate_grid = calculate_gate_grid(axes, qubit_lines, plot_params)

    width = gate_grid[-1] + plot_params['column_spacing']
    height = wire_grid[-1] + wire_height

    resize_figure(fig, axes, width, height, plot_params)

    # Convert grids into data coordinates
    units_per_inch = plot_params['units_per_inch']

    gate_grid *= units_per_inch
    gate_grid = gate_grid + plot_params['x_offset']
    wire_grid *= units_per_inch
    plot_params['column_spacing'] *= units_per_inch

    draw_wires(axes, n_labels, gate_grid, wire_grid, plot_params)

    draw_labels(axes, qubit_labels, drawing_order, wire_grid, plot_params)

    draw_gates(axes, qubit_lines, drawing_order, gate_grid, wire_grid,
               plot_params)
    return fig, axes


# ==============================================================================
# Functions used to calculate the layout


def gate_width(axes, gate_str, plot_params):
    """
    Calculate the width of a gate based on its string representation.

    Args:
        axes (matplotlib.axes.Axes): axes object
        gate_str (str): string representation of a gate
        plot_params (dict): plot parameters

    Returns:
        The width of a gate on the figure (in inches)
    """
    if gate_str == 'X':
        return 2 * plot_params['not_radius'] / plot_params['units_per_inch']
    if gate_str == 'Swap':
        return 2 * plot_params['swap_delta'] / plot_params['units_per_inch']

    if gate_str == 'Measure':
        return plot_params['mgate_width']

    obj = axes.text(0,
                    0,
                    gate_str,
                    visible=True,
                    bbox=dict(edgecolor='k', facecolor='w', fill=True, lw=1.0),
                    fontsize=14)
    obj.figure.canvas.draw()
    width = (obj.get_window_extent(obj.figure.canvas.get_renderer()).width
             / axes.figure.dpi)
    obj.remove()
    return width + 2 * plot_params['gate_offset']


def calculate_gate_grid(axes, qubit_lines, plot_params):
    """
    Calculate an optimal grid spacing for a list of quantum gates.

    Args:
        axes (matplotlib.axes.Axes): axes object
        qubit_lines (dict): list of gates for each qubit axis
        plot_params (dict): plot parameters

    Returns:
        An array (np.ndarray) with the gate x positions.
    """
    # NB: column_spacing is still in inch when this function is called
    column_spacing = plot_params['column_spacing']
    data = list(qubit_lines.values())
    depth = len(data[0])

    width_list = [
        max(
            gate_width(axes, line[idx][0], plot_params) if line[idx] else 0
            for line in data) for idx in range(depth)
    ]

    gate_grid = np.array([0] * (depth + 1), dtype=float)
    
    gate_grid[0] = plot_params['labels_margin']
    if depth > 0:
        gate_grid[0] += width_list[0] * 0.5
        for idx in range(1, depth):
            gate_grid[idx] = gate_grid[idx - 1] + column_spacing + (
                width_list[idx] + width_list[idx - 1]) * 0.5
        gate_grid[-1] = gate_grid[-2] + column_spacing + width_list[-1] * 0.5
    return gate_grid


# ==============================================================================
# Basic helper functions


def text(axes, gate_pos, wire_pos, textstr, plot_params):
    """
    Draws a text box on the figure.

    Args:
        axes (matplotlib.axes.Axes): axes object
        gate_pos (float): x coordinate of the gate [data units]
        wire_pos (float): y coordinate of the qubit wire
        textstr (str): text of the gate and box
        plot_params (dict): plot parameters
        box (bool): draw the rectangle box if box is True
    """
    return axes.text(gate_pos,
                     wire_pos,
                     textstr,
                     color='k',
                     ha='center',
                     va='center',
                     clip_on=True,
                     size=plot_params['fontsize'])


# ==============================================================================


def create_figure(plot_params):
    """
    Create a new figure as well as a new axes instance

    Args:
        plot_params (dict): plot parameters

    Returns:
        A tuple with (figure, axes)
    """
    fig = plt.figure(facecolor='w', edgecolor='w')
    axes = plt.axes()
    axes.set_axis_off()
    axes.set_aspect('equal')
    plot_params['units_per_inch'] = fig.dpi / axes.get_window_extent().width
    return fig, axes


def resize_figure(fig, axes, width, height, plot_params):
    """
    Resizes a figure and adjust the limits of the axes instance to make sure
    that the distances in data coordinates on the screen stay constant.

    Args:
        fig (matplotlib.figure.Figure): figure object
        axes (matplotlib.axes.Axes): axes object
        width (float): new figure width
        height (float): new figure height
        plot_params (dict): plot parameters

    Returns:
        A tuple with (figure, axes)
    """
    fig.set_size_inches(width, height)

    new_limits = plot_params['units_per_inch'] * np.array([width, height])
    axes.set_xlim(0, new_limits[0])
    axes.set_ylim(0, new_limits[1])


def draw_gates(axes, qubit_lines, drawing_order, gate_grid, wire_grid,
               plot_params):
    """
    Draws the gates.

    Args:
        qubit_lines (dict): list of gates for each qubit axis
        drawing_order (dict): index of the wire for each qubit ID to be drawn
        gate_grid (np.ndarray): x positions of the gates
        wire_grid (np.ndarray): y positions of the qubit wires
        plot_params (dict): plot parameters

    Returns:
        A tuple with (figure, axes)
    """
    for qubit_line in qubit_lines.values():
        for idx, data in enumerate(qubit_line):
            if data is not None:
                (gate_str, targets, controls) = data
                targets_order = [drawing_order[tgt] for tgt in targets]
                draw_gate(
                    axes, gate_str, gate_grid[idx],
                    [wire_grid[tgt] for tgt in targets_order], targets_order,
                    [wire_grid[drawing_order[ctrl]]
                     for ctrl in controls], plot_params)


def draw_gate(axes, gate_str, gate_pos, target_wires, targets_order,
              control_wires, plot_params):
    """
    Draws a single gate at a given location.

    Args:
        axes (AxesSubplot): axes object
        gate_str (str): string representation of a gate
        gate_pos (float): x coordinate of the gate [data units]
        target_wires (list): y coordinates of the target qubits
        targets_order (list): index of the wires corresponding to the target
                              qubit IDs
        control_wires (list): y coordinates of the control qubits
        plot_params (dict): plot parameters

    Returns:
        A tuple with (figure, axes)
    """
    # Special cases
    if gate_str == 'Z' and len(control_wires) == 1:
        draw_control_z_gate(axes, gate_pos, target_wires[0], control_wires[0],
                            plot_params)
    elif gate_str == 'X':
        draw_x_gate(axes, gate_pos, target_wires[0], plot_params)
    elif gate_str == 'Swap':
        draw_swap_gate(axes, gate_pos, target_wires[0], target_wires[1],
                       plot_params)
    elif gate_str == 'Measure':
        draw_measure_gate(axes, gate_pos, target_wires[0], plot_params)
    else:
        if len(target_wires) == 1:
            draw_generic_gate(axes, gate_pos, target_wires[0], gate_str,
                              plot_params)
        else:
            if sorted(targets_order) != list(
                    range(min(targets_order),
                          max(targets_order) + 1)):
                raise RuntimeError(
                    'Multi-qubit gate with non-neighbouring qubits!\n'
                    + 'Gate: {} on wires {}'.format(gate_str, targets_order))

            multi_qubit_gate(axes, gate_str, gate_pos, min(target_wires),
                             max(target_wires), plot_params)

    if not control_wires:
        return

    for control_wire in control_wires:
        axes.add_patch(
            Circle((gate_pos, control_wire),
                   plot_params['control_radius'],
                   ec='k',
                   fc='k',
                   fill=True,
                   lw=plot_params['linewidth']))

    all_wires = target_wires + control_wires
    axes.add_line(
        Line2D((gate_pos, gate_pos), (min(all_wires), max(all_wires)),
               color='k',
               lw=plot_params['linewidth']))


def draw_generic_gate(axes, gate_pos, wire_pos, gate_str, plot_params):
    """
    Draws a measurement gate.

    Args:
        axes (AxesSubplot): axes object
        gate_pos (float): x coordinate of the gate [data units]
        wire_pos (float): y coordinate of the qubit wire
        gate_str (str) : string representation of a gate
        plot_params (dict): plot parameters
    """
    obj = text(axes, gate_pos, wire_pos, gate_str, plot_params)
    obj.set_zorder(7)

    factor = plot_params['units_per_inch'] / obj.figure.dpi
    gate_offset = plot_params['gate_offset']

    renderer = obj.figure.canvas.get_renderer()
    width = obj.get_window_extent(renderer).width * factor + 2 * gate_offset
    height = obj.get_window_extent(renderer).height * factor + 2 * gate_offset

    axes.add_patch(
        Rectangle((gate_pos - width / 2, wire_pos - height / 2),
                  width,
                  height,
                  ec='k',
                  fc='w',
                  fill=True,
                  lw=plot_params['linewidth'],
                  zorder=6))


def draw_measure_gate(axes, gate_pos, wire_pos, plot_params):
    """
    Draws a measurement gate.

    Args:
        axes (AxesSubplot): axes object
        gate_pos (float): x coordinate of the gate [data units]
        wire_pos (float): y coordinate of the qubit wire
        plot_params (dict): plot parameters
    """
    # pylint: disable=invalid-name

    width = plot_params['mgate_width']
    height = 0.9 * width
    y_ref = wire_pos - 0.3 * height

    # Cannot use PatchCollection for the arc due to bug in matplotlib code...
    arc = Arc((gate_pos, y_ref),
              width * 0.7,
              height * 0.8,
              theta1=0,
              theta2=180,
              ec='k',
              fc='w',
              zorder=5)
    axes.add_patch(arc)

    patches = [
        Rectangle((gate_pos - width / 2, wire_pos - height / 2),
                  width,
                  height,
                  fill=True),
        Line2D((gate_pos, gate_pos + width * 0.35),
               (y_ref, wire_pos + height * 0.35),
               color='k',
               linewidth=1)
    ]

    gate = PatchCollection(patches,
                           edgecolors='k',
                           facecolors='w',
                           linewidths=plot_params['linewidth'],
                           zorder=5)
    gate.set_label('Measure')
    axes.add_collection(gate)


def multi_qubit_gate(axes, gate_str, gate_pos, wire_pos_min, wire_pos_max,
                     plot_params):
    """
    Draws a multi-target qubit gate.

    Args:
        axes (matplotlib.axes.Axes): axes object
        gate_str (str): string representation of a gate
        gate_pos (float): x coordinate of the gate [data units]
        wire_pos_min (float): y coordinate of the lowest qubit wire
        wire_pos_max (float): y coordinate of the highest qubit wire
        plot_params (dict): plot parameters
    """
    gate_offset = plot_params['gate_offset']
    y_center = (wire_pos_max - wire_pos_min) / 2 + wire_pos_min
    obj = axes.text(gate_pos,
                    y_center,
                    gate_str,
                    color='k',
                    ha='center',
                    va='center',
                    size=plot_params['fontsize'],
                    zorder=7)
    height = wire_pos_max - wire_pos_min + 2 * gate_offset
    inv = axes.transData.inverted()
    width = inv.transform_bbox(
        obj.get_window_extent(obj.figure.canvas.get_renderer())).width
    return axes.add_patch(
        Rectangle((gate_pos - width / 2, wire_pos_min - gate_offset),
                  width,
                  height,
                  edgecolor='k',
                  facecolor='w',
                  fill=True,
                  lw=plot_params['linewidth'],
                  zorder=6))


def draw_x_gate(axes, gate_pos, wire_pos, plot_params):
    """
    Draws the symbol for a X/NOT gate.

    Args:
        axes (matplotlib.axes.Axes): axes object
        gate_pos (float): x coordinate of the gate [data units]
        wire_pos (float): y coordinate of the qubit wire [data units]
        plot_params (dict): plot parameters
    """
    not_radius = plot_params['not_radius']

    gate = PatchCollection([
        Circle((gate_pos, wire_pos), not_radius, fill=False),
        Line2D((gate_pos, gate_pos),
               (wire_pos - not_radius, wire_pos + not_radius))
    ],
                           edgecolors='k',
                           facecolors='w',
                           linewidths=plot_params['linewidth'])
    gate.set_label('NOT')
    axes.add_collection(gate)


def draw_control_z_gate(axes, gate_pos, wire_pos1, wire_pos2, plot_params):
    """
    Draws the symbol for a controlled-Z gate.

    Args:
        axes (matplotlib.axes.Axes): axes object
        wire_pos (float): x coordinate of the gate [data units]
        y1 (float): y coordinate of the 1st qubit wire
        y2 (float): y coordinate of the 2nd qubit wire
        plot_params (dict): plot parameters
    """
    gate = PatchCollection([
        Circle(
            (gate_pos, wire_pos1), plot_params['control_radius'], fill=True),
        Circle(
            (gate_pos, wire_pos2), plot_params['control_radius'], fill=True),
        Line2D((gate_pos, gate_pos), (wire_pos1, wire_pos2))
    ],
                           edgecolors='k',
                           facecolors='k',
                           linewidths=plot_params['linewidth'])
    gate.set_label('CZ')
    axes.add_collection(gate)


def draw_swap_gate(axes, gate_pos, wire_pos1, wire_pos2, plot_params):
    """
    Draws the symbol for a SWAP gate.

    Args:
        axes (matplotlib.axes.Axes): axes object
        x (float): x coordinate [data units]
        y1 (float): y coordinate of the 1st qubit wire
        y2 (float): y coordinate of the 2nd qubit wire
        plot_params (dict): plot parameters
    """
    delta = plot_params['swap_delta']

    lines = []
    for wire_pos in (wire_pos1, wire_pos2):
        lines.append([(gate_pos - delta, wire_pos - delta),
                      (gate_pos + delta, wire_pos + delta)])
        lines.append([(gate_pos - delta, wire_pos + delta),
                      (gate_pos + delta, wire_pos - delta)])
    lines.append([(gate_pos, wire_pos1), (gate_pos, wire_pos2)])

    gate = LineCollection(lines,
                          colors='k',
                          linewidths=plot_params['linewidth'])
    gate.set_label('SWAP')
    axes.add_collection(gate)


def draw_wires(axes, n_labels, gate_grid, wire_grid, plot_params):
    """
    Draws all the circuit qubit wires.

    Args:
        axes (matplotlib.axes.Axes): axes object
        n_labels (int): number of qubit
        gate_grid (ndarray): array with the ref. x positions of the gates
        wire_grid (ndarray): array with the ref. y positions of the qubit
                             wires
        plot_params (dict): plot parameters
    """
    # pylint: disable=invalid-name

    lines = []
    for i in range(n_labels):
        lines.append(((gate_grid[0] - plot_params['column_spacing'],
                       wire_grid[i]), (gate_grid[-1], wire_grid[i])))
    all_lines = LineCollection(lines,
                               linewidths=plot_params['linewidth'],
                               edgecolor='k')
    all_lines.set_label('qubit_wires')
    axes.add_collection(all_lines)


def draw_labels(axes, qubit_labels, drawing_order, wire_grid, plot_params):
    """
    Draws the labels at the start of each qubit wire

    Args:
        axes (matplotlib.axes.Axes): axes object
        qubit_labels (list): labels of the qubit to be drawn
        drawing_order (dict): Mapping between wire indices and qubit IDs
        gate_grid (ndarray): array with the ref. x positions of the gates
        wire_grid (ndarray): array with the ref. y positions of the qubit
                             wires
        plot_params (dict): plot parameters
    """
    for qubit_id in qubit_labels:
        wire_idx = drawing_order[qubit_id]
        text(axes, plot_params['x_offset'], wire_grid[wire_idx],
             qubit_labels[qubit_id], plot_params)
