#   Copyright 2022 ProjectQ-Framework (www.projectq.ch)
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

"""Tests for projectq.backends._azure._azure_quantum.py."""

from unittest import mock

import pytest

from projectq.cengines import BasicMapperEngine, MainEngine
from projectq.ops import CX, All, H, Measure

_has_azure_quantum = True
try:
    from azure.quantum import Workspace

    import projectq.backends._azure._azure_quantum
    from projectq.backends import AzureQuantumBackend
    from projectq.backends._azure._exceptions import AzureQuantumTargetNotFoundError
except ImportError:
    _has_azure_quantum = False

has_azure_quantum = pytest.mark.skipif(not _has_azure_quantum, reason="azure quantum package is not installed")

ZERO_GUID = '00000000-0000-0000-0000-000000000000'


def mock_target_status(target_id, current_availability, average_queue_time):
    target_status = mock.MagicMock()

    target_status.id = target_id
    target_status.current_availability = current_availability
    target_status.average_queue_time = average_queue_time

    return target_status


def mock_provider_statuses():
    ionq_provider_status = mock.MagicMock()
    ionq_provider_status.id = 'ionq'
    ionq_provider_status.targets = [
        mock_target_status(target_id='ionq.simulator', current_availability='Available', average_queue_time=1000),
        mock_target_status(target_id='ionq.qpu', current_availability='Available', average_queue_time=2000),
    ]

    quantinuum_provider_status = mock.MagicMock()
    quantinuum_provider_status.id = 'quantinuum'
    quantinuum_provider_status.targets = [
        mock_target_status(
            target_id='quantinuum.hqs-lt-s1-apival', current_availability='Available', average_queue_time=3000
        ),
        mock_target_status(
            target_id='quantinuum.hqs-lt-s1-sim', current_availability='Available', average_queue_time=4000
        ),
        mock_target_status(target_id='quantinuum.hqs-lt-s1', current_availability='Degraded', average_queue_time=5000),
    ]

    return [ionq_provider_status, quantinuum_provider_status]


def mock_workspace():
    workspace = Workspace(
        subscription_id=ZERO_GUID, resource_group='testResourceGroup', name='testWorkspace', location='East US'
    )

    workspace.append_user_agent('projectq')

    workspace._client = mock.MagicMock()
    workspace._client.providers = mock.MagicMock()
    workspace._client.providers.get_status.return_value = mock_provider_statuses()

    return workspace


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id, expected_target_name",
    [
        (False, 'ionq.simulator', 'ionq', 'ionq.simulator'),
        (True, 'ionq.qpu', 'ionq', 'ionq.qpu'),
        (False, 'ionq.qpu', 'ionq', 'ionq.simulator'),
    ],
)
def test_azure_quantum_ionq_target(use_hardware, target_name, provider_id, expected_target_name):
    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=use_hardware, target_name=target_name, workspace=workspace)

    assert backend._target_name == expected_target_name


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id, expected_target_name",
    [
        (False, 'quantinuum.hqs-lt-s1-apival', 'quantinuum', 'quantinuum.hqs-lt-s1-apival'),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum', 'quantinuum.hqs-lt-s1-sim'),
        (True, 'quantinuum.hqs-lt-s1', 'quantinuum', 'quantinuum.hqs-lt-s1'),
        (False, 'quantinuum.hqs-lt-s1', 'quantinuum', 'quantinuum.hqs-lt-s1-apival'),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum', 'quantinuum.hqs-lt-s1-sim'),
    ],
)
def test_azure_quantum_quantinuum_target(use_hardware, target_name, provider_id, expected_target_name):
    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=use_hardware, target_name=target_name, workspace=workspace)

    assert backend._target_name == expected_target_name


@has_azure_quantum
def test_azure_quantum_invalid_target():
    workspace = mock_workspace()

    try:
        AzureQuantumBackend(use_hardware=False, target_name='invalid-target', workspace=workspace)
        assert False
    except AzureQuantumTargetNotFoundError:
        assert True


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id, current_availability",
    [
        (False, 'ionq.simulator', 'ionq', 'Available'),
        (True, 'ionq.qpu', 'ionq', 'Available'),
        (False, 'quantinuum.hqs-lt-s1-apival', 'quantinuum', 'Available'),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum', 'Available'),
        (True, 'quantinuum.hqs-lt-s1', 'quantinuum', 'Degraded'),
    ],
)
def test_current_availability(use_hardware, target_name, provider_id, current_availability):
    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=use_hardware, target_name=target_name, workspace=workspace)

    assert backend.current_availability == current_availability


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id, average_queue_time",
    [
        (False, 'ionq.simulator', 'ionq', 1000),
        (True, 'ionq.qpu', 'ionq', 2000),
        (False, 'quantinuum.hqs-lt-s1-apival', 'quantinuum', 3000),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum', 4000),
        (True, 'quantinuum.hqs-lt-s1', 'quantinuum', 5000),
    ],
)
def test_average_queue_time(use_hardware, target_name, provider_id, average_queue_time):
    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=use_hardware, target_name=target_name, workspace=workspace)

    assert backend.average_queue_time == average_queue_time


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id",
    [(False, 'ionq.simulator', 'ionq'), (True, 'ionq.qpu', 'ionq')],
)
def test_run_ionq_get_probabilities(use_hardware, target_name, provider_id):
    projectq.backends._azure._azure_quantum.send = mock.MagicMock(
        return_value={'histogram': {'0': 0.5, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.5}}
    )

    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=use_hardware, target_name=target_name, workspace=workspace, verbose=True)

    mapper = BasicMapperEngine()
    max_qubits = 3

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    main_engine.flush()

    result = backend.get_probabilities(circuit)

    assert len(result) == 8
    assert result['000'] == pytest.approx(0.5)
    assert result['001'] == 0.0
    assert result['010'] == 0.0
    assert result['011'] == 0.0
    assert result['100'] == 0.0
    assert result['101'] == 0.0
    assert result['110'] == 0.0
    assert result['111'] == pytest.approx(0.5)


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id",
    [
        (False, 'quantinuum.hqs-lt-s1-apival', 'quantinuum'),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum'),
        (True, 'quantinuum.hqs-lt-s1', 'quantinuum'),
    ],
)
def test_run_quantinuum_get_probabilities(use_hardware, target_name, provider_id):
    projectq.backends._azure._azure_quantum.send = mock.MagicMock(
        return_value={
            'c': [
                '000',
                '000',
                '000',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '111',
                '000',
                '000',
                '000',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '000',
                '000',
                '000',
                '000',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
            ]
        }
    )

    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=use_hardware, target_name=target_name, workspace=workspace, verbose=True)

    mapper = BasicMapperEngine()
    max_qubits = 3

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    main_engine.flush()

    result = backend.get_probabilities(circuit)

    assert len(result) == 2
    assert result['000'] == pytest.approx(0.41)
    assert result['111'] == pytest.approx(0.59)


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id",
    [(False, 'ionq.simulator', 'ionq'), (True, 'ionq.qpu', 'ionq')],
)
def test_run_ionq_get_probability(use_hardware, target_name, provider_id):
    projectq.backends._azure._azure_quantum.send = mock.MagicMock(
        return_value={'histogram': {'0': 0.5, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.5}}
    )

    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=use_hardware, target_name=target_name, workspace=workspace, verbose=True)

    mapper = BasicMapperEngine()
    max_qubits = 3

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    main_engine.flush()

    assert backend.get_probability('000', circuit) == pytest.approx(0.5)
    assert backend.get_probability('001', circuit) == 0.0
    assert backend.get_probability('010', circuit) == 0.0
    assert backend.get_probability('011', circuit) == 0.0
    assert backend.get_probability('100', circuit) == 0.0
    assert backend.get_probability('101', circuit) == 0.0
    assert backend.get_probability('110', circuit) == 0.0
    assert backend.get_probability('111', circuit) == pytest.approx(0.5)


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id",
    [
        (False, 'quantinuum.hqs-lt-s1-apival', 'quantinuum'),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum'),
        (True, 'quantinuum.hqs-lt-s1', 'quantinuum'),
    ],
)
def test_run_quantinuum_get_probability(use_hardware, target_name, provider_id):
    projectq.backends._azure._azure_quantum.send = mock.MagicMock(
        return_value={
            'c': [
                '000',
                '000',
                '000',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '111',
                '000',
                '000',
                '000',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '000',
                '000',
                '000',
                '000',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
            ]
        }
    )

    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=use_hardware, target_name=target_name, workspace=workspace, verbose=True)

    mapper = BasicMapperEngine()
    max_qubits = 3

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    main_engine.flush()

    assert backend.get_probability('000', circuit) == pytest.approx(0.41)
    assert backend.get_probability('001', circuit) == 0.0
    assert backend.get_probability('010', circuit) == 0.0
    assert backend.get_probability('011', circuit) == 0.0
    assert backend.get_probability('100', circuit) == 0.0
    assert backend.get_probability('101', circuit) == 0.0
    assert backend.get_probability('110', circuit) == 0.0
    assert backend.get_probability('111', circuit) == pytest.approx(0.59)


@has_azure_quantum
def test_run_no_circuit():
    workspace = mock_workspace()

    backend = AzureQuantumBackend(use_hardware=False, target_name='ionq.simulator', workspace=workspace, verbose=True)

    mapper = BasicMapperEngine()
    max_qubits = 3

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    circuit = main_engine.allocate_qureg(3)

    main_engine.flush()

    try:
        _ = backend.get_probabilities(circuit)

        assert False, 'Expected RuntimeError, run without any circuit'
    except RuntimeError:
        assert True


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id",
    [(False, 'ionq.simulator', 'ionq'), (True, 'ionq.qpu', 'ionq')],
)
def test_run_ionq_retrieve_execution(use_hardware, target_name, provider_id):
    projectq.backends._azure._azure_quantum.retrieve = mock.MagicMock(
        return_value={'histogram': {'0': 0.5, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.5}}
    )

    workspace = mock_workspace()

    backend = AzureQuantumBackend(
        use_hardware=use_hardware,
        target_name=target_name,
        workspace=workspace,
        retrieve_execution=ZERO_GUID,
        verbose=True,
    )

    mapper = BasicMapperEngine()
    max_qubits = 3

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    main_engine.flush()

    result = backend.get_probabilities(circuit)

    assert len(result) == 8
    assert result['000'] == pytest.approx(0.5)
    assert result['001'] == 0.0
    assert result['010'] == 0.0
    assert result['011'] == 0.0
    assert result['100'] == 0.0
    assert result['101'] == 0.0
    assert result['110'] == 0.0
    assert result['111'] == pytest.approx(0.5)


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id",
    [
        (False, 'quantinuum.hqs-lt-s1-apival', 'quantinuum'),
        (False, 'quantinuum.hqs-lt-s1-sim', 'quantinuum'),
        (True, 'quantinuum.hqs-lt-s1', 'quantinuum'),
    ],
)
def test_run_quantinuum_retrieve_execution(use_hardware, target_name, provider_id):
    projectq.backends._azure._azure_quantum.retrieve = mock.MagicMock(
        return_value={
            'c': [
                '000',
                '000',
                '000',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '111',
                '000',
                '000',
                '000',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '111',
                '000',
                '000',
                '000',
                '000',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '000',
                '111',
                '000',
                '111',
                '111',
                '111',
                '000',
                '111',
                '111',
                '000',
            ]
        }
    )

    workspace = mock_workspace()

    backend = AzureQuantumBackend(
        use_hardware=use_hardware,
        target_name=target_name,
        workspace=workspace,
        retrieve_execution=ZERO_GUID,
        verbose=True,
    )

    mapper = BasicMapperEngine()
    max_qubits = 3

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i

    mapper.current_mapping = mapping

    main_engine = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    main_engine.flush()

    result = backend.get_probabilities(circuit)

    assert len(result) == 2
    assert result['000'] == pytest.approx(0.41)
    assert result['111'] == pytest.approx(0.59)
