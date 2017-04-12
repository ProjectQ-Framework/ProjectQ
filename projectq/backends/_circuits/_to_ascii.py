# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict

from projectq.ops import Command, Allocate, Deallocate, Swap, XGate


def _between_wire_pattern(cur_role, next_role):
    cur_in = 'register' in cur_role
    next_in = 'register' in next_role
    change = next_role != cur_role

    if change and cur_in and next_in:
        return '├──┤'
    if change and next_in:
        return '┌─┴┐'
    if change and cur_in:
        return '└─┬┘'
    if cur_in:
        return '│  │'
    return '  │ '


def _on_wire_pattern(role):
    return ('  • ' if 'control' in role
            else '┤  ├' if 'register' in role
            else '──┼─')


def _between_wire_cols(has_controls, used_indices, roles, index_to_id, w,
                       border):
    between_wires = []
    prev_role = {}
    n = len(index_to_id)
    for i in range(n + 1):
        role = set() if i >= n else roles[index_to_id[i]]

        spacing_w = w - 3 if border else w - 1
        w1 = spacing_w // 2
        w2 = spacing_w - w1

        has_control_line = (has_controls and
                            min(used_indices) < i <= max(used_indices))
        pattern = _between_wire_pattern(prev_role, role)
        space = pattern[1] if border else ' '
        mid = (space if not has_control_line
               else '│' if not border
               else pattern[2])
        center = space * w1 + mid + space * w2
        full = pattern[0] + center + pattern[3] if border else center
        between_wires.append(full)
        prev_role = role
    return between_wires


def _on_wire_cols(name, has_controls, used_indices, roles, index_to_id, w,
                  border):
    on_wires = []
    used = False
    for i in range(len(index_to_id)):
        role = roles[index_to_id[i]]
        if not border and 'register' in role:
            on_wires.append(name)
            continue
        pattern = _on_wire_pattern(role)
        has_control_line = (has_controls and
                            min(used_indices) <= i <= max(used_indices))
        spacing_w = w - 3 if border else w - 1
        w1 = spacing_w // 2
        w2 = spacing_w - w1

        space = pattern[1] if border else '─'
        control_line = pattern[2]
        mid = control_line if has_control_line else space
        center = space * w1 + mid + space * w2
        if 'register' in role and not used:
            center = ' ' + name + ' '
            used = True
        full = pattern[0] + center + pattern[3] if border else center
        on_wires.append(full)
    return on_wires


def _name_border(cmd):
    if cmd.gate is Allocate:
        return '|0⟩', False
    if cmd.gate is Deallocate:
        return '┤  ', False
    if cmd.gate is Swap:
        return '×', False
    if isinstance(cmd.gate, XGate):
        return '⊕', False
    return str(cmd.gate), True


def _wire_col(cmd, id_to_index, index_to_id):
    roles = defaultdict(set)

    used_indices = [id_to_index[c.id]
                    for reg in cmd.all_qubits
                    for c in reg]

    for c in cmd.control_qubits:
        roles[c.id].add('control')
    for i in range(len(cmd.qubits)):
        for q in cmd.qubits[i]:
            roles[q.id].add('register')
            roles[q.id].add('register' + str(i))

    name, border = _name_border(cmd)
    w = len(name) + (4 if border else 0)

    between_wires = _between_wire_cols(len(cmd.control_qubits) > 0,
                                       used_indices,
                                       roles,
                                       index_to_id,
                                       w,
                                       border)
    on_wires = _on_wire_cols(name,
                             len(cmd.control_qubits) > 0,
                             used_indices,
                             roles,
                             index_to_id,
                             w,
                             border)
    col = []
    for i in range(len(id_to_index)):
        col.append(between_wires[i])
        col.append(on_wires[i])
    col.append(between_wires[-1])
    return col


def commands_to_ascii_circuit(commands):
    """
    Args:
        commands (list[Command]): Commands making up the circuit.
    Returns:
        str:
            Fixed-width text drawing using ascii and unicode characters.
    """
    qubit_ids = set(qubit.id
                    for cmd in commands
                    for qureg in cmd.all_qubits
                    for qubit in qureg)
    n = len(qubit_ids)
    index_to_id = {}
    id_to_index = {}
    for id in sorted(qubit_ids):
        index = len(index_to_id)
        index_to_id[index] = id
        id_to_index[id] = index

    empty_col = ([' ', '─'] * (n + 1))[:-1]
    init_col = (['    ', '|0⟩─'] * (n + 1))[:-1]

    cols = [init_col]
    skipping_allocs = True
    for cmd in commands:
        if skipping_allocs and cmd.gate is Allocate:
            continue
        skipping_allocs = False
        cols.append(_wire_col(cmd, id_to_index, index_to_id))
        cols.append(empty_col)

    return '\n'.join(''.join(col[row]
                             for col in cols).rstrip()
                     for row in range(len(empty_col))).strip()
