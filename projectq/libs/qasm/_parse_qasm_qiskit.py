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
""" Define function to read OpenQASM file format (using Qiskit). """

from projectq.ops import All, Measure

from qiskit.circuit import QuantumCircuit, Clbit

from ._qiskit_conv import gates_conv_table
from ._utils import apply_gate

# ==============================================================================


def apply_op(eng, gate, qubits, bits, bits_map):
    """
    Apply a qiskit operation.

    This function takes care of converting between qiskit gates and ProjectQ
    gates, as well as handling the translation between qiskit's and ProjectQ's
    qubit and bits.

    Args:
        eng (MainEngine): MainEngine to use to the operation(s)
        gate (qiskit.Gate): Qiskit gate to apply
        qubits (list): List of ProjectQ qubits to apply the gate to
        bits (list): List of classical bits to apply the gate to
    """
    # pylint: disable = expression-not-assigned, protected-access

    if bits:
        # Only measurement gates have clasical bits
        assert len(qubits) == len(bits)
        All(Measure) | qubits
        eng.flush()

        for idx, bit in enumerate(bits):
            assert isinstance(bit, Clbit)
            bits_map[bit.register.name][bit.index] = bool(qubits[idx])
    else:
        if gate.name not in gates_conv_table:
            if not gate._definition:
                # TODO: This will silently discard opaque gates...
                return

            gate_args = {gate._definition.qregs[0].name: qubits}

            for gate_sub, quregs_sub, bits_sub in gate._definition.data:
                # OpenQASM 2.0 limitation...
                assert gate.name != 'measure' and not bits_sub
                apply_op(eng, gate_sub, [
                    gate_args[qubit.register.name][qubit.index]
                    for qubit in quregs_sub
                ], [], bits_map)
        else:
            if gate.params:
                gate_projectq = gates_conv_table[gate.name](*gate.params)
            else:
                gate_projectq = gates_conv_table[gate.name]

            if gate.condition:
                # OpenQASM 2.0
                cbit, value = gate.condition

                if cbit.size == 1:
                    cbit_value = bits_map[cbit.name][0]
                else:
                    cbit_value = 0
                    for bit in reversed(bits_map[cbit.name]):
                        cbit_value = (cbit_value << 1) | bit

                if cbit_value == value:
                    apply_gate(gate_projectq, qubits)
            else:
                apply_gate(gate_projectq, qubits)


# ==============================================================================


def _convert_qiskit_circuit(eng, circuit):
    """
    Convert a QisKit circuit and convert it to ProjectQ commands.

    This function supports OpenQASM 2.0 (3.0 is experimental)

    Args:
        eng (MainEngine): MainEngine to use for creating qubits and commands.
        circuit (qiskit.QuantumCircuit): Quantum circuit to process

    Note:
        At this time, we support most of OpenQASM 2.0 and some of 3.0,
        although the latter is still experimental.
    """
    # Create maps between qiskit and ProjectQ for qubits and bits
    qubits_map = {
        qureg.name: eng.allocate_qureg(qureg.size)
        for qureg in circuit.qregs
    }
    bits_map = {bit.name: [False] * bit.size for bit in circuit.cregs}

    # Convert all the gates to ProjectQ commands
    for gate, quregs, bits in circuit.data:
        apply_op(
            eng, gate,
            [qubits_map[qubit.register.name][qubit.index]
             for qubit in quregs], bits, bits_map)

    return qubits_map, bits_map


# ==============================================================================


def read_qasm_str(eng, qasm_str):
    """
    Read an OpenQASM (2.0, 3.0 is experimental) string and convert it to
    ProjectQ commands.

    This version of the function uses Qiskit in order to parse the *.qasm
    file.

    Args:
        eng (MainEngine): MainEngine to use for creating qubits and commands.
        filename (string): Path to *.qasm file

    Note:
        At this time, we support most of OpenQASM 2.0 and some of 3.0,
        although the latter is still experimental.
    """
    circuit = QuantumCircuit.from_qasm_str(qasm_str)
    return _convert_qiskit_circuit(eng, circuit)


# ------------------------------------------------------------------------------


def read_qasm_file(eng, filename):
    """
    Read an OpenQASM (2.0, 3.0 is experimental) file and convert it to
    ProjectQ commands.

    This version of the function uses Qiskit in order to parse the *.qasm
    file.

    Args:
        eng (MainEngine): MainEngine to use for creating qubits and commands.
        filename (string): Path to *.qasm file

    Note:
        At this time, we support most of OpenQASM 2.0 and some of 3.0,
        although the latter is still experimental.
    """

    circuit = QuantumCircuit.from_qasm_file(filename)

    return _convert_qiskit_circuit(eng, circuit)


# ==============================================================================
