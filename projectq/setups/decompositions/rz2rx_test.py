
"Tests for projectq.setups.decompositions.rx2rz.py"

import math

import pytest

from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               DummyEngine, InstructionFilter, MainEngine)
from projectq.meta import Control
from projectq.ops import Measure, Ph, Rz

from . import rz2rx

def test_recognize_correct_gates():
    """ Checks that the recognize_RzNoCtrl behaves as it should """
    # Creates a circuit and checks that the recognize_RzNoCtrl
    # asserts correctly that there is/isn't a ctrl qubit in a given command
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend)
    qubit = eng.allocate_qubit()
    ctrl_qubit = eng.allocate_qubit()
    eng.flush()
    Rz(0.3) | qubit
    with Control(eng, ctrl_qubit):
        Rz(0.4) | qubit
    eng.flush(deallocate_qubits=True)
    assert rz2rx._recognize_RzNoCtrl(saving_backend.received_commands[3])
    assert not rz2rx._recognize_RzNoCtrl(saving_backend.received_commands[4])


def rz_decomp_gates(eng, cmd):
    """ Check that cmd.gate is the gate Rz """
    g = cmd.gate
    if isinstance(g, Rz):
        return False
    else:
        return True


@pytest.mark.parametrize("angle", [0, math.pi, 2*math.pi, 4*math.pi, 0.5])
def test_decomposition(angle):
    """ Test whether the decomposition of Rz results in  
    the same superposition of |0> and |1> as just using Rz """
    for basis_state in ([1, 0], [0, 1]):
        correct_dummy_eng = DummyEngine(save_commands=True)
        correct_eng = MainEngine(backend=Simulator(),
                                 engine_list=[correct_dummy_eng])

        rule_set = DecompositionRuleSet(modules=[rz2rx])
        test_dummy_eng = DummyEngine(save_commands=True)
        test_eng = MainEngine(backend=Simulator(),
                              engine_list=[AutoReplacer(rule_set),
                                           InstructionFilter(rz_decomp_gates),
                                           test_dummy_eng])

        correct_qb = correct_eng.allocate_qubit()
        Rz(angle) | correct_qb
        correct_eng.flush()

        test_qb = test_eng.allocate_qubit()
        Rz(angle) | test_qb
        test_eng.flush()

        assert correct_dummy_eng.received_commands[1].gate == Rz(angle)
        assert test_dummy_eng.received_commands[1].gate != Rz(angle)

        for fstate in ['0', '1']:
            test = test_eng.backend.get_amplitude(fstate, test_qb)
            correct = correct_eng.backend.get_amplitude(fstate, correct_qb)
            assert correct == pytest.approx(test, rel=1e-12, abs=1e-12)

        Measure | test_qb
        Measure | correct_qb