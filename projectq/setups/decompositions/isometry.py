from projectq import MainEngine
from projectq.ops import Measure, X, Rz, Isometry, UniformlyControlledGate, DiagonalGate
from projectq.ops._basics import BasicGate
from projectq.meta import Control, Compute, Uncompute, Dagger
from projectq.cengines import DecompositionRule
import projectq.setups.decompositions
from projectq.cengines import InstructionFilter, AutoReplacer, DecompositionRuleSet
from projectq.isometries import _apply_isometry

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
    decomposition = iso.decomposition

    qureg = []
    for reg in cmd.qubits:
        qureg.extend(reg)

    _apply_isometry(decomposition, qureg)


#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(Isometry, _decompose_isometry)
]
