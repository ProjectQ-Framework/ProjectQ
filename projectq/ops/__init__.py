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

from ._basics import (NotMergeable,
                      NotInvertible,
                      BasicGate,
                      SelfInverseGate,
                      BasicRotationGate,
                      ClassicalInstructionGate,
                      FastForwardingGate,
                      BasicMathGate)
from ._command import apply_command, Command
from ._metagates import (DaggeredGate,
                         get_inverse,
                         ControlledGate,
                         C,
                         Tensor,
                         All)
from ._gates import *
from ._qftgate import QFT
from ._shortcuts import *
