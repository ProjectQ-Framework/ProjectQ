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
This file defines BasicQubit, Qubit, WeakQubit and Qureg.

A Qureg represents a list of Qubit or WeakQubit objects.
Qubit represents a (logical-level) qubit with a unique index provided by the
MainEngine. Qubit objects are automatically deallocated if they go out of
scope and intented to be used within Qureg objects in user code.

Example:
	.. code-block:: python

		from projectq import MainEngine
		eng = MainEngine()
		qubit = eng.allocate_qubit()

qubit is a Qureg of size 1 with one Qubit object which is deallocated once
qubit goes out of scope.

WeakQubit are used inside the Command object and are not automatically
deallocated.
"""


class BasicQubit(object):
	"""
	BasicQubit objects represent qubits.
	
	They have an id and a reference to the owning engine.
	"""
	def __init__(self, engine, idx):
		"""
		Initialize a BasicQubit object.
		
		Args:
			engine: Owning engine / engine that created the qubit
			idx: Unique index of the qubit referenced by this qubit
		"""
		self.id = idx
		self.engine = engine

	def __str__(self):
		"""
		Return string representation of this qubit.
		"""
		return str(self.id)

	def __bool__(self):
		"""
		Access the result of a previous measurement and return False / True (0/1)
		"""
		return self.engine.main_engine.get_measurement_result(self)

	def __nonzero__(self):
		"""
		Access the result of a previous measurement for Python 2.7.
		"""
		return self.__bool__()

	def __int__(self):
		"""
		Access the result of a previous measurement and return as integer (0 / 1).
		"""
		return int(bool(self))

	def __eq__(self, other):
		"""
		Compare with other qubit (Returns True if equal id and engine).
		
		Args:
			other (BasicQubit): BasicQubit to which to compare this one
		"""
		return (isinstance(other, self.__class__) and self.id == other.id and
		        self.engine == other.engine)

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		"""
		Return the hash of this qubit.
		
		Hash definition because of custom __eq__.
		Enables storing a qubit in, e.g., a set.
		"""
		return hash((self.id, self.engine, object.__hash__(self)))


class Qubit(BasicQubit):
	"""
	Qubit class.
	
	Represents a (logical-level) qubit with a unique index provided by the
	MainEngine. Once the qubit goes out of scope (and is garbage-collected), it
	deallocates itself automatically, allowing automatic resource management.
	
	Thus the qubit is not copyable; only returns a reference to the same object.
	"""
	def __del__(self):
		"""
		Destroy the qubit and deallocate it (automatically).
		"""
		self.engine.deallocate_qubit(self)
		self.id = -1

	def __copy__(self):
		"""
		Non-copyable (returns reference to self).
		
		Note:
			To prevent problems with automatic deallocation, qubits are not copyable!
		"""
		return self

	def __deepcopy__(self, memo):
		"""
		Non-deepcopyable (returns reference to self).
		
		Note:
			To prevent problems with automatic deallocation, qubits are not deepcopyable!
		"""
		return self


class WeakQubitRef(BasicQubit):
	"""
	WeakQubitRef objects are used inside the Command object.
	
	Qubits feature automatic deallocation when destroyed. WeakQubitRefs, on the
	other hand, do not share this feature, allowing to copy them and pass them
	along the compiler pipeline, while the actual qubit objects may be garbage-
	collected (and, thus, cleaned up early). Otherwise there is no difference
	between a WeakQubitRef and a Qubit object.
	"""
	pass


class Qureg(list):
	"""
	Quantum register class.
	
	Simplifies accessing measured values for single-qubit registers (no []-
	access necessary) and enables pretty-printing of general quantum registers
	(call Qureg.__str__(qureg)).
	"""
	def __bool__(self):
		"""
		Return measured value if Qureg consists of 1 qubit only.
		
		Raises:
			Exception if more than 1 qubit resides in this register (then you
			need to specify which value to get using qureg[???])
		"""
		if len(self) == 1:
			return bool(self[0])
		else:
			raise Exception("__bool__(qureg): Quantum register contains more than 1"
			                "qubit. Use __bool__(qureg[idx]) instead.")

	def __int__(self):
		"""
		Return measured value if Qureg consists of 1 qubit only.
		
		Raises:
			Exception if more than 1 qubit resides in this register (then you
			need to specify which value to get using qureg[???])
		"""
		if len(self) == 1:
			return int(self[0])
		else:
			raise Exception("__int__(qureg): Quantum register contains more than 1"
			                "qubit. Use __int__(qureg[idx]) instead.")

	def __nonzero__(self):
		"""
		Return measured value if Qureg consists of 1 qubit only for Python 2.7.
		
		Raises:
			Exception if more than 1 qubit resides in this register (then you
			need to specify which value to get using qureg[???])
		"""
		if len(self) == 1:
			return int(self[0])
		else:
			raise Exception("__int__(qureg): Quantum register contains more than 1"
			                "qubit. Use __int__(qureg[idx]) instead.")

	def __str__(self):
		"""
		Get string representation of a quantum register.
		"""
		if len(self) == 1:
			return "Qubit[" + str(self[0]) + "]"
		else:
			return "Qureg" + str([q.id for q in self])

	@property
	def engine(self):
		"""
		Return owning engine.
		"""
		return self[0].engine
	
	@engine.setter
	def engine(self, eng):
		"""
		Set owning engine.
		"""
		for qb in self:
			qb.engine = eng
