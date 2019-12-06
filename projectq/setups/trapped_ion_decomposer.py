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

"""
Apply the restricted gate set setup for trapped ion based quantum computers.

It provides the `engine_list` for the `MainEngine`, restricting the gate set to
Rx and Ry single qubit gates and the Rxx two qubit gates.

A decomposition chooser is implemented following the ideas in QUOTE for reducing the
number of Ry gates in the new circuit. 
NOTE: Because the decomposition chooser is only called when a gate has to be decomposed,
This reduction will work better when the entire circuit has to be decomposed. Otherwise,
If the circuit has both superconding gates and native ion trapped gates the decomposed
circuit will not be optimal.  
"""

import inspect

import projectq
import projectq.libs.math
from projectq.setups import restrictedgateset
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               InstructionFilter, LocalOptimizer,
                               TagRemover)
from projectq.ops import (Rxx,Rx,Ry)

#List of qubits and the last decomposition used on them
# If the qubit is not on the dictionary, then no decomposition occured
# If the value is -1 then the last gate applied (during a decomposition!) was Ry(-math.pi/2)
# If the value is 1 then the last gate applied (during a decomposition!) was Ry(math.pi/2)
# If the value is 0 then the last gate applied (during a decomposition!) was a Rx
liste=dict()

def chooser_Ry_reducer(cmd,decomposition_list):
    """
    choose the decomposition to apply based on the previous decomposition used for the given qubit.

    Note:
        Classical instructions gates such as e.g. Flush and Measure are
        automatically allowed.

    Returns:
        a decomposition object from the decomposition_list
    """
    provisory_liste=dict() #Dictionary to evaluate available decomposition as well as the gate that needs to be decomposed
    name='default'
    
    for el in decomposition_list:
        try:
            decomposition=el.decompose.__name__.split('_')
            name=decomposition[2]
            provisory_liste[decomposition[3]]=el
        except:
            pass
    if name=='cnot2rxx': 
        ctrl = cmd.control_qubits
        idx=str(ctrl)
        if idx in liste:
            if liste[idx]<=0:
                liste[idx]=-1
                return provisory_liste['M']
            else:
                liste[idx]=1
                return provisory_liste['P']
        else:
            liste[idx]=-1
            return provisory_liste['M']
    elif name=='h2rx':
        qubit = cmd.qubits[0]
        idx=str(qubit)
        if idx not in liste:
            liste[idx]=+1
            return provisory_liste['M']
        elif liste[idx]==0:
            liste[idx]=+1
            return provisory_liste['M']
        else:
            liste[idx]=00
            return provisory_liste['N']
    elif name=='rz2rx':
        qubit = cmd.qubits[0]
        idx=str(qubit)
        if idx not in liste:
            liste[idx]=-1
            return provisory_liste['M']
        elif liste[idx]<=0:
            liste[idx]=-1
            return provisory_liste['M']
        else:
            liste[idx]=1
            return provisory_liste['P']
    else: #Nothing worked, so decompose the first decompostion function like the default function
        return decomposition_list[0]



def get_engine_list():
    """
    Returns an engine list compiling code into a trapped ion based compiled circuit code.

    Note:
        -Classical instructions gates such as e.g. Flush and Measure are
        automatically allowed.
        -The restricted gate set engine does not work with Rxx gates, as ProjectQ will by default bounce back and forth between Cz gates and Cx gates. An appropriate decomposition chooser needs to be used!

    Returns:
        A list of suitable compiler engines.
    """
    return restrictedgateset.get_engine_list(one_qubit_gates=(Rx,Ry),two_qubit_gates=(Rxx,),compiler_chooser=chooser_Ry_reducer)




 
