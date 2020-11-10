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

from projectq.ops import All, Measure, ControlledGate, SwapGate

from qiskit.circuit import QuantumCircuit, ClassicalRegister, Clbit

from ._qiskit_conv import gates_conv_table

# ==============================================================================


def apply_gate(gate, qubits):
    """
    Apply a gate to some qubits while separating control and target qubits.


    Args:
        gate (BasicGate): Instance of a ProjectQ gate
        qubits (list): List of ProjectQ qubits the gate applies to.
    """
    if isinstance(gate, ControlledGate):
        ctrls = qubits[:gate._n]
        qubits = qubits[gate._n:]
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
                    for bit in bits_map[cbit.name]:
                        cbit_value = (cbit_value << 1) | bit

                if cbit_value == value:
                    apply_gate(gate_projectq, qubits)
            else:
                apply_gate(gate_projectq, qubits)


def _convert_qiskit_circuit(eng, qc):
    """
    Convert a QisKit circuit and convert it to ProjectQ commands.

    This function supports OpenQASM 2.0 (3.0 is experimental)

    Args:
        eng (MainEngine): MainEngine to use for creating qubits and commands.
        qc (qiskit.QuantumCircuit): Quantum circuit to process

    Note:
        At this time, we support most of OpenQASM 2.0 and some of 3.0,
        although the latter is still experimental.
    """
    # Create maps between qiskit and ProjectQ for qubits and bits
    qubits_map = {
        qureg.name: eng.allocate_qureg(qureg.size)
        for qureg in qc.qregs
    }
    bits_map = {bit.name: [False] * bit.size for bit in qc.cregs}

    # Convert all the gates to ProjectQ commands
    for gate, quregs, bits in qc.data:
        apply_op(
            eng, gate,
            [qubits_map[qubit.register.name][qubit.index]
             for qubit in quregs], bits, bits_map)

    return qubits_map, bits_map


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
    qc = QuantumCircuit.from_qasm_str(qasm_str)
    return _convert_qiskit_circuit(eng, qc)


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

    qc = QuantumCircuit.from_qasm_file(filename)

    return _convert_qiskit_circuit(eng, qc)
