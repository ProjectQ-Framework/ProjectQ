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
Contains a (slow) Python simulator.

Please compile the c++ simulator for large-scale simulations.
"""

import cmath
import random
import numpy as _np


class Simulator(object):
	"""
	Python implementation of a quantum computer simulator.
	
	This Simulator can be used as a backup if compiling the c++ simulator is
	not an option (for some reason). It has the same features but is much
	slower, so please consider building the c++ version for larger experiments.
	"""
	def __init__(self, rnd_seed, *args, **kwargs):
		"""
		Initialize the simulator.
		
		Args:
			rnd_seed (int): Seed to initialize the random number generator.
			args: Dummy argument to allow an interface identical to the c++
				simulator.
			kwargs: Same as args.
		"""
		random.seed(rnd_seed)
		self._state = _np.ones(1, dtype=_np.complex128)
		self._map = dict()
		self._num_qubits = 0
		print("(Note: This is the (slow) Python simulator.)")
	
	
	def cheat(self):
		"""
		Return the qubit index to bit location map and the corresponding state
		vector.
		
		This function can be used to measure expectation values more efficiently
		(emulation).
		
		Returns:
			A tuple where the first entry is a dictionary mapping qubit indices to
			bit-locations	and the second entry is the corresponding state vector
		"""
		return (self._map, self._state)
	
	def measure_qubits(self, ids):
		"""
		Measure the qubits with IDs ids and return a list of measurement outcomes
		(True/False).
		
		Args:
			ids (list<int>): List of qubit IDs to measure.
			
		Returns:
			List of measurement results (containing either True or False).
		"""
		P = random.random()
		val = 0.
		i_picked = 0
		while val < P and i_picked < len(self._state):
			val += _np.abs(self._state[i_picked]) ** 2
			i_picked += 1
		
		i_picked -= 1
		
		pos = [self._map[ID] for ID in ids]
		res = [False] * len(pos)
		
		mask = 0
		val = 0
		for i in range(len(pos)):
			res[i] = (((i_picked >> pos[i]) & 1) == 1)
			mask |= (1 << pos[i])
			val |= ((res[i] & 1) << pos[i])
			
		nrm = 0.
		for i in range(len(self._state)):
			if (mask & i) != val:
				self._state[i] = 0.
			else:
				nrm += _np.abs(self._state[i]) ** 2

		self._state *= 1. / _np.sqrt(nrm)
		return res
	
	def allocate_qubit(self, ID):
		"""
		Allocate a qubit.
		
		Args:
			ID (int): ID of the qubit which is being allocated.
		"""
		self._map[ID] = self._num_qubits
		self._num_qubits += 1
		self._state.resize(1 << self._num_qubits)
	
	def get_classical_value(self, ID, tol=1.e-10):
		"""
		Return the classical value of a classical bit (i.e., a qubit which has
		been measured / uncomputed).
		
		Args:
			ID (int): ID of the qubit of which to get the classical value.
			tol (float): Tolerance for numerical errors when determining whether
				the qubit is indeed classical.
			
		Raises:
			RuntimeError: If the qubit is in a superposition, i.e., has not been
				measured / uncomputed.
		"""
		pos = self._map[ID]
		up = down = False
		
		for i in range(0, len(self._state), (1 << (pos + 1))):
			for j in range(0, (1 << pos)):
				if _np.abs(self._state[i + j]) > tol:
					up = True
				if _np.abs(self._state[i + j + (1 << pos)]) > tol:
					down = True
				if up and down:
					raise RuntimeError("Qubit has not been measured / uncomputed. Cannot "
					                "access its classical value and/or deallocate a "
					                "qubit in superposition!")
		return down
	
	def deallocate_qubit(self, ID):
		"""
		Deallocate a qubit (if it has been measured / uncomputed).
		
		Args:
			ID (int): ID of the qubit to deallocate.
			
		Raises:
			RuntimeError: If the qubit is in a superposition, i.e., has not been
				measured / uncomputed.
		"""
		pos = self._map[ID]
		
		cv = self.get_classical_value(ID)
		
		newstate = _np.zeros((1 << (self._num_qubits - 1)), dtype=_np.complex128)
		k = 0
		for i in range((1 << pos) * int(cv), len(self._state), (1 << (pos + 1))):
			newstate[k:k + (1 << pos)] = self._state[i:i + (1 << pos)]
			k += (1 << pos)
			
		newmap = dict()
		for key, value in self._map.items():
			if value > pos:
				newmap[key] = value - 1
			elif key != ID:
				newmap[key] = value
		self._map = newmap
		self._state = newstate
		self._num_qubits -= 1
	
	def _get_control_mask(self, ctrlids):
		"""
		Get control mask from list of control qubit IDs.
		
		Returns:
			A mask which represents the control qubits in binary.
		"""
		mask = 0
		for ctrlid in ctrlids:
			ctrlpos = self._map[ctrlid]
			mask |= (1 << ctrlpos)
		return mask
	
	def emulate_math(self, f, qubit_ids, ctrlqubit_ids):
		"""
		Emulate a math function (e.g., BasicMathGate).
		
		Args:
			f (function): Function executing the operation to emulate.
			qubit_ids (list<list<int>>): List of lists of qubit IDs to which the
				gate is being applied. Every gate is applied to a tuple of quantum
				registers, which corresponds to this 'list of lists'.
			ctrlqubit_ids (list<int>): List of control qubit ids.
		"""
		mask = self._get_control_mask(ctrlqubit_ids)
		# determine qubit locations from their IDs
		qb_locs = []
		for qureg in qubit_ids:
			qb_locs.append([])
			for qubit_id in qureg:
				qb_locs[-1].append(self._map[qubit_id])

		newstate = _np.zeros_like(self._state)
		for i in range(0, len(self._state)):
			if (mask & i) == mask:
				arg_list = [0] * len(qb_locs)
				for qr_i in range(len(qb_locs)):
					for qb_i in range(len(qb_locs[qr_i])):
						arg_list[qr_i] |= (((i >> qb_locs[qr_i][qb_i]) & 1) << qb_i)
				
				res = f(arg_list)
				new_i = i
				for qr_i in range(len(qb_locs)):
					for qb_i in range(len(qb_locs[qr_i])):
						if not (((new_i >> qb_locs[qr_i][qb_i]) & 1) ==
						        ((res[qr_i] >> qb_i) & 1)):
							new_i ^= (1 << qb_locs[qr_i][qb_i])
				newstate[new_i] = self._state[i]
			else:
				newstate[i] = self._state[i]
			
		self._state = newstate
	
	def apply_controlled_gate(self, m, ids, ctrlids):
		"""
		Applies the single qubit gate matrix m to the qubit with index ids[0],
		using ctrlids as control qubits.
		
		Args:
			m (list<list>): 2x2 complex matrix describing the single-qubit gate.
			ids (list): A list containing the qubit ID to which to apply the gate.
			ctrlids (list): A list of control qubit IDs (i.e., the gate is only
				applied where these qubits are 1).
		"""
		ID = ids[0]
		pos = self._map[ID]
		
		mask = self._get_control_mask(ctrlids)

		def kernel(u, d, m):
			return u * m[0][0] + d * m[0][1], u * m[1][0] + d * m[1][1]
		
		for i in range(0, len(self._state), (1 << (pos + 1))):
			for j in range(0, 1 << pos):
				if ((i + j) & mask) == mask:
					self._state[i + j], self._state[i + j + (1 << pos)] = kernel(
                                              self._state[i + j],
                                              self._state[i + j + (1 << pos)],
                                              m)
	
	def run(self):
		"""
		Dummy function to implement the same interface as the c++ simulator.
		"""
		pass
