import numpy as np

from projectq import MainEngine
from projectq.ops import CNOT, H
from projectq.tests.helpers import PhaseAgnosticStateComparator


def test_hadamard_twice():
    eng = MainEngine()
    q = eng.allocate_qureg(1)
    H | q[0]
    H | q[0]
    eng.flush()
    _, actual = eng.backend.cheat()
    expected = np.array([1, 0], dtype=complex)
    comparator = PhaseAgnosticStateComparator()
    comparator.compare(actual, expected)


def test_bell_state():
    eng = MainEngine()
    q = eng.allocate_qureg(2)
    H | q[0]
    CNOT | (q[0], q[1])
    eng.flush()
    _, actual = eng.backend.cheat()
    expected = np.array([1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)], dtype=complex)
    comparator = PhaseAgnosticStateComparator()
    comparator.compare(actual, expected)
