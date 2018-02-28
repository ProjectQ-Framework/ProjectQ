#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
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

        This function can be used to measure expectation values more
        efficiently (emulation).

        Returns:
            A tuple where the first entry is a dictionary mapping qubit indices
            to bit-locations and the second entry is the corresponding state
            vector
        """
        return (self._map, self._state)

    def measure_qubits(self, ids):
        """
        Measure the qubits with IDs ids and return a list of measurement
        outcomes (True/False).

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
            tol (float): Tolerance for numerical errors when determining
                whether the qubit is indeed classical.

        Raises:
            RuntimeError: If the qubit is in a superposition, i.e., has not
                been measured / uncomputed.
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
                    raise RuntimeError("Qubit has not been measured / "
                                       "uncomputed. Cannot access its "
                                       "classical value and/or deallocate a "
                                       "qubit in superposition!")
        return down

    def deallocate_qubit(self, ID):
        """
        Deallocate a qubit (if it has been measured / uncomputed).

        Args:
            ID (int): ID of the qubit to deallocate.

        Raises:
            RuntimeError: If the qubit is in a superposition, i.e., has not
                been measured / uncomputed.
        """
        pos = self._map[ID]

        cv = self.get_classical_value(ID)

        newstate = _np.zeros((1 << (self._num_qubits - 1)),
                             dtype=_np.complex128)
        k = 0
        for i in range((1 << pos) * int(cv), len(self._state),
                       (1 << (pos + 1))):
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
            qubit_ids (list<list<int>>): List of lists of qubit IDs to which
                the gate is being applied. Every gate is applied to a tuple of
                quantum registers, which corresponds to this 'list of lists'.
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
                        arg_list[qr_i] |= (((i >> qb_locs[qr_i][qb_i]) & 1) <<
                                           qb_i)

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

    def get_expectation_value(self, terms_dict, ids):
        """
        Return the expectation value of a qubit operator w.r.t. qubit ids.

        Args:
            terms_dict (dict): Operator dictionary (see QubitOperator.terms)
            ids (list[int]): List of qubit ids upon which the operator acts.

        Returns:
            Expectation value
        """
        expectation = 0.
        current_state = _np.copy(self._state)
        for (term, coefficient) in terms_dict:
            self._apply_term(term, ids)
            delta = coefficient * _np.vdot(current_state, self._state).real
            expectation += delta
            self._state = _np.copy(current_state)
        return expectation

    def apply_qubit_operator(self, terms_dict, ids):
        """
        Apply a (possibly non-unitary) qubit operator to qubits.

        Args:
            terms_dict (dict): Operator dictionary (see QubitOperator.terms)
            ids (list[int]): List of qubit ids upon which the operator acts.
        """
        new_state = _np.zeros_like(self._state)
        current_state = _np.copy(self._state)
        for (term, coefficient) in terms_dict:
            self._apply_term(term, ids)
            self._state *= coefficient
            new_state += self._state
            self._state = _np.copy(current_state)
        self._state = new_state

    def get_probability(self, bit_string, ids):
        """
        Return the probability of the outcome `bit_string` when measuring
        the qubits given by the list of ids.

        Args:
            bit_string (list[bool|int]): Measurement outcome.
            ids (list[int]): List of qubit ids determining the ordering.

        Returns:
            Probability of measuring the provided bit string.

        Raises:
            RuntimeError if an unknown qubit id was provided.
        """
        for i in range(len(ids)):
            if ids[i] not in self._map:
                raise RuntimeError("get_probability(): Unknown qubit id. "
                                   "Please make sure you have called "
                                   "eng.flush().")
        mask = 0
        bit_str = 0
        for i in range(len(ids)):
            mask |= (1 << self._map[ids[i]])
            bit_str |= (bit_string[i] << self._map[ids[i]])
        probability = 0.
        for i in range(len(self._state)):
            if (i & mask) == bit_str:
                e = self._state[i]
                probability += e.real**2 + e.imag**2
        return probability

    def get_amplitude(self, bit_string, ids):
        """
        Return the probability amplitude of the supplied `bit_string`.
        The ordering is given by the list of qubit ids.

        Args:
            bit_string (list[bool|int]): Computational basis state
            ids (list[int]): List of qubit ids determining the
                ordering. Must contain all allocated qubits.

        Returns:
            Probability amplitude of the provided bit string.

        Raises:
            RuntimeError if the second argument is not a permutation of all
            allocated qubits.
        """
        if not set(ids) == set(self._map):
            raise RuntimeError("The second argument to get_amplitude() must"
                               " be a permutation of all allocated qubits. "
                               "Please make sure you have called "
                               "eng.flush().")
        index = 0
        for i in range(len(ids)):
            index |= (bit_string[i] << self._map[ids[i]])
        return self._state[index]

    def emulate_time_evolution(self, terms_dict, time, ids, ctrlids):
        """
        Applies exp(-i*time*H) to the wave function, i.e., evolves under
        the Hamiltonian H for a given time. The terms in the Hamiltonian
        are not required to commute.

        This function computes the action of the matrix exponential using
        ideas from Al-Mohy and Higham, 2011.
        TODO: Implement better estimates for s.

        Args:
            terms_dict (dict): Operator dictionary (see QubitOperator.terms)
                defining the Hamiltonian.
            time (scalar): Time to evolve for
            ids (list): A list of qubit IDs to which to apply the evolution.
            ctrlids (list): A list of control qubit IDs.
        """
        # Determine the (normalized) trace, which is nonzero only for identity
        # terms:
        tr = sum([c for (t, c) in terms_dict if len(t) == 0])
        terms_dict = [(t, c) for (t, c) in terms_dict if len(t) > 0]
        op_nrm = abs(time) * sum([abs(c) for (_, c) in terms_dict])
        # rescale the operator by s:
        s = int(op_nrm + 1.)
        correction = _np.exp(-1j * time * tr / float(s))
        output_state = _np.copy(self._state)
        mask = self._get_control_mask(ctrlids)
        for i in range(s):
            j = 0
            nrm_change = 1.
            while nrm_change > 1.e-12:
                coeff = (-time * 1j) / float(s * (j + 1))
                current_state = _np.copy(self._state)
                update = 0j
                for t, c in terms_dict:
                    self._apply_term(t, ids)
                    self._state *= c
                    update += self._state
                    self._state = _np.copy(current_state)
                update *= coeff
                self._state = update
                for i in range(len(update)):
                    if (i & mask) == mask:
                        output_state[i] += update[i]
                nrm_change = _np.linalg.norm(update)
                j += 1
            for i in range(len(update)):
                if (i & mask) == mask:
                    output_state[i] *= correction
            self._state = _np.copy(output_state)

    def apply_controlled_gate(self, m, ids, ctrlids):
        """
        Applies the k-qubit gate matrix m to the qubits with indices ids,
        using ctrlids as control qubits.

        Args:
            m (list[list]): 2^k x 2^k complex matrix describing the k-qubit
                gate.
            ids (list): A list containing the qubit IDs to which to apply the
                gate.
            ctrlids (list): A list of control qubit IDs (i.e., the gate is
                only applied where these qubits are 1).
        """
        mask = self._get_control_mask(ctrlids)
        if len(m) == 2:
            pos = self._map[ids[0]]
            self._single_qubit_gate(m, pos, mask)
        else:
            pos = [self._map[ID] for ID in ids]
            self._multi_qubit_gate(m, pos, mask)

    def _single_qubit_gate(self, m, pos, mask):
        """
        Applies the single qubit gate matrix m to the qubit at position `pos`
        using `mask` to identify control qubits.

        Args:
            m (list[list]): 2x2 complex matrix describing the single-qubit
                gate.
            pos (int): Bit-position of the qubit.
            mask (int): Bit-mask where set bits indicate control qubits.
        """
        def kernel(u, d, m):
            return u * m[0][0] + d * m[0][1], u * m[1][0] + d * m[1][1]

        for i in range(0, len(self._state), (1 << (pos + 1))):
            for j in range(1 << pos):
                if ((i + j) & mask) == mask:
                    id1 = i + j
                    id2 = id1 + (1 << pos)
                    self._state[id1], self._state[id2] = kernel(
                        self._state[id1],
                        self._state[id2],
                        m)

    def _multi_qubit_gate(self, m, pos, mask):
        """
        Applies the k-qubit gate matrix m to the qubits at `pos`
        using `mask` to identify control qubits.

        Args:
            m (list[list]): 2^k x 2^k complex matrix describing the k-qubit
                gate.
            pos (list[int]): List of bit-positions of the qubits.
            mask (int): Bit-mask where set bits indicate control qubits.
        """
        # follows the description in https://arxiv.org/abs/1704.01127
        inactive = [p for p in range(len(self._map)) if p not in pos]

        matrix = _np.matrix(m)
        subvec = _np.zeros(1 << len(pos), dtype=complex)
        subvec_idx = [0] * len(subvec)
        for c in range(1 << len(inactive)):
            # determine base index (state of inactive qubits)
            base = 0
            for i in range(len(inactive)):
                base |= ((c >> i) & 1) << inactive[i]
            # check the control mask
            if mask != (base & mask):
                continue
            # now gather all elements involved in mat-vec mul
            for x in range(len(subvec_idx)):
                offset = 0
                for i in range(len(pos)):
                    offset |= ((x >> i) & 1) << pos[i]
                subvec_idx[x] = base | offset
                subvec[x] = self._state[subvec_idx[x]]
            # perform mat-vec mul
            self._state[subvec_idx] = matrix.dot(subvec)

    def set_wavefunction(self, wavefunction, ordering):
        """
        Set wavefunction and qubit ordering.

        Args:
            wavefunction (list[complex]): Array of complex amplitudes
                describing the wavefunction (must be normalized).
            ordering (list): List of ids describing the new ordering of qubits
                (i.e., the ordering of the provided wavefunction).
        """
        # wavefunction contains 2^n values for n qubits
        assert len(wavefunction) == (1 << len(ordering))
        # all qubits must have been allocated before
        if (not all([Id in self._map for Id in ordering]) or
                len(self._map) != len(ordering)):
            raise RuntimeError("set_wavefunction(): Invalid mapping provided."
                               " Please make sure all qubits have been "
                               "allocated previously (call eng.flush()).")

        self._state = _np.array(wavefunction, dtype=_np.complex128)
        self._map = {ordering[i]: i for i in range(len(ordering))}

    def collapse_wavefunction(self, ids, values):
        """
        Collapse a quantum register onto a classical basis state.

        Args:
            ids (list[int]): Qubit IDs to collapse.
            values (list[bool]): Measurement outcome for each of the qubit IDs
                in `ids`.
        Raises:
            RuntimeError: If probability of outcome is ~0 or unknown qubits
                are provided.
        """
        assert len(ids) == len(values)
        # all qubits must have been allocated before
        if not all([Id in self._map for Id in ids]):
            raise RuntimeError("collapse_wavefunction(): Unknown qubit id(s)"
                               " provided. Try calling eng.flush() before "
                               "invoking this function.")
        mask = 0
        val = 0
        for i in range(len(ids)):
            pos = self._map[ids[i]]
            mask |= (1 << pos)
            val |= (int(values[i]) << pos)
        nrm = 0.
        for i in range(len(self._state)):
            if (mask & i) == val:
                nrm += _np.abs(self._state[i]) ** 2
        if nrm < 1.e-12:
            raise RuntimeError("collapse_wavefunction(): Invalid collapse! "
                               "Probability is ~0.")
        inv_nrm = 1. / _np.sqrt(nrm)
        for i in range(len(self._state)):
            if (mask & i) != val:
                self._state[i] = 0.
            else:
                self._state[i] *= inv_nrm

    def run(self):
        """
        Dummy function to implement the same interface as the c++ simulator.
        """
        pass

    def _apply_term(self, term, ids, ctrlids=[]):
        """
        Applies a QubitOperator term to the state vector.
        (Helper function for time evolution & expectation)

        Args:
            term: One term of QubitOperator.terms
            ids (list[int]): Term index to Qubit ID mapping
            ctrlids (list[int]): Control qubit IDs
        """
        X = [[0., 1.], [1., 0.]]
        Y = [[0., -1j], [1j, 0.]]
        Z = [[1., 0.], [0., -1.]]
        gates = [X, Y, Z]
        for local_op in term:
            qb_id = ids[local_op[0]]
            self.apply_controlled_gate(gates[ord(local_op[1]) - ord('X')],
                                       [qb_id], ctrlids)
