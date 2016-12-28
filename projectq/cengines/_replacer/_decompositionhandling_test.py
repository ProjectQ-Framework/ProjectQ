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

"""Tests for projectq.cengines._replacer._decompositionhandling.py."""

import pytest

from projectq.ops import BasicRotationGate

from projectq.cengines._replacer import _decompositionhandling


def test_register_decomposition_wrong_input():
	class WrongInput(BasicRotationGate):
		pass
	
	def decompose_func(cmd):
		pass
	
	def recognize_func(cmd):
		pass
	
	with pytest.raises(_decompositionhandling.ThisIsNotAGateClassError):
		_decompositionhandling.register_decomposition(WrongInput.__class__, 
		                                     decompose_func, recognize_func)
	decompose_func("")
	recognize_func("")
