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
Contains a TagRemover engine, which removes temporary command tags (such as
Compute/Uncompute), thus enabling optimization across meta statements (loops
after unrolling, compute/uncompute, ...)
"""
from projectq.cengines import BasicEngine
from projectq.meta import ComputeTag, UncomputeTag


class TagRemover(BasicEngine):
	"""
	TagRemover is a compiler engine which removes temporary command tags (see
	the tag classes such as LoopTag in projectq.meta._loop).
	
	Removing tags is important (after having handled them if necessary) in order
	to enable optimizations across meta-function boundaries (compute/action/
	uncompute or loops after unrolling)
	"""
	def __init__(self, tags=[ComputeTag, UncomputeTag]):
		"""
		Construct the TagRemover.
		
		Args:
			tags: A list of meta tag classes (e.g., [ComputeTag, UncomputeTag])
				denoting the tags to remove
		"""
		BasicEngine.__init__(self)
		assert isinstance(tags, list)
		self._tags = tags
	
	def receive(self, command_list):
		"""
		Receive a list of commands from the previous engine, remove all tags which
		are an instance of at least one of the meta tags provided in the
		constructor, and then send them on to the next compiler engine.
		
		Args:
			command_list (list<Command>): List of commands to receive and then
				(after removing tags) send on.
		"""
		for cmd in command_list:
			for tag in self._tags:
				cmd.tags = [t for t in cmd.tags if not isinstance(t, tag)]
			self.send([cmd])
