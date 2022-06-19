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

import numpy as np
from collections import Counter

from projectq.types import WeakQubitRef
from projectq.cengines import BasicEngine
from projectq.meta import LogicalQubitIDTag
from projectq.ops import (
    AllocateQubitGate,
    DeallocateQubitGate,
    FlushGate,
    MeasureGate
)

from ._azure_quantum_client import send, retrieve
from ._util import (
    IONQ_PROVIDER_ID,
    QUANTINUUM_PROVIDER_ID,
    is_available_ionq,
    is_available_quantinuum,
    to_json,
    to_qasm,
    rearrange_result
)

from ._exceptions import AzureQuantumTargetNotFoundError

try:
    from azure.quantum import Workspace
    from azure.quantum.target import Target, IonQ, Quantinuum
    from azure.quantum.target.target_factory import TargetFactory
except ImportError:  # pragma: no cover
    raise ImportError(
        "Missing optional 'azure-quantum' dependencies. To install run: pip install projectq[azure-quantum]"
    )


class AzureQuantumBackend(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """Backend for building circuits and submitting them to the Azure Quantum."""

    DEFAULT_TARGETS = {
        IONQ_PROVIDER_ID: IonQ,
        QUANTINUUM_PROVIDER_ID: Quantinuum
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
                ```quantinuum.hqs-lt-s1-apival``` used for Quantinuum backend. Defaults to False.
            num_runs (int, optional): Number of times to run circuits. Defaults to 100.
            verbose (bool, optional): If True, print statistics after job results have been collected. Defaults to
                False.
            workspace (Workspace, optional): Azure Quantum workspace. If workspace is None, kwargs will be used to
                create Workspace object.
            target_name (str, optional): Target to run jobs on. Defaults to ```ionq.simulator```.
            num_retries (int, optional): Number of times to retry fetching a job after it has been submitted. Defaults
                to 100.
            interval (int, optional): Number of seconds to wait in between result fetch retries. Defaults to 1.
            retrieve_execution (str, optional): An Azure Quantum Job ID. If provided, a job result with this ID will be
                fetched. Defaults to None.
        """
        super().__init__()

        if target_name in IonQ.target_names:
            self._provider_id = IONQ_PROVIDER_ID
        elif target_name in Quantinuum.target_names:
            self._provider_id = QUANTINUUM_PROVIDER_ID
        else:  # pragma: no cover
            raise AzureQuantumTargetNotFoundError('Target {0} does not exit.'.format(target_name))

        if use_hardware:
            self._target_name = target_name
        else:
            if self._provider_id == IONQ_PROVIDER_ID:
                self._target_name = 'ionq.simulator'
            elif self._provider_id == QUANTINUUM_PROVIDER_ID:
                if target_name == 'quantinuum.hqs-lt-s1':
                    self._target_name = 'quantinuum.hqs-lt-s1-apival'
                else:
                    self._target_name = target_name

        if workspace is None:
            workspace = Workspace(**kwargs)

        workspace.append_user_agent('projectq')
        self._workspace = workspace

        self._num_runs = num_runs
        self._verbose = verbose
        self._num_retries = num_retries
        self._interval = interval
        self._retrieve_execution = retrieve_execution
        self._circuit = None
        self._measured_ids = []
        self._probabilities = {}
        self._clear = True

    def _reset(self):
        """
        Reset this backend.

        Note:
            This sets ``_clear = True``, which will trigger state cleanup on the next call to ``_store``.
        """
        # Lastly, reset internal state for measured IDs and circuit body.
        self._circuit = None
        self._clear = True

    def _store(self, cmd):
        """
        Temporarily store the command cmd.

        Translates the command and stores it in a local variable (self._cmds).

        Args:
            cmd: Command to store
        """

        if self._clear:
            self._probabilities = {}
            self._clear = False
            self._circuit = None

        gate = cmd.gate

        # No-op/Meta gates
        if isinstance(gate, (AllocateQubitGate, DeallocateQubitGate)):
            return

        # Measurement
        if isinstance(gate, MeasureGate):
            logical_id = None
            for tag in cmd.tags:
                if isinstance(tag, LogicalQubitIDTag):
                    logical_id = tag.logical_qubit_id
                    break

            if logical_id is None:
                raise RuntimeError('No LogicalQubitIDTag found in command!')

            self._measured_ids.append(logical_id)
            return

        if self._provider_id == IONQ_PROVIDER_ID:
            if not self._circuit:
                self._circuit = []

            json_cmd = to_json(cmd)
            if json_cmd:
                self._circuit.append(json_cmd)

        elif self._provider_id == QUANTINUUM_PROVIDER_ID:
            if not self._circuit:
                self._circuit = ''

            qasm_cmd = to_qasm(cmd)
            if qasm_cmd:
                self._circuit += '\n{0}'.format(qasm_cmd)

    def is_available(self, cmd):
        """
        Test if this backend is available to process the provided command.

        Args:
            cmd (Command): A command to process.

        Returns:
            bool: If this backend can process the command.
        """
        if self._provider_id == IONQ_PROVIDER_ID:
            return is_available_ionq(cmd)
        elif self._provider_id == QUANTINUUM_PROVIDER_ID:
            return is_available_quantinuum(cmd)

        return False

    @property
    def _target_factory(self):
        target_factory = TargetFactory(
            base_cls=Target,  # noqa
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
        """Current availability for given target."""
        return self._target.current_availability

    @property
    def average_queue_time(self):
        """Average queue time for given target."""
        return self._target.average_queue_time

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

        if self._provider_id == IONQ_PROVIDER_ID:
            return {
                "qubits": qubits,
                "circuit": self._circuit
            }
        elif self._provider_id == QUANTINUUM_PROVIDER_ID:
            measurement_gates = ""

            for measured_id in self._measured_ids:
                qb_loc = self.main_engine.mapper.current_mapping[measured_id]
                measurement_gates += "measure q[{0}] -> c[{0}];\n".format(qb_loc)

            return f"OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[{qubits}];\ncreg c[{qubits}];" \
                   f"{self._circuit}\n{measurement_gates}"

    @property
    def _metadata(self):
        qubit_mapping = self.main_engine.mapper.current_mapping
        num_qubits = len(qubit_mapping.keys())
        meas_map = [qubit_mapping[qubit_id] for qubit_id in self._measured_ids]

        return {
            "num_qubits": num_qubits,
            "meas_map": meas_map
        }

    def estimate_cost(self, **kwargs):
        """Estimate cost for the circuit this object has built during engine execution."""
        return self._target.estimate_cost(
            circuit=self._input_data,  # noqa
            num_shots=self._num_runs,  # noqa
            **kwargs
        )  # noqa

    def _run(self):  # pylint: disable=too-many-locals
        """Run the circuit this object has built during engine execution."""
        # Nothing to do with an empty circuit.
        if not self._circuit:
            return

        if self._retrieve_execution is None:
            res = send(
                input_data=self._input_data,
                metadata=self._metadata,
                num_shots=self._num_runs,
                target=self._target,
                num_retries=self._num_retries,
                interval=self._interval,
                verbose=self._verbose
            )

            if res is None:
                raise RuntimeError('Failed to submit job to the Azure Quantum!')
        else:
            res = retrieve(
                job_id=self._retrieve_execution,
                target=self._target,
                num_retries=self._num_retries,
                interval=self._interval,
                verbose=self._verbose
            )

            if res is None:
                raise RuntimeError(
                    "Failed to retrieve job from Azure Quantum with job id: '{}'!".format(self._retrieve_execution)
                )

        if self._provider_id == IONQ_PROVIDER_ID:
            self._probabilities = {
                rearrange_result(int(k), len(self._measured_ids)): v for k, v in res["histogram"].items()
            }
        elif self._provider_id == QUANTINUUM_PROVIDER_ID:
            histogram = Counter(res["c"])
            self._probabilities = {
                k: v / self._num_runs for k, v in histogram.items()
            }

        # Set a single measurement result
        bitstring = np.random.choice(list(self._probabilities.keys()), p=list(self._probabilities.values()))
        for qid in self._measured_ids:
            qubit_ref = WeakQubitRef(self.main_engine, qid)
            self.main_engine.set_measurement_result(qubit_ref, bitstring[qid])

    def receive(self, command_list):
        """Receive a command list from the ProjectQ engine pipeline.

        If a given command is a "flush" operation, the pending circuit will be
        submitted to Azure Quantum for processing.

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