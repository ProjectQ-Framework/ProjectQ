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
"""Tests for projectq.setup.ibm16."""

import projectq
from projectq.cengines import ManualMapper


def test_manual_mapper_in_cengines():
    import projectq.setups.ibm16
    found = False
    for engine in projectq.setups.ibm16.ibm16_default_engines():
        if isinstance(engine, ManualMapper):
            found = True

    # To undo the changes of loading the IBM setup:
    import projectq.setups.default
    projectq.default_engines = projectq.setups.default.default_engines

    assert found
