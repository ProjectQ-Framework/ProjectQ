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
Defines a setup to compile to a restricted gate set.

It provides the `engine_list` for the `MainEngine`. This engine list contains
an AutoReplacer with most of the gate decompositions of ProjectQ, which are
used to decompose a circuit into a restricted gate set (with some limitions
on the choice of gates).
"""

import inspect

import projectq
import projectq.libs.math
from projectq.setups import restrictedgateset
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               InstructionFilter, LocalOptimizer,
                               TagRemover)
from projectq.ops import (Rxx,Rx,Ry)

liste=dict()

def chooser_Ry_reducer(cmd,decomposition_list):
    provisory_liste=dict()
    name='default'
    try:
        for el in decomposition_list:
            decomposition=el.decompose.__name__.split('_')
            name=decomposition[2]
            provisory_liste[decomposition[3]]=el
    except:
        return decomposition_list[0]
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
    elif name=='h':
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
    elif name=='rz':
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
    else:
        return decomposition_list[0]



def get_engine_list():
    """
    Returns an engine list compiling code into a trapped ion based compiled circuit code.

    Note:
        Classical instructions gates such as e.g. Flush and Measure are
        automatically allowed.

    Returns:
        A list of suitable compiler engines.
    """
    return restrictedgateset.get_engine_list(one_qubit_gates=(Rx,Ry),two_qubit_gates=(Rxx,),compiler_chooser=chooser_Ry_reducer)




 
