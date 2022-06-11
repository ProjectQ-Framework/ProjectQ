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

from unittest import mock
from azure.quantum import Workspace
from azure.identity import ClientSecretCredential

from projectq import MainEngine
from projectq.ops import H, CX, All, Measure
from projectq.cengines import BasicMapperEngine
from projectq.backends import AzureQuantumBackend
from projectq.backends._azure._exceptions import AzureQuantumTargetNotFoundError

import pytest


ZERO_GUID = '00000000-0000-0000-0000-000000000000'


def create_workspace():
    return mock.MagicMock()


@pytest.mark.parametrize(
    "use_hardware, target_name, expected_provider_id, expected_target_name",
    [
        (False, 'ionq.simulator', 'ionq', 'ionq.simulator'),
        (True, 'ionq.qpu', 'ionq', 'ionq.qpu'),
        (False, 'ionq.qpu', 'ionq', 'ionq.simulator')
    ],
)
def test_azure_quantum_ionq_target(use_hardware, target_name, expected_provider_id, expected_target_name):
    workspace = create_workspace()
    backend = AzureQuantumBackend(
        use_hardware=use_hardware,
        target_name=target_name,
        workspace=workspace
    )

    assert backend._provider_id == expected_provider_id
    assert backend._target_name == expected_target_name


@pytest.mark.parametrize(
    "use_hardware, target_name, expected_provider_id, expected_target_name",
    [
        (False, 'quantinuum.hqs-lt-s1-apival', 'quantinuum', 'quantinuum.hqs-lt-s1-apival'),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum', 'quantinuum.hqs-lt-s1-sim'),
        (True, 'quantinuum.hqs-lt-s1', 'quantinuum', 'quantinuum.hqs-lt-s1'),
        (False, 'quantinuum.hqs-lt-s1', 'quantinuum', 'quantinuum.hqs-lt-s1-apival'),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum', 'quantinuum.hqs-lt-s1-sim')
    ],
)
def test_azure_quantum_quantinuum_target(use_hardware, target_name, expected_provider_id, expected_target_name):
    workspace = create_workspace()
    backend = AzureQuantumBackend(
        use_hardware=use_hardware,
        target_name=target_name,
        workspace=workspace
    )

    assert backend._provider_id == expected_provider_id
    assert backend._target_name == expected_target_name


def test_azure_quantum_invalid_target():
    workspace = create_workspace()

    try:
        AzureQuantumBackend(
            use_hardware=False,
            target_name='invalid-target',
            workspace=workspace
        )
        assert False
    except AzureQuantumTargetNotFoundError:
        assert True


@pytest.mark.parametrize(
    "use_hardware, target_name, expected_result",
    [
        (False, 'ionq.simulator', 1.0),
        (True, 'ionq.qpu', 10.0),
        (False, 'quantinuum.hqs-lt-s1-apival', 1.0),
        (False, 'quantinuum.hqs-lt-s1-sim', 1.0),
        (True, 'quantinuum.hqs-lt-s1', 10.0),
    ],
)
def test_estimate_cost(use_hardware, target_name, expected_result):
    workspace = create_workspace()
    backend = AzureQuantumBackend(
        use_hardware=use_hardware,
        target_name=target_name,
        workspace=workspace
    )

    # TODO:
    assert True


@pytest.mark.parametrize(
    "use_hardware, target_name",
    [
        (False, 'ionq.simulator'),
        (True, 'ionq.qpu')
    ],
)
def test_run_ionq(use_hardware, target_name):
    # mock send method from quantum client
    mock_send = mock.patch('projectq.backends._azure._util.send')
    mock_send.return_value = {
        'histogram': {
            '0': 0.125,
            '1': 0.125,
            '2': 0.125,
            '3': 0.125,
            '4': 0.125,
            '5': 0.125,
            '6': 0.125,
            '7': 0.125
        }
    }

    workspace = create_workspace()
    backend = AzureQuantumBackend(
        use_hardware=use_hardware,
        target_name=target_name,
        workspace=workspace,
        verbose=True
    )

    mapper = BasicMapperEngine()
    max_qubits = 2

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(
        backend=backend,
        engine_list=[mapper]
    )

    circuit = main_engine.allocate_qureg(2)
    q0, q1 = circuit

    H | q0
    CX | (q0, q1)
    All(Measure) | circuit

    main_engine.flush()

    result = backend.get_probabilities(circuit)
    assert result == {
        '000': 0.125,
        '100': 0.125,
        '010': 0.125,
        '110': 0.125,
        '001': 0.125,
        '101': 0.125,
        '011': 0.125,
        '111': 0.125
    }


@pytest.mark.parametrize(
    "use_hardware, target_name",
    [
        (False, 'quantinuum.hqs-lt-s1-apival'),
        (False, 'quantinuum.hqs-lt-s1-sim'),
        (True, 'quantinuum.hqs-lt-s1'),
    ],
)
def test_run_quantinuum(use_hardware, target_name):
    # mock send method from quantum client
    mock_send = mock.patch('projectq.backends._azure._util.send')
    mock_send.return_value = {
        'c': ['010', '100', '110', '000', '101', '111', '000', '100', '000', '110', '111', '100', '100', '000', '101',
              '110', '111', '011', '101', '100', '001', '110', '001', '001', '100', '011', '110', '000', '101', '101',
              '010', '100', '110', '111', '010', '000', '010', '110', '000', '110', '001', '100', '110', '011', '010',
              '111', '100', '110', '100', '100', '011', '000', '001', '101', '000', '011', '111', '101', '101', '001',
              '011', '110', '001', '010', '001', '110', '101', '000', '010', '001', '011', '100', '110', '100', '110',
              '101', '110', '111', '110', '001', '011', '101', '111', '011', '100', '111', '100', '001', '111', '111',
              '100', '100', '110', '101', '100', '110', '100', '000', '011', '000']
    }

    workspace = create_workspace()
    backend = AzureQuantumBackend(
        use_hardware=use_hardware,
        target_name=target_name,
        workspace=workspace,
        verbose=True
    )

    mapper = BasicMapperEngine()
    max_qubits = 2

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(
        backend=backend,
        engine_list=[mapper]
    )

    circuit = main_engine.allocate_qureg(2)
    q0, q1 = circuit

    H | q0
    CX | (q0, q1)
    All(Measure) | circuit

    main_engine.flush()

    result = backend.get_probabilities(circuit)
    assert result == {
        '010': 0.07,
        '100': 0.19,
        '110': 0.18,
        '000': 0.12,
        '101': 0.12,
        '111': 0.11,
        '011': 0.1,
        '001': 0.11
    }


@pytest.mark.parametrize(
    "use_hardware, target_name",
    [
        (False, 'ionq.simulator'),
        (True, 'ionq.qpu')
    ],
)
def test_run_ionq_retrieve_execution(use_hardware, target_name):
    assert True


@pytest.mark.parametrize(
    "use_hardware, target_name",
    [
        (False, 'quantinuum.hqs-lt-s1-apival'),
        (False, 'quantinuum.hqs-lt-s1-sim'),
        (True, 'quantinuum.hqs-lt-s1'),
    ],
)
def test_run_quantinuum_retrieve_execution(use_hardware, target_name):
    assert True
