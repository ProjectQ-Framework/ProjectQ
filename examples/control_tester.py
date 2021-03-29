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
                          Swap, X)

import time
    # make the compiler and run the circuit on the simulator backend
eng = MainEngine(verbose=True)
n = 3
m = 3
x = eng.allocate_qureg(n)

ctrl_reg = eng.allocate_qureg(m)
#X | x[1]
#X | x[1]

#X | ctrl_reg[0]
X | ctrl_reg[1]
#X | ctrl_reg[2]

#invert = True
with Control(eng, ctrl_reg, ctrl_state = '010'):
    X | x[0]
    X | x[1]
    #X | x[2]

All(Measure) | x
All(Measure) | ctrl_reg

eng.flush()
print('\n')
print('---------------------RESULTS--------------------------------')
for i in range(n):
    print('X_reg :',int(x[i]))
for j in range(m):
    print('Ctrl :', int(ctrl_reg[j]))













#