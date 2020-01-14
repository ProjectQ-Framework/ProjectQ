#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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
#
#   Module uses ideas from "Basic circuit compilation techniques
#   for an ion-trap quantum machine" by Dmitri Maslov (2017) at
#   https://iopscience.iop.org/article/10.1088/1367-2630/aa5e47
"""
Apply the restricted gate set setup for trapped ion based quantum computers.

It provides the `engine_list` for the `MainEngine`, restricting the gate set to
Rx and Ry single qubit gates and the Rxx two qubit gates.

A decomposition chooser is implemented following the ideas in QUOTE for
reducing the number of Ry gates in the new circuit.

NOTE:

Because the decomposition chooser is only called when a gate has to be
decomposed, this reduction will work better when the entire circuit has to be
decomposed. Otherwise, If the circuit has both superconding gates and native
ion trapped gates the decomposed circuit will not be optimal.
"""

from projectq.setups import restrictedgateset
from projectq.ops import (Rxx, Rx, Ry)
from projectq.meta import get_control_count

# ------------------chooser_Ry_reducer-------------------#
# If the qubit is not in the prev_Ry_sign dictionary, then no decomposition
# occured
# If the value is:
#  -1 then the last gate applied (during a decomposition!) was Ry(-math.pi/2)
#   1 then the last gate applied (during a decomposition!) was Ry(+math.pi/2)
#   0 then the last gate applied (during a decomposition!) was a Rx

prev_Ry_sign = dict()  # Keeps track of most recent Ry sign, i.e.
#                        whether we had Ry(-pi/2) or Ry(pi/2)
#                        prev_Ry_sign[qubit_index] should hold -1 or
#                        +1


def chooser_Ry_reducer(cmd, decomposition_list):
    """
    Choose the decomposition so as to maximise Ry cancellations, based on the
    previous decomposition used for the given qubit.

    Note:
        Classical instructions gates e.g. Flush and Measure are automatically
        allowed.

    Returns:
        A decomposition object from the decomposition_list.
    """
    decomp_rule = dict()
    name = 'default'

    for decomp in decomposition_list:
        try:
            # NB: need to (possibly) raise an exception before setting the
            # name variable below
            decomposition = decomp.decompose.__name__.split('_')
            decomp_rule[decomposition[3]] = decomp
            name = decomposition[2]
            # 'M' stands for minus, 'P' stands for plus 'N' stands for neutral
            # e.g. decomp_rule['M'] will give you the decomposition_rule that
            # ends with a Ry(-pi/2)
        except IndexError:
            pass

    local_prev_Ry_sign = prev_Ry_sign.setdefault(cmd.engine, dict())

    if name == 'cnot2rxx':
        assert get_control_count(cmd) == 1
        ctrl_id = cmd.control_qubits[0].id

        if local_prev_Ry_sign.get(ctrl_id, -1) <= 0:
            # If the previous qubit had Ry(-pi/2) choose the decomposition
            # that starts with Ry(pi/2)
            local_prev_Ry_sign[ctrl_id] = -1
            # Now the prev_Ry_sign is set to -1 since at the end of the
            # decomposition we will have a Ry(-pi/2)
            return decomp_rule['M']

        # Previous qubit had Ry(pi/2) choose decomposition that starts
        # with Ry(-pi/2) and ends with R(pi/2)
        local_prev_Ry_sign[ctrl_id] = 1
        return decomp_rule['P']

    if name == 'h2rx':
        qubit_id = [qb.id for qureg in cmd.qubits for qb in qureg]
        assert len(qubit_id) == 1  # this should be a single qubit gate
        qubit_id = qubit_id[0]

        if local_prev_Ry_sign.get(qubit_id, 0) == 0:
            local_prev_Ry_sign[qubit_id] = 1
            return decomp_rule['M']

        local_prev_Ry_sign[qubit_id] = 0
        return decomp_rule['N']

    if name == 'rz2rx':
        qubit_id = [qb.id for qureg in cmd.qubits for qb in qureg]
        assert len(qubit_id) == 1  # this should be a single qubit gate
        qubit_id = qubit_id[0]

        if local_prev_Ry_sign.get(qubit_id, -1) <= 0:
            local_prev_Ry_sign[qubit_id] = -1
            return decomp_rule['M']

        local_prev_Ry_sign[qubit_id] = 1
        return decomp_rule['P']

    # No decomposition chosen, so use the first decompostion in the list
    # like the default function
    return decomposition_list[0]


def get_engine_list():
    """
    Returns an engine list compiling code into a trapped ion based compiled
    circuit code.

    Note:

        - Classical instructions gates such as e.g. Flush and Measure are
        automatically allowed.
        - The restricted gate set engine does not work with Rxx gates, as
        ProjectQ will by default bounce back and forth between Cz gates and Cx
        gates. An appropriate decomposition chooser needs to be used!

    Returns:
        A list of suitable compiler engines.
    """
    return restrictedgateset.get_engine_list(
        one_qubit_gates=(Rx, Ry),
        two_qubit_gates=(Rxx, ),
        compiler_chooser=chooser_Ry_reducer)
