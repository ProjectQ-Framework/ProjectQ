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
    engines_5qb=projectq.setups.ibm.get_engine_list(device='ibmq_burlington')
    engines_15qb=projectq.setups.ibm.get_engine_list(device='ibmq_16_melbourne')
    engines_simulator=projectq.setups.ibm.get_engine_list(device='ibmq_qasm_simulator')
    assert len(engines_5qb)==15
    assert len(engines_15qb)==16
    assert len(engines_simulator)==13

