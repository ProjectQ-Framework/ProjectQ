from projectq import MainEngine
from projectq.ops import Measure, X, Rz, Isometry, UniformlyControlledGate, DiagonalGate
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute, Dagger
from projectq.cengines import DecompositionRule
import projectq.setups.decompositions
from projectq.cengines import InstructionFilter, AutoReplacer, DecompositionRuleSet
from projectq.isometries import _apply_isometry
from projectq.isometries import _DecomposeIsometry

import numpy as np
import math
import cmath
import copy
import random

def _print_qureg(qureg):
    eng = qureg.engine
    eng.flush()
    bla, vec = eng.backend.cheat()
    for i in range(len(vec)):
        print("{}: {:.3f}, {}".format(i,abs(vec[i]), cmath.phase(vec[i])))
    print("-")

def _print_vec(vec):
    for i in range(len(vec)):
        print("{}: {:.3f}, {}".format(i,abs(vec[i]), cmath.phase(vec[i])))
    print("-")

def _decompose_isometry(cmd):
    iso = cmd.gate
    if not iso.decomposed:
        iso.decompose()
    decomposition = iso.decomposition

    qureg = []
    for reg in cmd.qubits:
        qureg.extend(reg)

    _apply_isometry(decomposition, qureg)

# def _apply_mask(mask, qureg):
#     n = len(qureg)
#     for pos in range(n):
#         if ((mask >> pos) & 1) == 0:
#             X | qureg[pos]
#
# def _decompose_isometry(cmd):
#     qureg = []
#     for reg in cmd.qubits:
#         qureg.extend(reg)
#     cols = cmd.gate.cols
#     decomposition = _DecomposeIsometry(cols).get_decomposition()
#     reductions, phases = decomposition
#     n = len(qureg)
#     with Dagger(qureg[0].engine):
#         for k in range(len(reductions)):
#             for s in range(n):
#                 mcg, ucg = reductions[k][s]
#                 # apply MCG
#                 mask = b(k,s) + (a(k,s+1) << s)
#                 qubits = qureg[:s]+qureg[s+1:]
#                 e = qureg[0].engine
#                 with Compute(e):
#                     _apply_mask(mask,qubits)
#                 with Control(e, qubits):
#                     mcg | qureg[s]
#                 Uncompute(e)
#                 #apply UCG
#                 if len(ucg) > 0:
#                     UCG = UniformlyControlledGate(ucg, up_to_diagonal=True)
#                     UCG | (qureg[s+1:], qureg[s])
#         diagonal = DiagonalGate(phases=phases)
#         diagonal | qureg
#
# def a(k,s):
#     return k >> s
#
# def b(k,s):
#     return k - (a(k,s) << s)


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(Isometry, _decompose_isometry)
]
