# -*- coding: utf-8 -*-
# pylint: skip-file

import os
import sys

from projectq import MainEngine
from projectq.backends import CircuitDrawer
from projectq.ops import (
    X,
    Y,
    Z,
    Rx,
    Ry,
    Rz,
    Ph,
    S,
    T,
    H,
    Toffoli,
    Barrier,
    Swap,
    SqrtSwap,
    SqrtX,
    C,
    CNOT,
    Entangle,
    QFT,
    TimeEvolution,
    QubitOperator,
    BasicMathGate,
    Measure,
    All,
    Tensor,
    get_inverse,
)


def zoo_profile():
    '''
    Generate and display the zoo of quantum gates.
    '''
    # create a main compiler engine with a drawing backend
    drawing_engine = CircuitDrawer()
    locations = {0: 1, 1: 2, 2: 0, 3: 3}
    drawing_engine.set_qubit_locations(locations)
    main_eng = MainEngine(drawing_engine)
    qureg = main_eng.allocate_qureg(4)

    # define a zoo of gates
    te_gate = TimeEvolution(0.5, 0.1 * QubitOperator('X0 Y2'))

    def add(x, y):
        return x, y + 1

    zoo = [
        (X, 3),
        (Y, 2),
        (Z, 0),
        (Rx(0.5), 2),
        (Ry(0.5), 1),
        (Rz(0.5), 1),
        (Ph(0.5), 0),
        (S, 3),
        (T, 2),
        (H, 1),
        (Toffoli, (0, 1, 2)),
        (Barrier, None),
        (Swap, (0, 3)),
        (SqrtSwap, (0, 1)),
        (get_inverse(SqrtSwap), (2, 3)),
        (SqrtX, 2),
        (C(get_inverse(SqrtX)), (0, 2)),
        (C(Ry(0.5)), (2, 3)),
        (CNOT, (2, 1)),
        (Entangle, None),
        (te_gate, None),
        (QFT, None),
        (Tensor(H), None),
        (BasicMathGate(add), (2, 3)),
        (All(Measure), None),
    ]

    # apply them
    for gate, pos in zoo:
        if pos is None:
            gate | qureg
        elif isinstance(pos, tuple):
            gate | tuple(qureg[i] for i in pos)
        else:
            gate | qureg[pos]

    main_eng.flush()

    # generate latex code to draw the circuit
    s = drawing_engine.get_latex()
    prefix = 'zoo'
    with open('{}.tex'.format(prefix), 'w') as f:
        f.write(s)

    # compile latex source code and open pdf file
    os.system('pdflatex {}.tex'.format(prefix))
    openfile('{}.pdf'.format(prefix))


def openfile(filename):
    '''
    Open a file.

    Args:
        filename (str): the target file.

    Return:
        bool: succeed if True.
    '''
    platform = sys.platform
    if platform == "linux" or platform == "linux2":
        os.system('xdg-open %s' % filename)
    elif platform == "darwin":
        os.system('open %s' % filename)
    elif platform == "win32":
        os.startfile(filename)
    else:
        print('Can not open file, platform %s not handled!' % platform)
        return False
    return True


if __name__ == "__main__":
    zoo_profile()
