# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from projectq.backends._circuits import commands_to_ascii_circuit
from projectq.ops import Command, X, Swap
from projectq.types import Qureg, Qubit


def test_empty_circuit():
    assert commands_to_ascii_circuit([]) == ''


def test_addition_circuit():
    commands = []
    eng = None
    qs = [Qureg([Qubit(eng, idx=i)]) for i in range(10)]

    for i in range(10):
        if i != 4:
            commands.append(Command(eng, X, (qs[i],), controls=qs[4]))
    for i in range(4):
        commands.append(Command(eng, X, (qs[5+i],), controls=qs[4]))
        commands.append(Command(eng, Swap, (qs[4], qs[i]), controls=qs[5+i]))
    commands.append(Command(eng, X, (qs[-1],), controls=qs[4]))
    for i in range(4)[::-1]:
        commands.append(Command(eng, Swap, (qs[4], qs[i]), controls=qs[5+i]))
        commands.append(Command(eng, X, (qs[5+i],), controls=qs[i]))
    for i in range(10):
        if i != 4:
            commands.append(Command(eng, X, (qs[i],), controls=qs[4]))

    assert commands_to_ascii_circuit(commands) == '''
|0⟩─⊕───────────────────×───────────────────────────×─•─⊕─────────────────
    │                   │                           │ │ │
|0⟩─┼─⊕─────────────────┼───×───────────────────×─•─┼─┼─┼─⊕───────────────
    │ │                 │   │                   │ │ │ │ │ │
|0⟩─┼─┼─⊕───────────────┼───┼───×───────────×─•─┼─┼─┼─┼─┼─┼─⊕─────────────
    │ │ │               │   │   │           │ │ │ │ │ │ │ │ │
|0⟩─┼─┼─┼─⊕─────────────┼───┼───┼───×───×─•─┼─┼─┼─┼─┼─┼─┼─┼─┼─⊕───────────
    │ │ │ │             │   │   │   │   │ │ │ │ │ │ │ │ │ │ │ │
|0⟩─•─•─•─•─•─•─•─•─•─•─×─•─×─•─×─•─×─•─×─┼─×─┼─×─┼─×─┼─•─•─•─•─•─•─•─•─•─
            │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │         │ │ │ │ │
|0⟩─────────⊕─┼─┼─┼─┼─⊕─•─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─•─⊕─────────⊕─┼─┼─┼─┼─
              │ │ │ │     │ │ │ │ │ │ │ │ │ │ │ │ │               │ │ │ │
|0⟩───────────⊕─┼─┼─┼─────⊕─•─┼─┼─┼─┼─┼─┼─┼─┼─┼─•─⊕───────────────⊕─┼─┼─┼─
                │ │ │         │ │ │ │ │ │ │ │ │                     │ │ │
|0⟩─────────────⊕─┼─┼─────────⊕─•─┼─┼─┼─┼─┼─•─⊕─────────────────────⊕─┼─┼─
                  │ │             │ │ │ │ │                           │ │
|0⟩───────────────⊕─┼─────────────⊕─•─┼─•─⊕───────────────────────────⊕─┼─
                    │                 │                                 │
|0⟩─────────────────⊕─────────────────⊕─────────────────────────────────⊕─
    '''.strip()
