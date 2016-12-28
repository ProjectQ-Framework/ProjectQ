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
Contains a CommandModifier engine, which can be used to, e.g., modify the tags
of all commands which pass by (see the AutoReplacer for an example).
"""
from projectq.cengines import BasicEngine


class CommandModifier(BasicEngine):
	"""
	CommandModifier is a compiler engine which applies a function to all
	incoming commands, sending on the resulting command instead of the
	original one.
	"""
	def __init__(self, cmd_mod_fun):
		"""
		Initialize the CommandModifier.
		
		Args:
			cmd_mod_fun (function): Function which, given a command cmd, returns
				the command it should send instead.
				
		Example:
			.. code-block:: python
			
				def cmd_mod_fun(cmd):
					cmd.tags += [MyOwnTag()]
				compiler_engine = CommandModifier(cmd_mod_fun)
				...
		"""
		BasicEngine.__init__(self)
		self._cmd_mod_fun = cmd_mod_fun
	
	def receive(self, command_list):
		"""
		Receive a list of commands from the previous engine, modify all commands,
		and send them on to the next engine.
		
		Args:
			command_list (list<Command>): List of commands to receive and then
				(after modification) send on.
		"""
		new_command_list = [self._cmd_mod_fun(cmd) for cmd in command_list]
		self.send(command_list)
