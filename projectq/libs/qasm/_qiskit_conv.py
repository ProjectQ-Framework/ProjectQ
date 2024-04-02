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

"""Definition of helper variables for the Qiskit conversion functions."""

from projectq.ops import (
    CNOT,
    U2,
    U3,
    Barrier,
    C,
    HGate,
    Rx,
    Ry,
    Rz,
    Sdagger,
    SGate,
    SwapGate,
    Tdagger,
    TGate,
    Toffoli,
    XGate,
    YGate,
    ZGate,
)

# ==============================================================================
# Conversion map between Qiskit gate names and ProjectQ gates

gates_conv_table = {
    'barrier': lambda: Barrier,
    'h': HGate,
    's': SGate,
    'sdg': lambda: Sdagger,
    't': TGate,
    'tdg': lambda: Tdagger,
    'x': XGate,
    'y': YGate,
    'z': ZGate,
    'swap': SwapGate,
    'rx': Rx,
    'ry': Ry,
    'rz': Rz,
    'u1': Rz,
    'u2': U2,
    'u3': U3,
    'phase': Rz,
    # Controlled gates
    'ch': lambda: C(HGate()),
    'cx': lambda: CNOT,
    'cy': lambda: C(YGate()),
    'cz': lambda: C(ZGate()),
    'cswap': lambda: C(SwapGate()),
    'crz': lambda a: C(Rz(a)),
    'cu1': lambda a: C(Rz(a)),
    'cu2': lambda phi, lamda: C(U2(phi, lamda)),
    'cu3': lambda theta, phi, lamda: C(U3(theta, phi, lamda)),
    # Doubly-controlled gates
    "ccx": lambda: Toffoli,
}
