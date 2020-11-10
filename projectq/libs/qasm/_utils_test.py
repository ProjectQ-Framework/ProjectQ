#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Tests for projectq.libs.qasm._utils.py."""

import pytest

from projectq.types import WeakQubitRef
from projectq.cengines import DummyEngine
from projectq.ops import (X, Y, Z, T, Tdagger, S, Sdagger, H, Ph, R, Rx, Ry, Rz,
                          U2, U3, Swap, Toffoli, Barrier, C)
from ._utils import apply_gate, OpaqueGate

# ==============================================================================


def test_opaque_gate():
    gate = OpaqueGate('my_gate', None)
    assert gate.name == 'my_gate'
    assert not gate.params
    assert str(gate) == 'Opaque(my_gate)'

    gate = OpaqueGate('my_gate', ('lambda', 'alpha'))
    assert gate.name == 'my_gate'
    assert gate.params == ('lambda', 'alpha')

    assert str(gate) == 'Opaque(my_gate)(lambda,alpha)'


# ==============================================================================


@pytest.mark.parametrize(
    'gate, n_qubits', (list(
        map(lambda x:
            (x, 1), [
                X, Y, Z, S, Sdagger, T, Tdagger, H, Barrier,
                Ph(1.12),
                Rx(1.12),
                Ry(1.12),
                Rz(1.12),
                R(1.12),
                U2(1.12, 1.12),
                U3(1.12, 1.12, 1.12),
            ])) + list(map(lambda x:
                           (x, 2), [C(X), C(Y), C(Z), Swap, Barrier])) +
                       list(map(lambda x:
                                (x, 3), [Toffoli, C(Swap), Barrier])) +
                       list(map(lambda x: (x, 10), [Barrier]))),
    ids=str)
def test_apply_gate(gate, n_qubits):
    backend = DummyEngine()
    backend.is_last_engine = True

    gate.engine = backend
    qubits = [WeakQubitRef(backend, idx) for idx in range(n_qubits)]

    apply_gate(gate, qubits)
