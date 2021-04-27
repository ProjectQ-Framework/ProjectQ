import projectq.libs.math
import projectq.setups.decompositions
from projectq.backends import Simulator, ResourceCounter
from projectq.cengines import (AutoReplacer, DecompositionRuleSet,
                               InstructionFilter, LocalOptimizer,
                               MainEngine, TagRemover)
from projectq.libs.math import (AddConstant, AddConstantModN,
                                MultiplyByConstantModN)
from projectq.meta import Control
from projectq.ops import (All, BasicMathGate, get_inverse, H, Measure, QFT, R,
                          Swap, X, StatePreparation, SparseStatePreparation)
from projectq.meta._control import State
import numpy as np
import math
resource_counter = ResourceCounter()
import time
    # make the compiler and run the circuit on the simulator backend
resource_counter = ResourceCounter()
rule_set = DecompositionRuleSet(modules=[projectq.libs.math,
                                         projectq.setups.decompositions])
compilerengines = [AutoReplacer(rule_set),
                   TagRemover(),
                   LocalOptimizer(3),
                   AutoReplacer(rule_set),
                   TagRemover(),
                   LocalOptimizer(3),
                   resource_counter]
eng = MainEngine(Simulator(),compilerengines,verbose=True)
n = 4
x = eng.allocate_qureg(n)


#X | x[1]
#X | x[1]


#invert = True
state = np.array([ 0,1/math.sqrt(2),0,0,0,0,0,0,0,0,0,0,0,0,1/math.sqrt(2),0])


SparseStatePreparation(state) | x
    #X | x[2]

All(Measure) | x

eng.flush()
print('\n')
print('---------------------RESULTS--------------------------------')
for i in range(n):
    print('X_reg :',int(x[i]))

print(resource_counter)









#