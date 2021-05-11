
import pytest

import projectq
from projectq import MainEngine
from projectq.backends import Simulator
from projectq.cengines import (AutoReplacer, DecompositionRuleSet, DummyEngine,
                               InstructionFilter)
from projectq.meta import Control
from projectq.ops import All, CNOT, CZ, Measure, X, Z

from projectq.setups.decompositions import controlstate


def test_recognize_gates():
    saving_backend = DummyEngine(save_commands=True)
    eng = MainEngine(backend=saving_backend, verbose=True)
    qubit1 = eng.allocate_qubit()
    qubit2 = eng.allocate_qubit()
    qubit3 = eng.allocate_qubit()
    with Control(eng, qubit2,ctrl_state='0'):
        X | qubit1
    with Control(eng, qubit3,ctrl_state='1'):
        X | qubit1
    eng.flush()  # To make sure gates arrive before deallocate gates
    eng.flush(deallocate_qubits=True)
    # Don't test initial 4 allocate and flush
    for cmd in saving_backend.received_commands[2:3]:
        assert controlstate._recognize_offctrl(cmd)
    for cmd in saving_backend.received_commands[4:5]:
        assert not controlstate._recognize_offctrl(cmd)



