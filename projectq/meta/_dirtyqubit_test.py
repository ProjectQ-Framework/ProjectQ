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

"""Tests for projectq.meta._dirtyqubit.py"""

from projectq.meta import ComputeTag

from projectq.meta import _dirtyqubit


def test_dirty_qubit_tag():
	tag0 = _dirtyqubit.DirtyQubitTag()
	tag1 = _dirtyqubit.DirtyQubitTag()
	tag2 = ComputeTag()
	assert tag0 == tag1
	assert not tag0 != tag1
	assert not tag0 == tag2
