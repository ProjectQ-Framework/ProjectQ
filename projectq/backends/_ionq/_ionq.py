# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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

""" Back-end to run quantum programs using IonQ hardware."""
import random

from projectq.cengines import BasicEngine
from projectq.meta import LogicalQubitIDTag, get_control_count, has_negative_control
from projectq.ops import (
    Allocate,
    Barrier,
    DaggeredGate,
    Deallocate,
    FlushGate,
    HGate,
    Measure,
    R,
    Rx,
    Rxx,
    Ry,
    Ryy,
    Rz,
    Rzz,
    Sdag,
    SGate,
    SqrtXGate,
    SwapGate,
    Tdag,
    TGate,
    XGate,
    YGate,
    ZGate,
)
from projectq.types import WeakQubitRef

from . import _ionq_http_client as http_client
from ._ionq_exc import InvalidCommandError, MidCircuitMeasurementError

GATE_MAP = {
    XGate: 'x',
    YGate: 'y',
    ZGate: 'z',
    HGate: 'h',
    Rx: 'rx',
    Ry: 'ry',
    Rz: 'rz',
    SGate: 's',
    TGate: 't',
    SqrtXGate: 'v',
    Rxx: 'xx',
    Ryy: 'yy',
    Rzz: 'zz',
    SwapGate: 'swap',
}
SUPPORTED_GATES = tuple(GATE_MAP.keys())


def _rearrange_result(input_result, length):
    """Turn ``input_result`` from an integer into a bit-string.

    Args:
        input_result (int): An integer representation of qubit states.
        length (int): The total number of bits (for padding, if needed).

    Returns:
        str: A bit-string representation of ``input_result``.
    """
    bin_input = list(bin(input_result)[2:].rjust(length, '0'))
    return ''.join(bin_input)[::-1]


class IonQBackend(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """Backend for building circuits and submitting them to the IonQ API."""

    def __init__(
        self,
        use_hardware=False,
        num_runs=100,
        verbose=False,
        token=None,
        device='ionq_simulator',
        num_retries=3000,
        interval=1,
        retrieve_execution=None,
    ):  # pylint: disable=too-many-arguments
        """Constructor for the IonQBackend.

        Args:
            use_hardware (bool, optional): Whether or not to use real IonQ
                hardware or just a simulator. If False, the ionq_simulator is
                used regardless of the value of ``device``. Defaults to False.
            num_runs (int, optional): Number of times to run circuits. Defaults to 100.
            verbose (bool, optional): If True, print statistics after job
                results have been collected. Defaults to False.
            token (str, optional): An IonQ API token. Defaults to None.
            device (str, optional): Device to run jobs on.
                Supported devices are ``'ionq_qpu'`` or ``'ionq_simulator'``.
                Defaults to ``'ionq_simulator'``.
            num_retries (int, optional): Number of times to retry fetching a
                job after it has been submitted. Defaults to 3000.
            interval (int, optional): Number of seconds to wait inbetween
                result fetch retries. Defaults to 1.
            retrieve_execution (str, optional): An IonQ API Job ID.
                If provided, a job with this ID will be fetched. Defaults to None.
        """
        BasicEngine.__init__(self)
        self.device = device if use_hardware else 'ionq_simulator'
        self._num_runs = num_runs
        self._verbose = verbose
        self._token = token
        self._num_retries = num_retries
        self._interval = interval
        self._circuit = []
        self._measured_ids = []
        self._probabilities = dict()
        self._retrieve_execution = retrieve_execution
        self._clear = True

    def is_available(self, cmd):
        """Test if this backend is available to process the provided command.

        Args:
            cmd (Command): A command to process.

        Returns:
            bool: If this backend can process the command.
        """
        gate = cmd.gate

        # Metagates.
        if gate in (Measure, Allocate, Deallocate, Barrier):
            return True

        if has_negative_control(cmd):
            return False

        # CNOT gates.
        # NOTE: IonQ supports up to 7 control qubits
        num_ctrl_qubits = get_control_count(cmd)
        if 0 < num_ctrl_qubits <= 7:
            return isinstance(gate, (XGate,))

        # Gates witout control bits.
        if num_ctrl_qubits == 0:
            supported = isinstance(gate, SUPPORTED_GATES)
            supported_transpose = gate in (Sdag, Tdag)
            return supported or supported_transpose
        return False

    def _reset(self):
        """Reset this backend.

        .. NOTE::

            This sets ``_clear = True``, which will trigger state cleanup
            on the next call to ``_store``.
        """

        # Lastly, reset internal state for measured IDs and circuit body.
        self._circuit = []
        self._clear = True

    def _store(self, cmd):
        """Interpret the ProjectQ command as a circuit instruction and store it.

        Args:
            cmd (Command): A command to process.

        Raises:
            InvalidCommandError: If the command can not be interpreted.
            MidCircuitMeasurementError: If this command would result in a
                mid-circuit qubit measurement.
        """
        if self._clear:
            self._measured_ids = []
            self._probabilities = dict()
            self._clear = False

        # No-op/Meta gates.
        # NOTE: self.main_engine.mapper takes care qubit allocation/mapping.
        gate = cmd.gate
        if gate in (Allocate, Deallocate, Barrier):
            return

        # Create a measurement.
        if gate == Measure:
            logical_id = cmd.qubits[0][0].id
            for tag in cmd.tags:
                if isinstance(tag, LogicalQubitIDTag):
                    logical_id = tag.logical_qubit_id
                    break
            # Add the qubit id
            self._measured_ids.append(logical_id)
            return

        # Process the Command's gate type:
        gate_type = type(gate)
        gate_name = GATE_MAP.get(gate_type)
        # Daggered gates get special treatment.
        if isinstance(gate, DaggeredGate):
            gate_name = GATE_MAP[type(gate._gate)] + 'i'  # pylint: disable=protected-access

        # Unable to determine a gate mapping here, so raise out.
        if gate_name is None:
            raise InvalidCommandError('Invalid command: ' + str(cmd))

        # Now make sure there are no existing measurements on qubits involved
        #   in this operation.
        targets = [qb.id for qureg in cmd.qubits for qb in qureg]
        controls = [qb.id for qb in cmd.control_qubits]
        if len(self._measured_ids) > 0:

            # Check any qubits we are trying to operate on.
            gate_qubits = set(targets) | set(controls)

            # If any of them have already been measured...
            already_measured = gate_qubits & set(self._measured_ids)

            # Boom!
            if len(already_measured) > 0:
                err = (
                    'Mid-circuit measurement is not supported. '
                    'The following qubits have already been measured: {}.'.format(list(already_measured))
                )
                raise MidCircuitMeasurementError(err)

        # Initialize the gate dict:
        gate_dict = {
            'gate': gate_name,
            'targets': targets,
        }

        # Check if we have a rotation
        if isinstance(gate, (R, Rx, Ry, Rz, Rxx, Ryy, Rzz)):
            gate_dict['rotation'] = gate.angle

        # Set controls
        if len(controls) > 0:
            gate_dict['controls'] = controls

        self._circuit.append(gate_dict)

    def get_probability(self, state, qureg):
        """Shortcut to get a specific state's probability.

        Args:
            state (str): A state in bit-string format.
            qureg (Qureg): A ProjectQ Qureg object.

        Returns:
            float: The probability for the provided state.
        """
        if len(state) != len(qureg):
            raise ValueError('Desired state and register must be the same length!')

        probs = self.get_probabilities(qureg)
        return probs[state]

    def get_probabilities(self, qureg):
        """Given the provided qubit register, determine the probability of
        each possible outcome.

        .. NOTE::

            This method should only be called *after* a circuit has been
            run and its results are available.

        Args:
            qureg (Qureg): A ProjectQ Qureg object.

        Returns:
            dict: A dict mapping of states -> probability.
        """
        if len(self._probabilities) == 0:
            raise RuntimeError("Please, run the circuit first!")

        probability_dict = {}
        for state in self._probabilities:
            mapped_state = ['0'] * len(qureg)
            for i, qubit in enumerate(qureg):
                try:
                    meas_idx = self._measured_ids.index(qubit.id)
                except ValueError:
                    continue
                mapped_state[i] = state[meas_idx]
            probability = self._probabilities[state]
            mapped_state = "".join(mapped_state)
            probability_dict[mapped_state] = probability_dict.get(mapped_state, 0) + probability
        return probability_dict

    def _run(self):  # pylint: disable=too-many-locals
        """Run the circuit this object has built during engine execution."""
        # Nothing to do with an empty circuit.
        if len(self._circuit) == 0:
            return

        if self._retrieve_execution is None:
            qubit_mapping = self.main_engine.mapper.current_mapping
            measured_ids = self._measured_ids[:]
            info = {
                'circuit': self._circuit,
                'nq': len(qubit_mapping.keys()),
                'shots': self._num_runs,
                'meas_mapped': [qubit_mapping[qubit_id] for qubit_id in measured_ids],
                'meas_qubit_ids': measured_ids,
            }
            res = http_client.send(
                info,
                device=self.device,
                token=self._token,
                num_retries=self._num_retries,
                interval=self._interval,
                verbose=self._verbose,
            )
            if res is None:
                raise RuntimeError('Failed to submit job to the server!')
        else:
            res = http_client.retrieve(
                device=self.device,
                token=self._token,
                jobid=self._retrieve_execution,
                num_retries=self._num_retries,
                interval=self._interval,
                verbose=self._verbose,
            )
            if res is None:
                raise RuntimeError("Failed to retrieve job with id: '{}'!".format(self._retrieve_execution))
            self._measured_ids = measured_ids = res['meas_qubit_ids']

        # Determine random outcome from probable states.
        random_outcome = random.random()
        p_sum = 0.0
        measured = ""
        star = ""
        num_measured = len(measured_ids)
        probable_outcomes = res['output_probs']
        states = probable_outcomes.keys()
        self._probabilities = {}
        for idx, state_int in enumerate(states):
            state = _rearrange_result(int(state_int), num_measured)
            probability = probable_outcomes[state_int]
            p_sum += probability
            if p_sum >= random_outcome and measured == "" or (idx == len(states) - 1):
                measured = state
                star = "*"
            self._probabilities[state] = probability
            if self._verbose and probability > 0:  # pragma: no cover
                print(state + " with p = " + str(probability) + star)

        # Register measurement results
        for idx, qubit_id in enumerate(measured_ids):
            result = int(measured[idx])
            qubit_ref = WeakQubitRef(self.main_engine, qubit_id)
            self.main_engine.set_measurement_result(qubit_ref, result)

    def receive(self, command_list):
        """Receive a command list from the ProjectQ engine pipeline.

        If a given command is a "flush" operation, the pending circuit will be
        submitted to IonQ's API for processing.

        Args:
            command_list (list[Command]): A list of ProjectQ Command objects.
        """
        for cmd in command_list:
            if not isinstance(cmd.gate, FlushGate):
                self._store(cmd)
            else:
                # After that, the circuit is ready to be submitted.
                try:
                    self._run()
                finally:
                    # Make sure we always reset engine state so as not to leave
                    #    anything dirty atexit.
                    self._reset()


__all__ = ['IonQBackend']
