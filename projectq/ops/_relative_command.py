from projectq.ops._metagates import ControlledGate

class RelativeCommand(object):
    """ 
    Class:
        Used to represent commands when there is no engine.
        i.e. in the definition of a relative commutable_circuit 
        within a gate class. 

    Attributes:
        gate: The gate class.
        _gate: If RelativeCommand.gate = ControlledGate, _gate will
        return the gate class on the target qubit. 
        e.g. if relative_command.gate = CNOT 
        (class = projectq.ops._metagates.ControlledGate)
        relative_command._gate = NOT
        (class = projectq.ops._gates.XGate)
        relative_qubit_idcs: Tuple of integers, representing the
        relative qubit idcs in a commutable_circuit.
        relative_ctrl_idcs: Tuple of integers, representing the 
        relative control qubit idcs in a commutable_circuit.
    """
    def __init__(self, gate, relative_qubit_idcs, relative_ctrl_idcs=()):
        self.gate = gate
        self.relative_qubit_idcs = relative_qubit_idcs
        self.relative_ctrl_idcs = relative_ctrl_idcs
        self._gate = gate
        if (self.gate.__class__ == ControlledGate):
            self._gate = self.gate._gate

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
        if other is None:
            return False
        if (self.gate.__class__ != other.gate.__class__):
            return False
        if (self.relative_qubit_idcs != other.relative_qubit_idcs):
            return False
        if (self.relative_ctrl_idcs != other.relative_ctrl_idcs):
            return False
        if (self._gate.__class__ != self._gate.__class__):
            return False
        else:
           return True
