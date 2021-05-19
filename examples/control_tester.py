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
from projectq.ops import All, get_inverse, H, Measure, QFT, R, X, CtrlAll

# make the compiler and run the circuit on the simulator backend

eng = MainEngine()
n = 3
m = 3
x = eng.allocate_qureg(n)

ctrl_reg = eng.allocate_qureg(m)
# X | x[1]
# X | x[1]

X | ctrl_reg[0]
# X | ctrl_reg[1]
X | ctrl_reg[2]
# invert = True
with Control(eng, ctrl_reg[1], ctrl_state='0'):
    with Control(eng, ctrl_reg[0], ctrl_state='1'):
        with Control(eng, ctrl_reg[0], ctrl_state='1'):
            X | x[0]
            X | x[1]
    # X | x[2]

All(Measure) | x
All(Measure) | ctrl_reg

eng.flush()
print('\n')
print('---------------------RESULTS--------------------------------')
for i in range(n):
    print('X_reg :', int(x[i]))
for j in range(m):
    print('Ctrl :', int(ctrl_reg[j]))
