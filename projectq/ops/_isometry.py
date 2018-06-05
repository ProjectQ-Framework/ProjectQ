from ._basics import BasicGate


import copy
import numpy as np



class Isometry(BasicGate):
    """
    A gate that represents arbitrary isometries.

    Example:
        .. code-block:: python
            col_0 = [1j, -1j]
            col_1 = ...
            V = Isometry([col_0 col_1])
            V | qureg

    """
    def __init__(self, cols):
        self.cols = copy.deepcopy(cols)
        self.interchangeable_qubit_indices = []
        self._decomposition = None
        n = int(np.log2(len(cols[0])))
        #print("n={} th={}".format(n,_get_ucg_mcg_threshold(n)))
        self._threshold = _get_ucg_mcg_threshold(n)

    @property
    def decomposition(self):
        if self._decomposition == None:
            from projectq.isometries import _decompose_isometry
            self._decomposition = _decompose_isometry(self.cols, self._threshold)
        return self._decomposition

    def __str__(self):
        return "V"


def _my_is_available(cmd):
    from projectq.ops import (Command, X, Y, Z, T, H, Tdag, S, Sdag, Measure,
                              Allocate, Deallocate, NOT, Rx, Ry, Rz, Barrier,
                              Entangle)
    from projectq.meta import Control, Compute, Uncompute, get_control_count

    g = cmd.gate
    if g == NOT and get_control_count(cmd) <= 1:
        return True
    if get_control_count(cmd) == 0:
        if g in (T, Tdag, S, Sdag, H, Y, Z):
            return True
        if isinstance(g, (Rx, Ry, Rz)):
            return True
    if g in (Measure, Allocate, Deallocate, Barrier):
        return True
    return False

def _count_cnot_in_mcg(n):
    from projectq import MainEngine
    from projectq.ops import C, Z, H
    from projectq.backends import ResourceCounter
    from projectq.cengines import AutoReplacer, DecompositionRuleSet, DummyEngine, BasicEngine
    import projectq.setups.decompositions

    resource_counter = ResourceCounter()
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    engines = [AutoReplacer(rule_set), resource_counter]
    backend = DummyEngine()
    backend.is_available = _my_is_available;
    eng = MainEngine(backend, engines)
    qureg = eng.allocate_qureg(n+1)
    C(H,n) | (qureg[1:], qureg[0])
    for item in str(resource_counter).split("\n"):
        if "CX : " in item:
            return int(item.strip()[5:])
    return 0

def _get_ucg_mcg_threshold(n):
    for ctrl in range(2,n):
        if (1<<ctrl)-1 > _count_cnot_in_mcg(ctrl):
            return ctrl
    return n
