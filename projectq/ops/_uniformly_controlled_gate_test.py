import cmath
import copy

import numpy as np
import pytest
from scipy.linalg import block_diag


from projectq import MainEngine
from projectq.backends import CommandPrinter
from projectq.ops import BasicGate, Ph, X, Y, Z, H, Measure, Rx,Ry,Rz,CNOT
from projectq.meta import Dagger
from projectq.cengines import AutoReplacer, DecompositionRuleSet, LocalOptimizer
import projectq.setups.decompositions

from . import _uniformly_controlled_gate as ucg
from projectq.setups.decompositions import uniformly_controlled_gate as ucg_dec

def test_basic_decomposition_1_choice():
    a = Rx(np.pi/5).matrix
    b = Ry(np.pi/3).matrix
    v,u,r = ucg._basic_decomposition(a,b)
    d = np.matrix([[np.exp(1j*np.pi/4),0],
                   [0,np.exp(-1j*np.pi/4)]])
    assert np.allclose(a, r.getH()*u*d*v)
    assert np.allclose(b, r*u*d.getH()*v)

    block = np.matrix(block_diag(a,b))
    inverse = np.matrix(block_diag(a,b)).getH()
    print(inverse*block)
    print(block*inverse)

    eng = MainEngine()
    qureg = eng.allocate_qureg(2)
    eng.flush() # makes sure the qubits are allocated in order

    U = ucg._SingleQubitGate(u)
    V = ucg._SingleQubitGate(v)

    target = qureg[0]
    choice = qureg[1]

    with Dagger(eng):
        V | target

        H | target
        CNOT | (choice, target)
        H | target

        Rz(-np.pi/2) | target
        Rz(-np.pi/2) | choice

        U | target

    eng.flush()
    qbit_to_bit_map, final_wavefunction = eng.backend.cheat()
    print(qbit_to_bit_map)
    vec = np.array([final_wavefunction]).T

    reference = np.matrix(block_diag(a,b))
    print(reference*vec)
    assert np.isclose(abs((reference*vec).item(0)), 1)

    Measure | qureg
    eng.flush()

def test_dagger():
    gates = [X,Y,Z,H]

    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    eng = MainEngine(verbose = True, engine_list=[AutoReplacer(rule_set), CommandPrinter(), LocalOptimizer()])
    qureg = eng.allocate_qureg(3)
    eng.flush() # order
    choice = qureg[1:]
    target = qureg[0]

    U = ucg.UniformlyControlledGate(gates)
    U | (choice, target)
    with Dagger(eng):
        U | (choice, target)

    eng.flush()
    qbit_to_bit_map, vec = eng.backend.cheat()
    print(qbit_to_bit_map)

    assert np.isclose(vec.item(0), 1)

    Measure | qureg 
    eng.flush()
