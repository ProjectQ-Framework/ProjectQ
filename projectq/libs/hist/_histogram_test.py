from projectq import MainEngine
from projectq.ops import H, C, X, Measure, All
from projectq.backends import Simulator
from projectq.libs import histogram
import pytest
from pytest import approx
import matplotlib

@pytest.fixture(scope="module")
def matplotlib_setup():
    old_backend = matplotlib.get_backend()
    matplotlib.use('agg') # avoid showing the histogram plots
    yield
    matplotlib.use(old_backend)

def test_qubit(matplotlib_setup):
    sim = Simulator()
    eng = MainEngine(sim)
    qb = eng.allocate_qubit()
    eng.flush()
    fig, axes, prob = histogram(sim, qb)
    assert prob["0"] == approx(1)
    assert prob["1"] == approx(0)
    H | qb
    eng.flush()
    fig, axes, prob = histogram(sim, qb)
    assert prob["0"] == approx(0.5)
    Measure | qb
    eng.flush()
    fig, axes, prob = histogram(sim, qb)
    assert prob["0"] == approx(1) or prob["1"] == approx(1)


def test_qureg(matplotlib_setup):
    sim = Simulator()
    eng = MainEngine(sim)
    qr = eng.allocate_qureg(3)
    eng.flush()
    fig, axes, prob = histogram(sim, qr)
    assert prob["000"] == approx(1)
    assert prob ["110"] == approx(0)
    H | qr[0]
    C(X, 1) | (qr[0], qr[1])
    H | qr[2]
    eng.flush()
    fig, axes, prob = histogram(sim, qr)
    assert prob["110"] == approx(0.25)
    assert prob["100"] == approx(0)
    All(Measure) | qr
    eng.flush()
    fig, axes, prob = histogram(sim, qr)
    assert prob["000"] == approx(1) or prob["001"] == approx(1) or prob["110"] == approx(1) or prob["111"] == approx(1)
    assert prob["000"] + prob["001"] + prob["110"] + prob["111"] == approx(1)


def test_combination(matplotlib_setup):
    sim = Simulator()
    eng = MainEngine(sim)
    qr = eng.allocate_qureg(2)
    qb = eng.allocate_qubit()
    eng.flush()
    fig, axes, prob = histogram(sim, [qr, qb])
    assert prob["000"] == approx(1)
    H | qr[0]
    C(X, 1)| (qr[0], qr[1])
    H | qb
    Measure | qr[0]
    eng.flush()
    fig, axes, prob = histogram(sim, [qr, qb])
    assert (prob["000"] == approx(0.5) and prob["001"] == approx(0.5)) or (prob["110"] == approx(0.5) and prob["111"] == approx(0.5))
    assert prob["100"] == approx(0)
    Measure | qb


def test_too_many_qubits():
    sim = Simulator()
    eng = MainEngine(sim)
    qr = eng.allocate_qureg(6)
    eng.flush()
    fig, axes, prob = histogram(sim, qr)
    assert prob["000000"] == approx(1)
    All(Measure)
