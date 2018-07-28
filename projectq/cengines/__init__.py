#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
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

from ._basics import (BasicEngine,
                      LastEngineException,
                      ForwarderEngine)
from ._cmdmodifier import CommandModifier
from ._basicmapper import BasicMapperEngine
from ._ibm5qubitmapper import IBM5QubitMapper
from ._swapandcnotflipper import SwapAndCNOTFlipper
from ._linearmapper import LinearMapper, return_swap_depth
from ._manualmapper import ManualMapper
from ._main import (MainEngine,
                    NotYetMeasuredError,
                    UnsupportedEngineError)
from ._optimize import LocalOptimizer
from ._replacer import (AutoReplacer,
                        InstructionFilter,
                        DecompositionRuleSet,
                        DecompositionRule)
from ._tagremover import TagRemover
from ._testengine import CompareEngine, DummyEngine
from ._twodmapper import GridMapper
