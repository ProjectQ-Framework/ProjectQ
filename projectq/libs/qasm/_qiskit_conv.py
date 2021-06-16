# -*- coding: utf-8 -*-
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
from projectq.ops import Barrier, H, S, Sdagger, T, Tdagger, X, Y, Z, Rx, Ry, Rz, Swap, Toffoli, C, CNOT, U2, U3

# ==============================================================================
# Conversion map between Qiskit gate names and ProjectQ gates

gates_conv_table = {
    'barrier': Barrier,
    'h': H,
    's': S,
    'sdg': Sdagger,
    't': T,
    'tdg': Tdagger,
    'x': X,
    'y': Y,
    'z': Z,
    'swap': Swap,
    'rx': lambda a: Rx(a),
    'ry': lambda a: Ry(a),
    'rz': lambda a: Rz(a),
    'u1': lambda a: Rz(a),
    'u2': lambda p, l: U2(p, l),
    'u3': lambda t, p, l: U3(t, p, l),
    'phase': lambda a: Rz(a),
    # Controlled gates
    'ch': C(H),
    'cx': CNOT,
    'cy': C(Y),
    'cz': C(Z),
    'cswap': C(Swap),
    'crz': lambda a: C(Rz(a)),
    'cu1': lambda a: C(Rz(a)),
    'cu2': lambda p, l: C(U2(p, l)),
    'cu3': lambda t, p, l: C(U3(t, p, l)),
    # Doubly-controlled gates
    "ccx": Toffoli,
}
