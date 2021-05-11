from projectq.cengines import DecompositionRule
from projectq.meta import Control, get_control_count, Compute, Uncompute\
    , has_negative_control, drop_engine_after
from projectq.ops import BasicGate, X

def _decompose_controlstate(cmd):
    """
    Decompose commands with control qubits in negative state (ie. control
    qubits with state '0' instead of '1')
    """
    with Compute(cmd.engine):

        for state, ctrl in zip(cmd.ctrl_state, cmd.control_qubits):
            if state == '0':
                X | ctrl

    # Resend the command with the `ctrl_state` cleared
    cmd.ctrl_state = '1' * len(cmd.ctrl_state)
    orig_engine = cmd.engine
    cmd.engine.receive([cmd])
    Uncompute(orig_engine)

def _recognize_offctrl(cmd):
    return has_negative_control(cmd) == 1

#: Decomposition rules
all_defined_decomposition_rules = [
    DecompositionRule(BasicGate, _decompose_controlstate, _recognize_offctrl)
]