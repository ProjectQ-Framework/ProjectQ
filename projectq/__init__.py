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

"""
ProjectQ - An open source software framework for quantum computing

Get started:
	Simply import the main compiler engine (from projectq import MainEngine)
	together with your setup of choice (e.g., import projectq.setups.default)
	and start coding!
	
	For examples, see the example folder, which features implementation of
	a quantum random number generator, entanglement demonstration (simulation
	or run on the IBM backend), Teleportation, Grover search, and
	Shor's algorithm for factoring.
"""

from ._version import __version__
from projectq.cengines import MainEngine
