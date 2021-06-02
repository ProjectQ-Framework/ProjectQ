#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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

from projectq.cengines import MainEngine
from projectq.meta import Control
from projectq.ops import All, get_inverse, H, Measure, QFT, R, X, CtrlAll, Swap
from projectq.libs.math import AddConstant
# make the compiler and run the circuit on the simulator backend
from scipy.stats import unitary_group
import numpy as np
eng = MainEngine()
n = 3
x = eng.allocate_qureg(n)

#X | x[0]
#H | x[0]

# invert = True

#H | x[1]
#X | x[0]
#X | x[2]
with Control(eng,x[1],ctrl_state='0'):

 #   Swap | (x[0],x[2])
    #X | x[2]
    X | x[0]
    with Control(eng, x[0]):
        X | x[2]

eng.flush()
print(np.matmul(eng.backend.matout(),[1]+([0]*(2**n-1))))
print(eng.backend.cheat())
All(Measure) | x

print('---------------------')
#y = eng.allocate_qureg(3)

#X | y[0]
#with Control(eng,y[1],ctrl_state='0'):
#   Swap | (y[0],y[2])

#All(Measure) | y
#print(eng.backend.matout())
#eng.flush()

print('\n')
print('---------------------RESULTS--------------------------------')
for i in range(n):
    print('X_reg :', int(x[i]))

#for i in range(2):
 #   print('Y_reg :', int(y[i]))




