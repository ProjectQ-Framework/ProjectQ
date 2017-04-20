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

"""Tests for projectq.meta._qubitplacement.py"""

from projectq.meta import ComputeTag

from projectq.meta._qubitplacement import QubitPlacementTag


def test_qubit_placement_tag():
    tag0 = QubitPlacementTag(0)
    tag1 = QubitPlacementTag(0)
    tag2 = QubitPlacementTag(2)
    tag3 = ComputeTag()
    assert tag0 == tag1
    assert not tag0 == tag2
    assert not tag0 == tag3
    assert not tag3 == tag2
