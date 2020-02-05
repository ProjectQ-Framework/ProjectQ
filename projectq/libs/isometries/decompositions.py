import numpy as np
from projectq.libs.isometries.single_qubit_gate import _SingleQubitGate


def _wrap(gates):
    return [_SingleQubitGate(np.matrix(gate)) for gate in gates]


def _unwrap(gates):
    return [gate.matrix.tolist() for gate in gates]


try:
    import projectq.libs.isometries.cppdec as cppdec
    _DecomposeDiagonal = cppdec._DecomposeDiagonal

    class _DecomposeUCG(object):
        def __init__(self, wrapped_gates):
            self._backend = cppdec._BackendDecomposeUCG(_unwrap(wrapped_gates))

        def get_decomposition(self):
            unwrapped_gates, phases = self._backend.get_decomposition()
            return _wrap(unwrapped_gates), phases

    class _DecomposeIsometry(object):
        def __init__(self, V, threshold):
            self._backend = cppdec._BackendDecomposeIsometry(V, threshold)

        def get_decomposition(self):
            reductions, diagonal_decomposition = \
                self._backend.get_decomposition()
            for k in range(len(reductions)):
                for s in range(len(reductions[k])):
                    (mcg, phases1), (ucg, phases2) = reductions[k][s]
                    reductions[k][s] = (_wrap(mcg), phases1), (_wrap(ucg),
                                                               phases2)
            return reductions, diagonal_decomposition

except ImportError:  # pragma: no cover
    from .decompose_diagonal import _DecomposeDiagonal
    from .decompose_ucg import _DecomposeUCG
    from .decompose_isometry import _DecomposeIsometry


def _decompose_diagonal_gate(phases):
    return _DecomposeDiagonal(phases).get_decomposition()


def _decompose_uniformly_controlled_gate(gates):
    return _DecomposeUCG(gates).get_decomposition()


def _decompose_isometry(columns, threshold):
    return _DecomposeIsometry(columns, threshold).get_decomposition()
