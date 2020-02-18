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

'''
    Tests for projectq.backends._circuits._drawer.py.

    To generate the baseline images
    run the tests with '--mpl-generate-path=baseline'

    Then run the tests simply with '--mpl'
'''

import pytest
from projectq import MainEngine
from projectq.ops import *
from projectq.backends import Simulator
from projectq.backends import CircuitDrawerMatplotlib
from projectq.cengines import DecompositionRuleSet, AutoReplacer
import projectq.setups.decompositions

@pytest.mark.mpl_image_compare
def test_drawer_mpl():
    drawer = CircuitDrawerMatplotlib()
    rule_set = DecompositionRuleSet(modules=[projectq.setups.decompositions])
    eng = MainEngine(backend=Simulator(), engine_list=[AutoReplacer(rule_set),
                                                       drawer])
    ctrl = eng.allocate_qureg(2)
    qureg = eng.allocate_qureg(3)

    Swap | (qureg[0], qureg[2])
    C(Swap) | (qureg[0], qureg[1], qureg[2])

    CNOT | (qureg[0], qureg[2])
    Rx(1.0) | qureg[0]
    CNOT | (qureg[1], qureg[2])
    C(X, 2) | (ctrl[0], ctrl[1], qureg[2])
    QFT | qureg
    All(Measure) | qureg

    eng.flush()
    fig, ax = drawer.draw()
    return fig