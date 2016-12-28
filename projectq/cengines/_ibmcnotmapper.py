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
Contains a compiler engine to map the CNOT gates for the IBM backend.
"""
from copy import deepcopy

from projectq.cengines import (BasicEngine,
                              ForwarderEngine,
                              CommandModifier)
from projectq.meta import get_control_count
from projectq.ops import (CNOT,
                          NOT,
                          H,
                          FastForwardingGate,
                          FlushGate,
                          All)

from projectq.backends import IBMBackend


class IBMCNOTMapper(BasicEngine):
	"""
	CNOT mapper for the IBM backend.

	Transforms CNOTs such that all CNOTs within the circuit have the same
	target qubit (required by IBM backend). If necessary, it will flip
	around the CNOT gate by first applying Hadamard gates to both qubits, then
	CNOT with swapped control and target qubit, and finally Hadamard gates to
	both qubits.
	
	Note:
		The mapper has to be run once on the entire circuit. Else, an Exception
		will be raised (if, e.g., several measurements are performed without re-
		initializing the mapper).
	
	Warning:
		If the provided circuit cannot be mapped to the hardware layout without
		performing Swaps, the mapping procedure **raises an Exception**.
	"""

	def __init__(self):
		"""
		Initialize an IBM CNOT Mapper compiler engine.
		
		Resets the mapping.
		"""
		BasicEngine.__init__(self)
		self._reset()
		
	def is_available(self, cmd):
		"""
		Check if the IBM backend can perform the Command cmd and return True if
		so.

		Args:
			cmd (Command): The command to check
		"""
		return IBMBackend().is_available(cmd)
	
	def _reset(self):
		"""
		Reset the mapping parameters so the next circuit can be mapped.
		"""
		self._cmds = []
		self._cnot_ids = []
		self._cnot_id = -1
	
	def _is_cnot(self, cmd):
		"""
		Check if the command corresponds to a CNOT (controlled NOT gate).
		
		Args:
			cmd (Command): Command to check whether it is a controlled NOT gate.
		"""
		return isinstance(cmd.gate, NOT.__class__) and get_control_count(cmd) == 1
	
	def _run(self):
		"""
		Runs all stored gates.

		Raises:
			Exception:
				If the mapping to the IBM backend cannot be performed or if the
				mapping was already determined but more CNOTs get sent down the
				pipeline.
		"""
		cnot_id = self._cnot_id
		if cnot_id == -1 and len(self._cnot_ids) > 0:
			cnot_id = self._cnot_ids[0]
			if len(self._cnot_ids) == 2:  # we can optimize (at least a little bit)!
				count1 = 0
				count2 = 0
				for cmd in self._cmds:
					if self._is_cnot(cmd):
						qb = cmd.qubits[0][0]
						ctrl = cmd.control_qubits[0]
						if ctrl.id == self._cnot_ids[0]:
							count1 += 1
						elif ctrl.id == self._cnot_ids[1]:
							count2 += 1
				if count1 > count2:
					cnot_id = self._cnot_ids[1]
		
		for cmd in self._cmds:
			if self._is_cnot(cmd) and not cmd.qubits[0][0].id == cnot_id:
				# we have to flip it around. To have nice syntax, we'll use a
				# forwarder engine and a command modifier to get the tags right.
				# (If the CNOT is an 'uncompute', then so must be the remapped CNOT)
				def cmd_mod(command):
					command.tags = cmd.tags[:] + command.tags
					command.engine = self.main_engine
					return command
					
				cmd_mod_eng = CommandModifier(cmd_mod)  # will add potential meta tags
				cmd_mod_eng.next_engine = self.next_engine # and send on all commands
				cmd_mod_eng.main_engine = self.main_engine
				# forward everything to the command modifier
				forwarder_eng = ForwarderEngine(cmd_mod_eng)
				cmd.engine = forwarder_eng  # and send all gates to forwarder engine.
				
				qubit = cmd.qubits[0]
				ctrl = cmd.control_qubits
				# flip the CNOT using Hadamard gates:
				All(H) | (ctrl + qubit)
				CNOT | (qubit, ctrl)
				All(H) | (ctrl + qubit)
				
				# This cmd would require remapping --> 
				# raise an exception if the CNOT id has already been determined.
				if self._cnot_id != -1:
					self._reset()
					raise Exception("\nIBM Quantum Experience does not allow "
					                "intermediate measurements / \ndestruction of "
					                "qubits! CNOT mapping may be inconsistent.\n")
			else:
				self.next_engine.receive([cmd])
		self._cmds = []
		self._cnot_id = cnot_id
	
	def _store(self, cmd):
		"""
		Store a command and handle CNOTs.

		Args:
			cmd (Command): A command to store
		Raises:
			Exception: If the mapping to the IBM backend cannot be performed without
				SWAPs.
		"""
		if self._is_cnot(cmd):
			# CNOT encountered
			if len(self._cnot_ids) == 0:
				self._cnot_ids += [cmd.control_qubits[0].id, cmd.qubits[0][0].id]
			else:
				apply_to = cmd.qubits[0][0].id
				ctrl = cmd.control_qubits[0].id
				if not apply_to in self._cnot_ids:
					if not ctrl in self._cnot_ids:
						raise Exception("Mapping without SWAPs failed! Sorry...")
					else:
						self._cnot_ids = [ctrl]
				elif not ctrl in self._cnot_ids:
					self._cnot_ids = [apply_to]
		
		self._cmds.append(cmd)
	
	def receive(self, command_list):
		"""
		Receives a command list and, for each command, stores it until completion.

		Args:
			command_list (list of Command objects): list of commands to receive.
		
		Raises:
			Exception: If mapping the CNOT gates to 1 qubit would require Swaps. The
				current version only supports remapping of CNOT gates without
				performing any Swaps due to the large costs associated with Swapping
				given the CNOT constraints.
		"""
		for cmd in command_list:
			self._store(cmd)
			if isinstance(cmd.gate, FastForwardingGate):
				self._run()
			if isinstance(cmd.gate, FlushGate):
				self._reset()
