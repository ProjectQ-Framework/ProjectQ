from projectq import MainEngine
from projectq.ops import Measure, X, UniformlyControlledGate, Isometry
from projectq.backends import CommandPrinter
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute
import projectq.setups.decompositions
from projectq.cengines import InstructionFilter, AutoReplacer, DecompositionRuleSet

import numpy as np
import math
import cmath
import copy
import random
import pytest

from . import isometry as iso

def normalize(v):
    return v/np.linalg.norm(v,2)

# def test_ab():
#     k = 0xdeadbeef
#     assert iso.a(k, 16) == 0xdead
#     assert iso.b(k, 16) == 0xbeef
#     assert iso.a(k, 0) == k
#     assert iso.b(k, 0) == 0

# def test_to_zero_gate():
#     U = iso.ToZeroGate()
#     U.c0 = 2+1j
#     U.c1 = 1-2j
#     matrix = U.matrix
#     vec = normalize(np.matrix([[U.c0],[U.c1]]))
#     assert np.allclose(matrix.H * matrix, np.eye(2))
#     assert np.allclose(matrix * vec, [[1], [0]])

def filter_function(self, cmd):
    if(isinstance(cmd.gate, UniformlyControlledGate)):
        return False
    if(isinstance(cmd.gate, DiagonalGate)):
        return False
    return cmd.engine.backend.is_available(cmd)

# def test_state_prep():
#     target_state = np.array([1.j,2.,3.j,4.,-5.j,6.,1+7.j,8.+3.j])
#     target_state = target_state/np.linalg.norm(target_state, 2)
#     V = [target_state]
#
#     filter = InstructionFilter(filter_function)
#     rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
#     eng = MainEngine(engine_list=[AutoReplacer(rule_set)])
#     qureg = eng.allocate_qureg(3)
#     eng.flush() # order
#
#     iso._apply_isometry(V,qureg)
#     eng.flush()
#
#     order, result = eng.backend.cheat()
#     print(order)
#
#     iso._print_vec(target_state)
#     iso._print_qureg(qureg)
#     assert np.allclose(result, target_state)
#
#     Measure | qureg
#     eng.flush()
#
# # @pytest.mark.parametrize("k,n", [(k,n) for n in range(1,5) for k in range(2**n)])
# # def test_disentangle(k, n):
# #     eng = MainEngine()
# #     qureg = eng.allocate_qureg(n)
# #     wf = np.array([0.]*k + [1.]*(2**n-k)) / math.sqrt(2**n-k)
# #     eng.flush()
# #     eng.backend.set_wavefunction(wf,qureg)
# #     for s in range(n):
# #         iso._disentangle(k, s, [], )
# #     assert abs(iso.c(qureg, k)) == pytest.approx(1., 1e-10)
# #     Measure | qureg
# #     eng.flush()
#
# def test_2_columns():
#     col_0 = normalize(np.array([1.j,2.,3.j,4.,-5.j,6.,1+7.j,8.]))
#     col_1 = normalize(np.array([8.j,7.,6.j,5.,-4.j,3.,1+2.j,1.]))
#     # must be orthogonal
#     col_1 = normalize(col_1 - col_0*(np.vdot(col_0,col_1)))
#     assert abs(np.vdot(col_0,col_1)) < 1e-10
#     V = [col_0, col_1]
#
#     rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
#     eng = MainEngine()
#     qureg = eng.allocate_qureg(3)
#     eng.flush() # order
#
#     iso._apply_isometry(V,qureg)
#     eng.flush()
#     order, result = eng.backend.cheat()
#     print(order)
#     iso._print_vec(col_0)
#     iso._print_qureg(qureg)
#     assert np.allclose(result, col_0)
#     Measure | qureg
#     eng.flush()
#
#     eng = MainEngine(engine_list=[AutoReplacer(rule_set), CommandPrinter()])
#     qureg = eng.allocate_qureg(3)
#     eng.flush() # order
#     X | qureg[0]
#     iso._apply_isometry(V,qureg)
#     eng.flush()
#     order, result = eng.backend.cheat()
#     print(order)
#     iso._print_vec(col_1)
#     iso._print_qureg(qureg)
#     assert np.allclose(result, col_1)
#     Measure | qureg
#     eng.flush()
#
#     #assert False
#
#     n = 5
#     for k in range(1<<n):
#         for s in range(n):
#             range_l = list(range(iso.a(k,s+1), 2**(n-1-s)))
#             if range_l:
#                 print("Range(k={},s={}): {}, {}".format(k,s,range_l[0], range_l[-1]))
#             else:
#                 print("Range(k={},s={}): empty".format(k,s))
#             # if s > 0:
#             #     print("MCG {}".format(iso.b(k,s) + (iso.a(k,s) << (s-1))))
#         print("--")

def create_initial_state(mask, qureg):
    n = len(qureg)
    for pos in range(n):
        if ((mask >> pos) & 1) == 1:
            X | qureg[pos]

@pytest.mark.parametrize("index", range(8))
def test_full_unitary_3_qubits(index):
    n = 3
    N = 1<<n
    np.random.seed(42)
    re = np.random.rand(N,N)
    im = np.random.rand(N,N)
    M = re + 1j*im
    U,R = np.linalg.qr(M, mode='reduced')
    V = []
    for i in range(N):
        V.append(U[:,i])

    # must be orthogonal
    for i in range(N):
        for j in range(N):
            if i != j:
                assert abs(np.vdot(U[:,i],U[:,j])) < 1e-14
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    eng = MainEngine(engine_list=[AutoReplacer(rule_set)])
    #eng = MainEngine()
    qureg = eng.allocate_qureg(3)
    eng.flush() # order
    create_initial_state(index, qureg)
    Isometry(V) | qureg
    eng.flush()
    order, result = eng.backend.cheat()
    print(order)
    #iso._print_vec(U[:,index])
    #iso._print_qureg(qureg)
    assert np.allclose(result, U[:,index])
    Measure | qureg
    eng.flush()
