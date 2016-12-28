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
Contains the main engine of every compiler engine pipeline, called MainEngine.
"""

import atexit
import weakref

import projectq
from projectq.cengines import BasicEngine
from projectq.ops import Command, FlushGate
from projectq.types import WeakQubitRef
from projectq.backends import Simulator


class NotYetMeasuredError(Exception):
	pass


class UnsupportedEngineError(Exception):
	pass


class MainEngine(BasicEngine):
	"""
	The MainEngine class provides all functionality of the main compiler engine.
	
	It initializes all further compiler engines (calls, e.g., .next_engine=...)
	and keeps track of measurement results and active qubits (and their IDs).
	
	Attributes:
		next_engine (BasicEngine): Next compiler engine (or the back-end).
		main_engine (MainEngine): Self.
		active_qubits (WeakSet): WeakSet containing all active qubits
		dirty_qubits (Set): Containing all dirty qubit ids
		
	"""
	def __init__(self, backend=None, engine_list=None):
		"""
		Initialize the main compiler engine and all compiler engines.
		
		Sets 'next_engine'- and 'main_engine'-attributes of all compiler engines
		and adds the back-end as the last engine.
		
		Args:
			backend (BasicEngine): Backend to send the circuit to.
			engine_list (list<BasicEngine>): List of engines / backends to use as
				compiler engines.
			
		Example:
			.. code-block:: python
				
				from projectq import MainEngine
				eng = MainEngine() # will load default setup using Simulator backend
			
		Alternatively, one can specify all compiler engines explicitly, e.g., 
		
		Example:
			.. code-block:: python
				
				from projectq.cengines import TagRemover,AutoReplacer,LocalOptimizer
				from projectq.backends import Simulator
				from projectq import MainEngine
				engines = [AutoReplacer(), TagRemover(), LocalOptimizer(3)]
				eng = MainEngine(Simulator(), engines)
		"""
		BasicEngine.__init__(self)
		
		if backend is None:
			backend = Simulator()
		else: # Test that backend is BasicEngine object
			if not isinstance(backend, BasicEngine):
				raise UnsupportedEngineError(
					"\nYou supplied a backend which is not supported,\n" +
					"i.e. not an instance of BasicEngine.\n"+
					"Did you forget the brackets to create an instance?\n" +
					"E.g. MainEngine(backend=Simulator) instead of \n" +
					"     MainEngine(backend=Simulator())")
		if engine_list is None:
			try:
				engine_list = projectq.default_engines()
			except AttributeError:
				from projectq.setups.default import default_engines
				engine_list = default_engines()
		else: # Test that engine list elements are all BasicEngine objects
			if not isinstance(engine_list, list):
				raise UnsupportedEngineError(
					"\n The engine_list argument is not a list!\n")
			for current_eng in engine_list:
				if not isinstance(current_eng, BasicEngine):
					raise UnsupportedEngineError(
						"\nYou supplied an unsupported engine in engine_list,\n" +
						"i.e. not an instance of BasicEngine.\n"+
						"Did you forget the brackets to create an instance?\n" +
						"E.g. MainEngine(engine_list=[AutoReplacer]) instead of \n" +
						"     MainEngine(engine_list=[AutoReplacer()])")
		
		engine_list.append(backend)

		# Test that user did not supply twice the same engine instance
		num_different_engines = len(set([id(item) for item in engine_list]))
		if len(engine_list) != num_different_engines:
			raise UnsupportedEngineError(
				"\n Error:\n You supplied twice the same engine as backend" +
				" or item in engine_list. This doesn't work. Create two \n" +
				" separate instances of a compiler engine if it is needed\n" +
				" twice.\n")
		
		self._qubit_idx = int(0)
		for i in range(len(engine_list) - 1):
			engine_list[i].next_engine = engine_list[i + 1]
			engine_list[i].main_engine = self
		engine_list[-1].main_engine = self
		engine_list[-1].is_last_engine = True
		self.next_engine = engine_list[0]
		self.main_engine = self
		self.active_qubits = weakref.WeakSet()
		self._measurements = dict()
		self.dirty_qubits = set()
		
		# In order to terminate an example code without eng.flush or Measure
		self._delfun = lambda x: x.flush(deallocate_qubits=True)
		atexit.register(self._delfun, self)
	
	def __del__(self):
		"""
		Destroy the main engine.
		
		Flushes the entire circuit down the pipeline, clearing all temporary
		buffers (in, e.g., optimizers).
		"""
		self.flush()
		try:
			atexit.unregister(self._delfun)  # only available in Python3
		except AttributeError:
			pass
	
	def set_measurement_result(self, qubit, value):
		"""
		Register a measurement result
		
		The engine being responsible for measurement results needs to register
		these results with the master engine such that they are available when the
		user calls an int() or bool() conversion operator on a measured qubit.
		
		Args:
			qubit (BasicQubit): Qubit for which to register the measurement result.
			value (bool): Boolean value of the measurement outcome (True / False = 1
				/ 0 respectively)
		"""
		self._measurements[qubit.id] = bool(value)
	
	def get_measurement_result(self, qubit):
		"""
		Return the classical value of a measured qubit, given that an engine
		registered this result previously (see setMeasurementResult).
		
		Args:
			qubit (BasicQubit): Qubit of which to get the measurement result.
			
		Example:
			.. code-block:: python
			
				from projectq.ops import H, Measure
				from projectq import MainEngine
				eng = MainEngine()
				qubit = eng.allocate_qubit() # quantum register of size 1
				H | qubit
				Measure | qubit
				eng.get_measurement_result(qubit[0]) == int(qubit)
		"""
		if qubit.id in self._measurements:
			return self._measurements[qubit.id]
		else:
			raise NotYetMeasuredError(
			                "\nError: Can't access measurement result for " +
			                "qubit #" + str(qubit.id) + ". The problem may " +
			                "be:\n\t1. Your " +
			                "code lacks a measurement statement\n\t" +
			                "2. You have not yet called engine.flush() to " +
			                "force execution of your code\n\t3. The " +
			                "underlying backend failed to register " +
			                "the measurement result\n")
	
	def get_new_qubit_id(self):
		"""
		Returns a unique qubit id to be used for the next qubit allocation.
		
		Returns:
			new_qubit_id (int): New unique qubit id.
		"""
		self._qubit_idx += 1
		return (self._qubit_idx - 1)
	
	def receive(self, command_list):
		"""
		Forward the list of commands to the first engine.
		
		Args:
			command_list (list<Command>): List of commands to receive (and then send
				on)
		"""
		self.send(command_list)
	
	def flush(self, deallocate_qubits=False):
		"""
		Flush the entire circuit down the pipeline, clearing potential buffers
		(of, e.g., optimizers).
		
		Args:
			deallocate_qubits (bool): If True, deallocates all qubits that are still
				alive (invalidating references to them by setting their id to -1)
		"""
		if deallocate_qubits:
			for qb in self.active_qubits:
				qb.__del__()
			self.active_qubits = weakref.WeakSet()
		self.receive([Command(self, FlushGate(), ([WeakQubitRef(self, -1)],))])
