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

"""Back-end to run quantum programs using Azure Quantum."""

import math
import numpy as np

from projectq.types import WeakQubitRef
from projectq.cengines import BasicEngine
from projectq.meta import LogicalQubitIDTag, get_control_count, has_negative_control
from projectq.ops import (
    Allocate,
    Barrier,
    DaggeredGate,
    Deallocate,
    FlushGate,
    H,
    HGate,
    NOT,
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

from ._azure_quantum_client import send, retrieve
from ._exceptions import AzureQuantumTargetNotFoundError

from .._exceptions import InvalidCommandError, MidCircuitMeasurementError

try:
    from azure.quantum import Workspace
    from azure.quantum.target import Target, IonQ, Honeywell
    from azure.quantum.target.target_factory import TargetFactory
except ImportError:  # pragma: no cover
    raise ImportError(
        "Missing optional 'azure-quantum' dependencies. To install run: pip install projectq[azure-quantum]"
    )

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


class AzureQuantumBackend(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """Backend for building circuits and submitting them to the Azure Quantum."""

    DEFAULT_TARGETS = {
        "ionq": IonQ,
        "honeywell": Honeywell
    }

    def __init__(
        self,
        use_hardware=False,
        num_runs=100,
        verbose=False,
        workspace=None,
        target_name='ionq.simulator',
        num_retries=100,
        interval=1,
        retrieve_execution=None,
        **kwargs
    ):  # pylint: disable=too-many-arguments
        """
        Initialize an Azure Quantum Backend object.

        Args:
            use_hardware (bool, optional): Whether or not to use real hardware or just a simulator. If False,
            regardless of the value of ```device```, ```ionq.simulator``` used for ionq provider and
                ```honeywell.hqs-lt-s1-apival``` used for honeywell backend. Defaults to False.
            num_runs (int, optional): Number of times to run circuits. Defaults to 100.
            verbose (bool, optional): If True, print statistics after job results have been collected. Defaults to
                False.
            workspace (Workspace, optional): Azure Quantum workspace. If workspace is None, kwargs will be used to
                create Workspace object.
            target_name (str, optional): Target to run jobs on. Defaults to ```ionq.simulator```.
            num_retries (int, optional): Number of times to retry fetching a job after it has been submitted. Defaults
                to 100.
            interval (int, optional): Number of seconds to wait inbetween result fetch retries. Defaults to 1.
            retrieve_execution (str, optional): An IonQ API Job ID.  If provided, a job with this ID will be
                fetched. Defaults to None.
        """
        super().__init__()

        if target_name in IonQ.target_names:
            self._provider_id = 'ionq'
        elif target_name in Honeywell.target_names:
            self._provider_id = 'honeywell'
        else:  # pragma: no cover
            raise AzureQuantumTargetNotFoundError('Target {0} does not exit.'.format(target_name))

        if use_hardware:
            self._target_name = target_name
        else:
            if self._provider_id == 'ionq':
                self._target_name = 'ionq.simulator'
            elif self._provider_id == 'honeywell':
                self._target_name = 'honeywell.hqs-lt-s1-apival'

        if workspace is None:
            workspace = Workspace(**kwargs)

        workspace.append_user_agent('projectq')
        self._workspace = workspace

        self._num_runs = num_runs
        self._verbose = verbose
        self._num_retries = num_retries
        self._interval = interval
        self._retrieve_execution = retrieve_execution
        self._circuit = []
        self._measured_ids = []
        self._probabilities = {}
        self._clear = True
        self._allocated_qubits = set()
        self.qasm = ""
        self._json = []

    def _reset(self):
        """
        Reset this backend.

        Note:
            This sets ``_clear = True``, which will trigger state cleanup on the next call to ``_store``.
        """
        # Lastly, reset internal state for measured IDs and circuit body.
        self._circuit = []
        self._clear = True

    def _store_ionq_json(self, cmd):
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
            self._probabilities = {}
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

    def _store_qasm(self, cmd):  # pylint: disable=too-many-branches,too-many-statements
        """
        Temporarily store the command cmd.

        Translates the command and stores it in a local variable (self._cmds).

        Args:
            cmd: Command to store
        """
        if self.main_engine.mapper is None:
            raise RuntimeError('No mapper is present in the compiler engine list!')

        if self._clear:
            self._probabilities = {}
            self._clear = False
            self.qasm = ""
            self._json = []
            self._allocated_qubits = set()

        gate = cmd.gate
        if gate == Allocate:
            self._allocated_qubits.add(cmd.qubits[0][0].id)
            return

        if gate == Deallocate:
            return

        if gate == Measure:
            logical_id = None
            for tag in cmd.tags:
                if isinstance(tag, LogicalQubitIDTag):
                    logical_id = tag.logical_qubit_id
                    break
            if logical_id is None:
                raise RuntimeError('No LogicalQubitIDTag found in command!')
            self._measured_ids += [logical_id]
        elif gate == NOT and get_control_count(cmd) == 1:
            ctrl_pos = cmd.control_qubits[0].id
            qb_pos = cmd.qubits[0][0].id
            self.qasm += "\ncx q[{}], q[{}];".format(ctrl_pos, qb_pos)
            self._json.append({'qubits': [ctrl_pos, qb_pos], 'name': 'cx'})
        elif gate == Barrier:
            qb_pos = [qb.id for qr in cmd.qubits for qb in qr]
            self.qasm += "\nbarrier "
            qb_str = ""
            for pos in qb_pos:
                qb_str += "q[{}], ".format(pos)
            self.qasm += qb_str[:-2] + ";"
            self._json.append({'qubits': qb_pos, 'name': 'barrier'})
        elif isinstance(gate, (Rx, Ry, Rz)):
            qb_pos = cmd.qubits[0][0].id
            u_strs = {'Rx': 'u3({}, -pi/2, pi/2)', 'Ry': 'u3({}, 0, 0)', 'Rz': 'u1({})'}
            u_name = {'Rx': 'u3', 'Ry': 'u3', 'Rz': 'u1'}
            u_angle = {
                'Rx': [gate.angle, -math.pi / 2, math.pi / 2],
                'Ry': [gate.angle, 0, 0],
                'Rz': [gate.angle],
            }
            gate_qasm = u_strs[str(gate)[0:2]].format(gate.angle)
            gate_name = u_name[str(gate)[0:2]]
            params = u_angle[str(gate)[0:2]]
            self.qasm += "\n{} q[{}];".format(gate_qasm, qb_pos)
            self._json.append({'qubits': [qb_pos], 'name': gate_name, 'params': params})
        elif gate == H:
            qb_pos = cmd.qubits[0][0].id
            self.qasm += "\nu2(0,pi/2) q[{}];".format(qb_pos)
            self._json.append({'qubits': [qb_pos], 'name': 'u2', 'params': [0, 3.141592653589793]})
        else:
            raise InvalidCommandError(
                'Command not authorized. You should run the circuit with the appropriate ibm setup.'
            )

    def _store(self, cmd):
        self._store_ionq_json(cmd)
        self._store_qasm(cmd)
        # if self._provider_id == 'ionq':
        #     self._store_ionq_json(cmd)
        # elif self._provider_id == 'honeywell':
        #     self._store_qasm(cmd)

    def is_available(self, cmd):
        """
        Test if this backend is available to process the provided command.

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

    @property
    def _target_factory(self):
        target_factory = TargetFactory(
            base_cls=Target,
            workspace=self._workspace,
            default_targets=AzureQuantumBackend.DEFAULT_TARGETS
        )

        return target_factory

    @property
    def _target(self):
        target = self._target_factory.get_targets(
            name=self._target_name,
            provider_id=self._provider_id
        )

        if type(target) is list and len(target) == 0:  # pragma: no cover
            raise AzureQuantumTargetNotFoundError(
                'Target {} is not available on workspace {}.'.format(
                    self._target_name, self._workspace.name)
            )

        return target

    @property
    def current_availability(self):
        """Current availability for given provider."""
        return self._target.current_availability

    @property
    def average_queue_time(self):
        """Average queue time for given target."""
        return self._target.average_queue_time

    def estimate_cost(self):
        """Estimate cost for the circuit this object has built during engine execution."""
        input_data = {
            'qubits': len(self._measured_ids),
            'circuit': self._circuit
        }

        return self._target.estimate_cost(
            circuit=input_data,
            num_shots=self._num_runs
        )

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
        """
        Given the provided qubit register, determine the probability of each possible outcome.

        Note:
            This method should only be called *after* a circuit has been run and its results are available.

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

    @property
    def _input_data(self):
        qubit_mapping = self.main_engine.mapper.current_mapping
        qubits = len(qubit_mapping.keys())

        if self._provider_id == 'ionq':
            return {
                "qubits": qubits,
                "circuit": self._circuit,
            }
        elif self._provider_id == 'honeywell':
            for measured_id in self._measured_ids:
                qb_loc = self.main_engine.mapper.current_mapping[measured_id]
                self.qasm += "\nmeasure q[{0}] -> c[{0}];".format(qb_loc)

            self.qasm = self.qasm.replace("u2(0,pi/2)", "h")
            return f"OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[{qubits}];\ncreg c[{qubits}];{self.qasm}\n"

    @property
    def _metadata(self):
        qubit_mapping = self.main_engine.mapper.current_mapping
        num_qubits = len(qubit_mapping.keys())
        meas_map = [qubit_mapping[qubit_id] for qubit_id in self._measured_ids]

        return {
            "num_qubits": num_qubits,
            "meas_map": meas_map
        }

    def _run(self):  # pylint: disable=too-many-locals
        """Run the circuit this object has built during engine execution."""
        # Nothing to do with an empty circuit.
        if len(self._circuit) == 0:
            return

        if self._retrieve_execution is None:
            res = send(
                input_data=self._input_data,
                metadata=self._metadata,
                num_shots=self._num_runs,
                target=self._target,
                provider=self._provider_id,
                num_retries=self._num_retries,
                interval=self._interval,
                verbose=self._verbose
            )

            if res is None:
                raise RuntimeError('Failed to submit job to the Azure Quantum!')
        else:
            res = retrieve(
                target=self._target,
                job_id=self._retrieve_execution,
                num_retries=self._num_retries,
                interval=self._interval,
                verbose=self._verbose
            )
            if res is None:
                raise RuntimeError(
                    "Failed to retrieve job from Azure Quantum with id: '{}'!".format(self._retrieve_execution)
                )

        self._probabilities = {
            _rearrange_result(int(k), len(self._measured_ids)): v for k, v in res["histogram"].items()
        }

        # Set a single measurement result
        bitstring = np.random.choice(list(self._probabilities.keys()), p=list(self._probabilities.values()))
        for qid in self._measured_ids:
            qubit_ref = WeakQubitRef(self.main_engine, qid)
            self.main_engine.set_measurement_result(qubit_ref, bitstring[qid])

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


__all__ = ['AzureQuantumBackend']
