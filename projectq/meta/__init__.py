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
The projectq.meta package features meta instructions which help both the user
and the compiler in writing/producing efficient code. It includes, e.g.,

* Loop (with Loop(eng): ...)
* Compute/Uncompute (with Compute(eng): ..., [...], Uncompute(eng))
* Control (with Control(eng, ctrl_qubits): ...)
* Dagger (with Dagger(eng): ...)
"""


from ._dirtyqubit import DirtyQubitTag
from ._loop import (LoopTag,
                    Loop)
from ._compute import (Compute,
                       Uncompute,
                       CustomUncompute,
                       ComputeTag,
                       UncomputeTag)
from ._control import (Control,
                       get_control_count)
from ._dagger import Dagger
