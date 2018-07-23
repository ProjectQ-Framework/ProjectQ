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
"""Tests for projectq.setup.ibm."""

import projectq
from projectq import MainEngine
from projectq.cengines import IBM5QubitMapper, SwapAndCNOTFlipper


def test_ibm_cnot_mapper_in_cengines():
    import projectq.setups.ibm
    found = 0
    for engine in projectq.setups.ibm.get_engine_list():
        if isinstance(engine, IBM5QubitMapper):
            found |= 1
        if isinstance(engine, SwapAndCNOTFlipper):
            found |= 2
    assert found == 3
