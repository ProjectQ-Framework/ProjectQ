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
from projectq.cengines import IBMCNOTMapper


def test_ibm_cnot_mapper_in_cengines():
    import projectq.setups.ibm
    found = False
    for engine in projectq.setups.ibm.ibm_default_engines():
        if isinstance(engine, IBMCNOTMapper):
            found = True
    # To undo the changes of loading the IBM setup:
    import projectq.setups.default
    projectq.default_engines = projectq.setups.default.default_engines
    assert found
