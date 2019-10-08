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

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

def to_draw(gates,labels=[],inits={},plot_labels=True,**kwargs):
    """

    :param gates:
    :param label:
    :param inits:
    :param plot_labels:
    :param kwargs:
    :return:
    """
    plot_params = dict(scale=1.0, fontsize=14.0, linewidth=1.0,
                       control_radius=0.05, not_radius=0.15,
                       swap_delta=0.08, label_buffer=0.0)
    plot_params.update(kwargs)
    scale = plot_params['scale']

    # Create labels from gates. This will become slow if there are a lot
    #  of gates, in which case move to an ordered dictionary
    # if not labels:
    #     labels = []
    #     for i, gate in enumerate_gates(gates):
    #         for label in gate[1:]:
    #             if label not in labels:
    #                 labels.append(label)
    
    nq = len(labels)
    ng = len(gates)
    wire_grid = np.arange(0.0, nq * scale, scale, dtype=float)
    gate_grid = np.arange(0.0, ng * scale, scale, dtype=float)

    fig, ax = setup_figure(nq, ng, gate_grid, wire_grid, plot_params)

    measured = measured_wires(gates, labels)
    draw_wires(ax, nq, gate_grid, wire_grid, plot_params, measured)

    if plot_labels:
        draw_labels(ax, labels, inits, gate_grid, wire_grid, plot_params)

    draw_gates(ax, gates, labels, gate_grid, wire_grid, plot_params, measured)
    return ax


def enumerate_gates(l, schedule=False):
    "Enumerate the gates in a way that can take l as either a list of gates or a schedule"
    if schedule:
        for i, gates in enumerate(l):
            for gate in gates:
                yield i, gate
    else:
        for i, gate in enumerate(l):
            yield i, gate
    return


def measured_wires(l, labels, schedule=False):
    "measured[i] = j means wire i is measured at step j"
    # schedule is always false...not implemented.
    measured = {}
    for i, gate in enumerate_gates(l, schedule=schedule):
        name, target = gate[:2]
        j = get_flipped_index(target, labels)
        if name.startswith('M'):
            measured[j] = i
    return measured


def draw_gates(ax, l, labels, gate_grid, wire_grid, plot_params, measured={}, schedule=False):
    x_labels = {label: 0 for label in labels}
    x_position = 0
    for i, gate in enumerate_gates(l, schedule=schedule):
        if len(gate) > 2:  # Controlled
            qb_target = gate[1]
            qb_control = gate[2]

            x_position = max(x_labels[qb_target], x_labels[qb_control])
            draw_controls(ax, x_position, gate, labels, gate_grid, wire_grid, plot_params, measured)

            x_labels[qb_target] = x_position
            draw_target(ax, x_labels[qb_target], gate, labels, gate_grid, wire_grid, plot_params)

            # all the x betweeen control and target has to be added 1...for multi. qubit.
            begin = min(qb_control, qb_target)
            end = max(qb_control, qb_target)

            for itr, value in x_labels.items():
                if begin <= itr <= end:
                    x_labels[itr] = x_position + 1

        else:
            qb = gate[1]

            draw_target(ax, x_labels[qb], gate, labels, gate_grid, wire_grid, plot_params)

            x_labels[qb] = x_labels[qb] + 1

    return


def draw_controls(ax, i, gate, labels, gate_grid, wire_grid, plot_params, measured={}):
    linewidth = plot_params['linewidth']
    scale = plot_params['scale']
    control_radius = plot_params['control_radius']

    # what about multi target, can't set 2 here..
    # make a case, specifically for multi target gate..
    name, target = gate[:2]
    target_index = get_flipped_index(target, labels)

    # what about multi control
    controls = gate[2:]
    control_indices = get_flipped_indices(controls, labels)
    gate_indices = control_indices + [target_index]

    min_wire = min(gate_indices)
    max_wire = max(gate_indices)
    line(ax, gate_grid[i], gate_grid[i], wire_grid[min_wire], wire_grid[max_wire], plot_params)

    ismeasured = False
    for index in control_indices:
        # what is this used for???
        if measured.get(index, 1000) < i:
            ismeasured = True
    if ismeasured:
        dy = 0.04  # TODO: put in plot_params
        line(ax, gate_grid[i] + dy, gate_grid[i] + dy, wire_grid[min_wire], wire_grid[max_wire], plot_params)

    for ci in control_indices:
        x = gate_grid[i]
        y = wire_grid[ci]
        if name in ['SWAP']:
            swapx(ax, x, y, plot_params)
        else:
            cdot(ax, x, y, plot_params)
    return


def draw_target(ax, i, gate, labels, gate_grid, wire_grid, plot_params):
    target_symbols = dict(CNOT='X', CPHASE='Z', NOP='', CX='X', CZ='Z')
    name, target = gate[:2]
    symbol = target_symbols.get(name, name)  # override name with target_symbols, get(keyname,value)
    
    if symbol in ['X'] and len(gate) >= 3:
        name = 'CNOT'
        
    x = gate_grid[i]
    target_index = get_flipped_index(target, labels)
    y = wire_grid[target_index]
    
    if not symbol: return
    if name in ['CNOT', 'TOFFOLI']:
        oplus(ax, x, y, plot_params)
    elif name in ['CPHASE']:
        cdot(ax, x, y, plot_params)
    elif name in ['SWAP']:
        swapx(ax, x, y, plot_params)
    elif name in ['M']:
        draw_mwires(ax, x, y, gate_grid, wire_grid, plot_params)

        text(ax, x, y, symbol, plot_params, box=True)
    else:
        text(ax, x, y, symbol, plot_params, box=True)
    return


def line(ax, x1, x2, y1, y2, plot_params):
    Line2D = matplotlib.lines.Line2D
    line = Line2D((x1, x2), (y1, y2),
                  color='k', lw=plot_params['linewidth'])
    ax.add_line(line)


def text(ax, x, y, textstr, plot_params, box=False):
    linewidth = plot_params['linewidth']
    fontsize = plot_params['fontsize']

    if box:
        bbox = dict(ec='k', fc='w', fill=True, lw=linewidth)  # draw gate box
    else:
        bbox = dict(ec='w', fc='w', fill=False, lw=linewidth)  # draw the qubit box
    ax.text(x, y, textstr, color='k', ha='center', va='center', bbox=bbox, size=fontsize)
    return


def oplus(ax, x, y, plot_params):
    Line2D = matplotlib.lines.Line2D
    Circle = matplotlib.patches.Circle
    not_radius = plot_params['not_radius']
    linewidth = plot_params['linewidth']
    c = Circle((x, y), not_radius, ec='k',
               fc='w', fill=False, lw=linewidth)
    ax.add_patch(c)
    line(ax, x, x, y - not_radius, y + not_radius, plot_params)
    return


def cdot(ax, x, y, plot_params):
    Circle = matplotlib.patches.Circle
    control_radius = plot_params['control_radius']
    scale = plot_params['scale']
    linewidth = plot_params['linewidth']
    c = Circle((x, y), control_radius * scale,
               ec='k', fc='k', fill=True, lw=linewidth)
    ax.add_patch(c)
    return


def swapx(ax, x, y, plot_params):
    d = plot_params['swap_delta']
    linewidth = plot_params['linewidth']
    line(ax, x - d, x + d, y - d, y + d, plot_params)
    line(ax, x - d, x + d, y + d, y - d, plot_params)
    return


def setup_figure(nq, ng, gate_grid, wire_grid, plot_params):
    scale = plot_params['scale']
    fig = plt.figure(
        figsize=(ng * scale, nq * scale),
        facecolor='w',
        edgecolor='w'
    )
    ax = fig.add_subplot(1, 1, 1, frameon=True)
    ax.set_axis_off()
    offset = 0.5 * scale
    ax.set_xlim(gate_grid[0] - offset, gate_grid[-1] + offset)
    ax.set_ylim(wire_grid[0] - offset, wire_grid[-1] + offset)
    ax.set_aspect('equal')
    return fig, ax


def draw_wires(ax, nq, gate_grid, wire_grid, plot_params, measured={}):
    scale = plot_params['scale']
    linewidth = plot_params['linewidth']
    xdata = (gate_grid[0] - scale, gate_grid[-1] + scale)
    for i in range(nq):
        line(ax, gate_grid[0] - scale, gate_grid[-1] + scale, wire_grid[i], wire_grid[i], plot_params)
    return


def draw_mwires(ax, x, y, gate_grid, wire_grid, plot_params):
    # Add the doubling for measured wires:
    scale = plot_params['scale']
    dy = 0.04  # TODO: add to plot_params

    line(ax, x, gate_grid[-1] + scale, y + dy, y + dy, plot_params)

    # wired_grid indicate which qubit it belongs to
    # gate_grid is the x-axes, x2=grid_grid[-1], so it will always draw the line to the end.
    return


def draw_labels(ax, labels, inits, gate_grid, wire_grid, plot_params):
    scale = plot_params['scale']
    label_buffer = plot_params['label_buffer']
    fontsize = plot_params['fontsize']
    nq = len(labels)
    xdata = (gate_grid[0] - scale, gate_grid[-1] + scale)
    for i in range(nq):
        j = get_flipped_index(labels[i], labels)
        text(ax, xdata[0] - label_buffer, wire_grid[j], render_label(labels[i], inits), plot_params)
    return


def get_flipped_index(target, labels):
    """Get qubit labels from the rest of the line,and return indices

    >>> get_flipped_index('q0', ['q0', 'q1'])
    1
    >>> get_flipped_index('q1', ['q0', 'q1'])
    0
    """
    nq = len(labels)
    i = labels.index(target)
    return nq - i - 1


def get_flipped_indices(targets, labels): return [get_flipped_index(t, labels) for t in targets]


def render_label(label, inits={}):
    """Slightly more flexible way to render labels.

    >>> render_label('q0')
    '$|q0\\\\rangle$'
    >>> render_label('q0', {'q0':'0'})
    '$|0\\\\rangle$'
    """
    if label in inits:
        s = inits[label]
        if s is None:
            return ''
        else:
            return r'$|%s\rangle$' % inits[label]
    return r'$|%s\rangle$' % label
