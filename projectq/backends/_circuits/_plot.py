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

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
from matplotlib.patches import Arc


def to_draw(gates, labels=None, inits=None, plot_labels=True, **kwargs):
    """
    Use Matplotlib to plot a quantum circuit.
    Args:
        gates (list): List of tuples for each gate in the quantum circuit.
            (name,target,control1,control2...). Targets and controls initially
             defined in terms of labels.
        labels (list): Qubits' index in the quantum circuit
        inits (dict): Initialization list of gates, optional
        plot_labels (bool): If plot_labels is false, the qubits' label will not
            be drawed.
        **kwargs (dict): Can override plot_parameters
    """
    if labels is None:
        labels = []

    if inits is None:
        inits = {label: 0 for label in labels}

    plot_params = dict(scale=1.0, fontsize=14.0, linewidth=1.0,
                       linebetween=0.06, control_radius=0.05, not_radius=0.15,
                       swap_delta=0.08, label_buffer=0.0)
    plot_params.update(kwargs)
    scale = plot_params['scale']

    n_labels = len(labels)
    n_gates = len(gates)

    # create grid for the plot
    wire_grid = np.arange(0.0, n_labels * scale, scale, dtype=float)
    gate_grid = np.arange(0.0, n_gates * scale, scale, dtype=float)
    if len(gate_grid) == 0:
        gate_grid = wire_grid

    fig, axes = setup_figure(n_labels, n_gates, gate_grid, wire_grid, plot_params)

    draw_wires(axes, n_labels, gate_grid, wire_grid, plot_params)

    if plot_labels:
        draw_labels(axes, labels, inits, gate_grid, wire_grid, plot_params)

    draw_gates(axes, gates, labels, gate_grid, wire_grid, plot_params)
    return fig, axes


def draw_gates(axes, gates, labels, gate_grid, wire_grid, plot_params):
    """
    matching the position of each gate to the figure and draw each gate
    Args:
        ax (AxesSubplot): axes object
        gates (list): List of tuples for each gate in the quantum circuit.
        labels (list): contains qubits' label
        gate_grid (ndarray): grid for positioning gate
        wire_grid (ndarray): grid for positioning wires
        plot_params (dict): parameter for the figure
    """

    # initialize the position of gates as 0 for each qubit label
    x_labels = {label: 0 for label in labels}
    x_position = 0
    check_gate_length = False  # keep track of the last gate length

    for gate in gates:
        if len(gate) > 2:  # case: multi-control or target gate
            gate_name, qb_target, qb_control = gate
            tar_max = max(qb_target)
            tar_min = min(qb_target)
            ctr_max = max(qb_control)
            ctr_min = min(qb_control)

            # get the index of qubit between control and target qubit
            begin = min(ctr_min, tar_min)
            end = max(ctr_max, tar_max)

            # check the max position between control and target gate
            max_position = max(x_labels[tar_max], x_labels[ctr_max])
            check_max = False
            for qb_id in range(begin, end + 1):
                if x_labels[qb_id] > max_position:
                    check_max = True
                    break
            if check_max:
                x_position = max(x_labels.values())
            else:
                x_position = max_position

            draw_controls(axes, x_position, gate, labels,
                          gate_grid, wire_grid, plot_params)

            for qb_id in qb_target:
                x_labels[qb_id] = x_position

            draw_target(axes, x_labels, gate, labels,
                        gate_grid, wire_grid, plot_params)
            draw_lines(axes, x_labels, gate, labels,
                       gate_grid, wire_grid, plot_params)

            # update x position between control and target qubit
            distance = 2 if len(gate_name) > 4 else 1
            check_gate_length = (distance == 2)
            for itr in x_labels:
                if begin <= itr <= end:
                    x_labels[itr] = x_position + distance

        else:
            # get target qubit (tuple)
            _, target_qubits = gate
            # if the last gate length > 4
            if check_gate_length:
                for qb_id in target_qubits:
                    x_labels[qb_id] = x_labels[qb_id] - 1

            draw_target(axes, x_labels, gate, labels,
                        gate_grid, wire_grid, plot_params)
            draw_lines(axes, x_labels, gate, labels,
                       gate_grid, wire_grid, plot_params)

            if len(target_qubits) > 1:
                begin = min(target_qubits)
                end = max(target_qubits)
                for itr in x_labels:
                    if begin <= itr <= end:
                        x_labels[itr] = x_labels[itr] + 1
            else:
                qb_id = target_qubits[0]
                x_labels[qb_id] = x_labels[qb_id] + 1

            check_gate_length = False

def draw_lines(axes, x_labels, gate, labels, gate_grid, wire_grid, plot_params):
    """
    draw the wires of connection between gates and control qubits
    Args:
        ax (AxesSubplot): axes object
        x_labels (dict): the x position of each qubit
        gate (tuple): control qubit gate
        labels (list): contains qubits' label
        gate_grid (ndarray): grid for positioning gate
        wire_grid (ndarray): grid for positioning wires
        plot_params (dict): parameter for the figure
    """

    if len(gate) == 3:
        _, targets, controls = gate

        tar_indices = get_flipped_indices(targets, labels)

        # include multi-control gate
        ctr_indices = get_flipped_indices(controls, labels)

        i = x_labels[targets[0]]
        tar_max = max(tar_indices)
        tar_min = min(tar_indices)
        ctr_max = max(ctr_indices)
        ctr_min = min(ctr_indices)

        min_wire = min(tar_min, ctr_min)
        max_wire = max(tar_max, ctr_max)
        line(axes, (gate_grid[i], gate_grid[i]),
             (wire_grid[min_wire], wire_grid[max_wire]), plot_params)
    else:
        _, targets = gate

        tar_indices = get_flipped_indices(targets, labels)
        i = x_labels[targets[0]] # use the first target qubit position

        tar_max = max(tar_indices)
        tar_min = min(tar_indices)
        line(axes, (gate_grid[i], gate_grid[i]),
             (wire_grid[tar_min], wire_grid[tar_max]), plot_params)


def draw_controls(axes, i, gate, labels, gate_grid, wire_grid, plot_params):
    """
    draw the control qubit gate
    Args:
        ax (AxesSubplot): axes object
        i (int): position of the control gate
        gate (tuple): control qubit gate
        labels (list): contains qubits' label
        gate_grid (ndarray): grid for positioning gate
        wire_grid (ndarray): grid for positioning wires
        plot_params (dict): parameter for the figure
    """

    _, _, controls = gate

    # include multi-control gate
    ctr_indices = get_flipped_indices(controls, labels)

    for cidx in ctr_indices:
        cdot(axes, gate_grid[i], wire_grid[cidx], plot_params)


def draw_target(axes, x_labels, gate, labels, gate_grid, wire_grid, plot_params):
    """
    draw the target gate in figure
    Args:
        ax (AxesSubplot): axes object
        x_labels (dict): the x position of each qubit
        gate (tuple): control qubit gate
        labels (list): contains qubits' label
        gate_grid (ndarray): grid for positioning gate
        wire_grid (ndarray): grid for positioning wires
        plot_params (dict): parameter for the figure
    """
    # pylint: disable=invalid-name

    if len(gate) == 3:
        name, targets, _ = gate
    else:
        name, targets = gate

    for qb_id in targets:
        i = x_labels[qb_id]
        x = gate_grid[i]

        target_index = get_flipped_index(qb_id, labels)
        y = wire_grid[target_index]

        if name in ('X', 'CNOT', 'TOFFOLI'):
            oplus(axes, x, y, plot_params)
        elif name == 'CPHASE':
            cdot(axes, x, y, plot_params)
        elif name == 'Swap':
            swapx(axes, x, y, plot_params)
        elif name == 'Measure':
            draw_mwires(axes, x, y, gate_grid, wire_grid, plot_params)
            measure(axes, x, y, plot_params)
        else:
            text(axes, x, y, name, plot_params, box=True)


def measure(axes, x, y, plot_params):
    """
    drawing the measure gate
    Args:
        ax (AxesSubplot): axes object
        x (float): x coordinate
        y (float): y coordinate
        plot_params (dict): parameter for the figure
    """
    # pylint: disable=invalid-name

    height = 0.65
    width = 0.65

    # add box
    text(axes, x, y, '   ', plot_params, box=True)
    # add measure symbol
    arc = Arc(xy=(x, y - 0.15 * height), width=width * 0.60,
              height=height * 0.7, theta1=0, theta2=180,
              fill=False, linewidth=1, zorder=5)
    axes.add_patch(arc)
    axes.plot([x, x + 0.35 * width],
              [y - 0.15 * height, y + 0.20 * height], color='k',
              linewidth=1, zorder=5)


def line(axes, xdata, ydata, plot_params):
    """
    draw line in the plot, begin at (x1, y1) and end at (x2, y2)
    Args:
        ax (AxesSubplot): axes object
        x1 (float): x_1 coordinate
        x2 (float): x_2 coordinate
        y1 (float): y_1 coordinate
        y2 (float): y_2 coordinate
        plot_params (dict): parameter for the figure
    """
    axes.add_line(Line2D(xdata, ydata,
                         color='k', lw=plot_params['linewidth']))


def text(axes, x, y, textstr, plot_params, box=False):
    """
    draw the name of gate or qubit and draw the rectangle box at (x, y)
    Args:
        ax (AxesSubplot): axes object
        x (float): x coordinate
        y (float): y coordinate
        textstr (str): text of the gate and box
        plot_params (dict): parameter for the text
        box (bool): draw the rectangle box if box is True
    """
    # pylint: disable=invalid-name

    linewidth = plot_params['linewidth']
    fontsize = plot_params['fontsize']

    if box:
        # draw gate box
        bbox = dict(ec='k', fc='w', fill=True, lw=linewidth)
    else:
        # draw the qubit box
        bbox = dict(ec='w', fc='w', fill=False, lw=linewidth)
    # draw the text
    axes.text(x, y, textstr, color='k', ha='center', va='center',
              bbox=bbox, size=fontsize)


def oplus(axes, x, y, plot_params):
    """
    Draw the Symbol for control gate
    Args:
        ax (AxesSubplot): axes object
        x (float): x coordinate
        y (float): y coordinate
        plot_params (dict): parameter for the text
    """
    # pylint: disable=invalid-name

    not_radius = plot_params['not_radius']
    linewidth = plot_params['linewidth']

    axes.add_patch(Circle((x, y), not_radius, ec='k',
                          fc='w', fill=False, lw=linewidth))

    line(axes, (x, x), (y - not_radius, y + not_radius), plot_params)

def cdot(axes, x, y, plot_params):
    """
    draw the control dot for control gate
    Args:
        ax (AxesSubplot): axes object
        x (float): x coordinate
        y (float): y coordinate
        plot_params (dict): parameter for the text
    """
    # pylint: disable=invalid-name

    control_radius = plot_params['control_radius']
    scale = plot_params['scale']
    linewidth = plot_params['linewidth']

    axes.add_patch(Circle((x, y), control_radius * scale,
                          ec='k', fc='k', fill=True, lw=linewidth))

def swapx(axes, x, y, plot_params):
    """
    draw the SwapX symbol
    Args:
        ax (AxesSubplot): axes object
        x (float): x coordinate
        y (float): y coordinate
        plot_params (dict): parameter for the text
    """
    # pylint: disable=invalid-name

    d = plot_params['swap_delta']
    line(axes, (x - d, x + d), (y - d, y + d), plot_params)
    line(axes, (x - d, x + d), (y + d, y - d), plot_params)

def setup_figure(n_labels, n_gates, gate_grid, wire_grid, plot_params):
    """
    Create the figure and set up the parameter of figure
    Args:
        n_labels (int): number of labels representing qubits
        n_gates (int): number of gates to be drawed
        gate_grid (ndarray): grid for positioning gates
        wire_grid (ndarray): grid for positioning wires
        plot_params (dict): parameter for the figure
    Returns:
    return the Figure and AxesSubplot object
    """
    scale = plot_params['scale']
    width = n_gates * scale
    height = n_labels * scale
    if width == 0:
        width = height

    fig = plt.figure(
        figsize=(width, height),
        facecolor='w',
        edgecolor='w'
    )

    axes = plt.subplot()
    axes.set_axis_off()
    offset = scale

    axes.set_xlim(gate_grid[0] - offset, gate_grid[-1] + offset)
    axes.set_ylim(wire_grid[0] - offset, wire_grid[-1] + offset)
    axes.set_aspect('equal')
    return fig, axes

def draw_wires(axes, n_labels, gate_grid, wire_grid, plot_params):
    """
    draw the circuit wire
    Args:
        ax (AxesSubplot): axes object
        n_labels (int): number of qubit
        gate_grid (ndarray): grid for positioning gates
        wire_grid (ndarray): grid for positioning wires
        plot_params (dict): parameter for the figure
    """
    # pylint: disable=invalid-name

    scale = plot_params['scale']
    x_pos = (gate_grid[0] - 0.5 * scale, gate_grid[-1] + 2 * scale)

    for i in range(n_labels):
        line(axes, (x_pos[0], x_pos[-1]),
             (wire_grid[i], wire_grid[i]), plot_params)

def draw_mwires(axes, x, y, gate_grid, wire_grid, plot_params):
    """
    Add the doubling for measured wires
    Args:
        ax (AxesSubplot): axes object
        x (float): x coordinate
        y (float): y coordinate
        gate_grid (ndarray): grid for positioning gate
        wire_grid (ndarray): grid for positioning wires
        plot_params (dict): parameter for the figure
    """
    # pylint: disable=invalid-name

    scale = plot_params['scale']
    dy = plot_params['linebetween']

    # gate_grid indicate x-axes
    line(axes, (x, gate_grid[-1] + 2 * scale), (y + dy, y + dy), plot_params)

def draw_labels(axes, labels, inits, gate_grid, wire_grid, plot_params):
    """
    draw the qubit label
    Args:
        ax (AxesSubplot): axes object
        labels (list): labels of the qubit to be drawed
        inits (list): Initialization of qubits
        gate_grid (ndarray): grid for positioning gate
        wire_grid (ndarray): grid for positioning wires
        plot_params (dict): parameter for the figure
    """
    scale = plot_params['scale']
    label_buffer = plot_params['label_buffer']
    n_labels = len(labels)
    if inits is None:
        inits = {label: 0 for label in labels}
    xdata = (gate_grid[0] - scale, gate_grid[-1] + scale)
    for i in range(n_labels):
        j = get_flipped_index(labels[i], labels)
        text(axes, xdata[0] - label_buffer, wire_grid[j],
             render_label(labels[i], inits), plot_params)

def get_flipped_index(target, labels):
    """
    flip the index of the target qubit in order to match the coordination

    >>> get_flipped_index('q0', ['q0', 'q1'])
    1
    >>> get_flipped_index('q1', ['q0', 'q1'])
    0

    Args:
        target (str): target qubit
        labels (list): contains all labels of qubits
    """

    n_labels = len(labels)
    i = labels.index(target)

    return n_labels - i - 1

def get_flipped_indices(targets, labels):
    """
    flip the index of the target qubit for multi targets
    Args:
        targets (tuple): target qubit
        labels (list): contains all labels of qubits
    """
    return [get_flipped_index(t, labels) for t in targets]

def render_label(label, inits):
    """
    render qubit label as |0>
    Args:
        label: label of the qubit
        inits (list): initial qubits
    """
    if label in inits:
        if inits[label] is None:
            return ''
        return  r'$|{}\rangle$'.format(inits[label])
    return r'$|{}\rangle$'.format(label)
