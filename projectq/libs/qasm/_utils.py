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

"""Some helper utilities."""

from projectq.ops import BasicGate, ControlledGate, SwapGate

# ==============================================================================


class OpaqueGate(BasicGate):
    """Gate representing an opaque gate type."""

    def __init__(self, name, params):
        """
        Initialize an OpaqueGate object.

        Args:
            name (str): Name/type of the quantum gate
            params (list,tuple): Parameter for the gate (may be empty)
        """
        super().__init__()
        self.name = name
        self.params = params

    def __str__(self):
        """Return the string representation of an OpaqueGate."""
        # TODO: This is a bit crude...
        if self.params:
            return f'Opaque({self.name})({",".join(self.params)})'
        return f'Opaque({self.name})'


# ==============================================================================


def apply_gate(gate, qubits):
    """
    Apply a gate to some qubits while separating control and target qubits.

    Args:
        gate (BasicGate): Instance of a ProjectQ gate
        qubits (list): List of ProjectQ qubits the gate applies to.
    """
    # pylint: disable = protected-access

    if isinstance(gate, ControlledGate):
        ctrls = qubits[: gate._n]
        qubits = qubits[gate._n :]  # noqa: E203
        if isinstance(gate._gate, SwapGate):
            assert len(qubits) == 2
            gate | (ctrls, qubits[0], qubits[1])
        else:
            gate | (ctrls, qubits)
    elif isinstance(gate, SwapGate):
        assert len(qubits) == 2
        gate | (qubits[0], qubits[1])
    else:
        gate | qubits


# ==============================================================================
