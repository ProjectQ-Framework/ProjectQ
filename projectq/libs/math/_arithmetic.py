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

from projectq.types import Qureg
from projectq.meta import Control, Dagger
from projectq.ops import X, Swap


def _increment_using_1_dirty(eng, target):
	"""
	Increments a target register using O(N) gates and a single dirty ancilla.

	Args:
		eng (projectq.cengines.BasicEngine): Engine.
		target (projectq.types.Qureg): The even-sized register to increment.
	"""
	n = (len(target) + 1) // 2
	low_cut = 1 - (len(target) & 1)  # An extra qubit, or no qubits.
	med_cut = low_cut + n

	with eng.allocate_qubit(dirty=True) as q:
		low = target[:low_cut]
		med = target[low_cut:med_cut]
		high = Qureg([q] + target[med_cut:])

		# Add two into the high bits iff the low and med bits are all ON.
		_subtract_reg_from_reg(eng, med, high)
		with Control(eng, low + med):
			X | high
		_add_reg_into_reg(eng, med, high)
		with Control(eng, low + med):
			X | high

		# Increment the med bits iff the low bit is on.
		_controlled_increment_using_n_workspace(
			eng, controls=low, target=med, workspace=high)

		# Increment the low bit.
		X | low


def _decrement_using_1_dirty(eng, target):
	"""
	Increments a target register using O(N) gates and a single dirty ancilla.

	Args:
		eng (projectq.cengines.BasicEngine): Engine.
		target (projectq.types.Qureg): The even-sized register to increment.
	"""
	with Dagger(eng):
		_increment_using_1_dirty(eng, target)


def _controlled_increment_using_n_workspace(eng, controls, target, workspace):
	"""
	Increments a target register only if all of the controls are on, using O(N)
	operations.

	Uses ~half as many gates as the 1-dirty-bit incrementer.

	Args:
		eng (cengines.BasicEngine): Engine.
		controls (projectq.types.Qureg): As many controls as desired.
		target (projectq.types.Qureg): The destination register to increment.
		workspace (projectq.types.Qureg): A workspace register as large as the target.
	"""
	assert len(workspace) == len(target)

	# If controls aren't satisfied, the subtract and add cancel out.

	# If controls are satisfied, the NOTs invert the add into a subtract and
	# also invert the workspace input x into ~x = -x-1, so in total the target
	# is shifted by -x-(-x-1) = +1 as desired.

	_subtract_reg_from_reg(eng, workspace, target)
	with Control(eng, controls):
		X | target + workspace
	_add_reg_into_reg(eng, workspace, target)
	with Control(eng, controls):
		X | target + workspace


def _add_reg_into_reg(eng, input, target):
	"""
	Reversibly adds the input register's value into the target register,
	in O(N) depth and O(N) size with no ancilla using only CNOT and CSWAP
	operations.

	This construction is based on the VanRantergem adder, but modified in a way
	that avoids the need for an ancilla for the carry signal. Instead, the high
	bit of the input is used to hold the carry signal.

	Args:
		eng (projectq.cengines.BasicEngine): Engine.
		input (projectq.types.Qureg): The source register. Used as workspace, but not affected in the end.
		target (projectq.types.Qureg): The destination register.
	"""
	with Dagger(eng):
		_subtract_reg_from_reg(eng, input, target)


def _subtract_reg_from_reg(eng, input, target):
	"""
	Reversibly subtracts the input register's value out of the target register,
	in O(N) depth and O(N) size with no ancilla using only CNOT and CSWAP
	operations.

	This construction is based on the VanRantergem adder, but modified in a way
	that avoids the need for an ancilla for the carry signal. Instead, the high
	bit of the input is used to hold the carry signal.

	Args:
		eng (projectq.cengines.BasicEngine): Engine.
		input (projectq.types.Qureg): The source register. Used as workspace, but not affected in the end.
		target (projectq.types.Qureg): The destination register.
	"""
	n = len(target)

	if len(input) < n:
		# TODO: carry into an increment.
		raise NotImplementedError("Target is larger than the input.")

	if len(input) > n:
		avail, used = input[:-n], input[-n:]
		return _subtract_reg_from_reg(eng, Qureg(used), target)

	carry_signal = input[-1]
	low_inputs = input[:-1]
	m = n - 1

	# Stash same-or-different in target.
	for i in range(m):
		with Control(eng, low_inputs[i]):
			X | target[i]

	# Correct for inverted carry signal (part 1/2).
	with Control(eng, carry_signal):
		X | low_inputs

	# Propagate carry signals through input.
	for i in range(m):
		# If bits were different, carry stays same. Else bits replace carry.
		with Control(eng, target[i]):
			Swap | (carry_signal, low_inputs[i])

	# Apply carry signal effects while uncomputing carry signal.
	for i in range(m)[::-1]:
		# Apply.
		with Control(eng, carry_signal):
			X | target[i + 1]
		# Uncompute.
		with Control(eng, target[i]):
			Swap | (carry_signal, low_inputs[i])

	# Unstash same-vs-dif and correct for inverted carry signal (part 2/2).
	with Control(eng, carry_signal):
		X | low_inputs + target[1:-1]
