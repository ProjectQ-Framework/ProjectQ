#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
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
"""
This file defines the RelativeCommand class.

RelativeCommand should be used to represent a Command
when there is no main_engine, for example within Gate 
definitions. Using RelativeCommand we can define 
commutable_circuits for a particular gate. 

Example:

.. code-block:: python

    class Rz(BasicRotationGate):

        def __init__(self, angle):
            BasicRotationGate.__init__(self, angle)
            self._commutable_gates = [Rzz,]
            self._commutable_circuit_list = [[RelativeCommand(H,(0,)), 
                RelativeCommand(C(NOT),(0,), relative_ctrl_idcs=(1,)), 
                RelativeCommand(H,(0,))],]

The _commutable_circuit_list has been defined using RelativeCommand
objects. The is_commutable function defined in the Command class looks
for _commutable_circuits in the definition of its' gate. Then we can 
check if there might be a commutable circuit coming after a Command. 
This is used in the _check_for_commutable_circuit function and in the
LocalOptimizer in _optimize.py

    cmd1 = _command.Command(main_engine, Rz(0.2), (qubit1,))
    cmd2 = _command.Command(main_engine, H, (qubit1,))
    if (cmd1.is_commutable(cmd2) == 2): 
        # Check for a commutable circuit

Rz has a commutable circuit which starts with H. If is_commutable returns '2' 
it indicates that the next command may be the start of a commutable circuit.  

"""

from projectq.ops._metagates import ControlledGate

class RelativeCommand(object):
    """ Alternative representation of a Command.

    Class:
        Used to represent commands when there is no engine.
        i.e. in the definition of a relative commutable_circuit 
        within a gate class. 

    Attributes:
        gate: The gate class.
        _gate: The true gate class if gate is a metagate.
        relative_qubit_idcs: Tuple of integers, representing the
            relative qubit idcs in a commutable_circuit.
        relative_ctrl_idcs: Tuple of integers, representing the 
            relative control qubit idcs in a commutable_circuit.
    """
    def __init__(self, gate, relative_qubit_idcs, relative_ctrl_idcs=()):
        self.gate = gate
        self.relative_qubit_idcs = relative_qubit_idcs
        self.relative_ctrl_idcs = relative_ctrl_idcs
        self._gate = self.gate._gate if isinstance(self.gate, ControlledGate) else gate

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        return self.equals(other)

    def to_string(self, symbols=False):
        """
        Get string representation of this Command object.
        """
        print('i should not exist')
        qubits = self.relative_qubit_idcs
        ctrlqubits = self.relative_ctrl_idcs
        if len(ctrlqubits) > 0:
            qubits = (self.relative_ctrl_idcs, ) + qubits
        qstring = ""
        if len(qubits) == 1:
            qstring = str(qubits)
        else:
            qstring = "( "
            for qreg in range(len(qubits)):
                qstring += str(qubits[qreg])
                qstring += ", "
            qstring = qstring[:-2] + " )"
        return self.gate.to_string(symbols) + " | " + qstring

    def equals(self, other):
        if ((type(self.gate) is type(other.gate)) 
            and (self.relative_qubit_idcs == other.relative_qubit_idcs)
            and (self.relative_ctrl_idcs == other.relative_ctrl_idcs)
            and (type(self._gate) is type(self._gate))):
            return True
        else:
           return False
