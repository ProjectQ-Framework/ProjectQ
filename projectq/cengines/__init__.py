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

"""ProjectQ module containing all compiler engines."""

from contextlib import contextmanager

from ._basicmapper import BasicMapperEngine
from ._basics import BasicEngine, ForwarderEngine, LastEngineException
from ._cmdmodifier import CommandModifier

# isort: split

from ._ibm5qubitmapper import IBM5QubitMapper
from ._linearmapper import LinearMapper, return_swap_depth
from ._main import MainEngine, NotYetMeasuredError, UnsupportedEngineError
from ._manualmapper import ManualMapper
from ._optimize import LocalOptimizer
from ._replacer import (
    AutoReplacer,
    DecompositionRule,
    DecompositionRuleSet,
    InstructionFilter,
)
from ._swapandcnotflipper import SwapAndCNOTFlipper
from ._tagremover import TagRemover
from ._testengine import CompareEngine, DummyEngine
from ._twodmapper import GridMapper


@contextmanager
def flushing(engine):
    """
    Context manager to flush the given engine at the end of the 'with' context block.

    Example:
        with flushing(MainEngine()) as eng:
            qubit = eng.allocate_qubit()
            ...

    Calling 'eng.flush()' is no longer needed because the engine will be flushed at the
    end of the 'with' block even if an exception has been raised within that block.
    """
    try:
        yield engine
    finally:
        engine.flush()
