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
from projectq.ops import CX, All, Command, H, Measure
from projectq.types import WeakQubitRef

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


def mock_target(target_id, current_availability, average_queue_time):
    target = mock.MagicMock()

    estimate_cost = mock.Mock()
    estimate_cost.estimated_total = 10

    target.id = target_id
    target.current_availability = current_availability
    target.average_queue_time = average_queue_time
    target.estimate_cost = mock.MagicMock(return_value=estimate_cost)

    return target


def mock_providers():
    ionq_provider = mock.MagicMock()
    ionq_provider.id = 'ionq'
    ionq_provider.targets = [
        mock_target(target_id='ionq.simulator', current_availability='Available', average_queue_time=1000),
        mock_target(target_id='ionq.qpu', current_availability='Available', average_queue_time=2000),
    ]

    quantinuum_provider = mock.MagicMock()
    quantinuum_provider.id = 'quantinuum'
    quantinuum_provider.targets = [
        mock_target(target_id='quantinuum.hqs-lt-s1-apival', current_availability='Available', average_queue_time=3000),
        mock_target(target_id='quantinuum.hqs-lt-s1-sim', current_availability='Available', average_queue_time=4000),
        mock_target(target_id='quantinuum.hqs-lt-s1', current_availability='Degraded', average_queue_time=5000),
    ]

    return [ionq_provider, quantinuum_provider]


def mock_target_factory(target_name):
    for provider in mock_providers():
        for target in provider.targets:
            if target.id == target_name:
                return target

    return []


def _get_azure_backend(use_hardware, target_name, retrieve_execution=None):
    AzureQuantumBackend._target_factory = mock.MagicMock(return_value=mock_target_factory(target_name))

    workspace = Workspace(
        subscription_id=ZERO_GUID, resource_group='testResourceGroup', name='testWorkspace', location='East US'
    )

    backend = AzureQuantumBackend(
        use_hardware=use_hardware,
        target_name=target_name,
        workspace=workspace,
        retrieve_execution=retrieve_execution,
        verbose=True,
    )

    return backend


def _get_main_engine(backend, max_qubits=3):
    mapper = BasicMapperEngine()

    mapping = {}
    for i in range(max_qubits):
        mapping[i] = i
    mapper.current_mapping = mapping

    main_engine = MainEngine(backend=backend, engine_list=[mapper], verbose=True)

    return main_engine


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
    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name)

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
    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name)

    assert backend._target_name == expected_target_name


@has_azure_quantum
def test_initialize_azure_backend_using_kwargs():
    backend = AzureQuantumBackend(
        use_hardware=False,
        target_name='ionq.simulator',
        subscription_id=ZERO_GUID,
        resource_group='testResourceGroup',
        name='testWorkspace',
        location='East US',
    )

    assert backend._target_name == 'ionq.simulator'


@has_azure_quantum
def test_azure_quantum_invalid_target():
    with pytest.raises(AzureQuantumTargetNotFoundError):
        _get_azure_backend(use_hardware=False, target_name='invalid-target')


@has_azure_quantum
def test_is_available_ionq():
    with mock.patch('projectq.backends._azure._azure_quantum.is_available_ionq') as is_available_ionq_patch:
        backend = _get_azure_backend(use_hardware=False, target_name='ionq.simulator')
        main_engine = _get_main_engine(backend=backend)

        q0 = main_engine.allocate_qubit()

        cmd = Command(main_engine, H, (q0,))
        main_engine.is_available(cmd)

        is_available_ionq_patch.assert_called()


@has_azure_quantum
def test_is_available_quantinuum():
    with mock.patch('projectq.backends._azure._azure_quantum.is_available_quantinuum') as is_available_quantinuum_patch:
        backend = _get_azure_backend(use_hardware=False, target_name='quantinuum.hqs-lt-s1-sim')
        main_engine = _get_main_engine(backend=backend)

        q0 = main_engine.allocate_qubit()

        cmd = Command(main_engine, H, (q0,))
        main_engine.is_available(cmd)

        is_available_quantinuum_patch.assert_called()


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
    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name)

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
    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name)

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

    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name)
    main_engine = _get_main_engine(backend=backend)

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

    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name)
    main_engine = _get_main_engine(backend=backend)

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
def test_run_get_probabilities_unused_qubit():
    projectq.backends._azure._azure_quantum.send = mock.MagicMock(
        return_value={'histogram': {'0': 0.5, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.5}}
    )

    backend = _get_azure_backend(use_hardware=False, target_name='ionq.simulator')
    main_engine = _get_main_engine(backend=backend, max_qubits=4)

    circuit = main_engine.allocate_qureg(3)
    unused_qubit = main_engine.allocate_qubit()
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    main_engine.flush()

    result = backend.get_probabilities(unused_qubit)

    assert len(result) == 1
    assert result['0'] == pytest.approx(1)


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id",
    [(False, 'ionq.simulator', 'ionq'), (True, 'ionq.qpu', 'ionq')],
)
def test_run_ionq_get_probability(use_hardware, target_name, provider_id):
    projectq.backends._azure._azure_quantum.send = mock.MagicMock(
        return_value={'histogram': {'0': 0.5, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.5}}
    )

    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name)
    main_engine = _get_main_engine(backend=backend)

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

    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name)
    main_engine = _get_main_engine(backend=backend)

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
def test_estimate_cost():
    projectq.backends._azure._azure_quantum.send = mock.MagicMock(
        return_value={'histogram': {'0': 0.5, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.5}}
    )

    backend = _get_azure_backend(use_hardware=False, target_name='ionq.simulator')
    main_engine = _get_main_engine(backend=backend)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    estimate_cost = backend.estimate_cost()

    assert estimate_cost.estimated_total == 10


@has_azure_quantum
def test_run_get_probability_invalid_state():
    projectq.backends._azure._azure_quantum.send = mock.MagicMock(
        return_value={'histogram': {'0': 0.5, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.5}}
    )

    backend = _get_azure_backend(use_hardware=False, target_name='ionq.simulator')
    main_engine = _get_main_engine(backend=backend)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    main_engine.flush()

    with pytest.raises(ValueError):
        _ = backend.get_probability('0000', circuit)


@has_azure_quantum
def test_run_no_circuit():
    backend = _get_azure_backend(use_hardware=False, target_name='ionq.simulator')
    main_engine = _get_main_engine(backend=backend)

    circuit = main_engine.allocate_qureg(3)

    main_engine.flush()

    with pytest.raises(RuntimeError):
        _ = backend.get_probabilities(circuit)


@has_azure_quantum
@pytest.mark.parametrize(
    "use_hardware, target_name, provider_id",
    [(False, 'ionq.simulator', 'ionq'), (True, 'ionq.qpu', 'ionq')],
)
@pytest.mark.parametrize(
    'retrieve_retval',
    (None, {'histogram': {'0': 0.5, '1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.5}}),
    ids=('retrieve-FAIL', 'retrieve-SUCESS'),
)
def test_run_ionq_retrieve_execution(use_hardware, target_name, provider_id, retrieve_retval):
    projectq.backends._azure._azure_quantum.retrieve = mock.MagicMock(return_value=retrieve_retval)

    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name, retrieve_execution=ZERO_GUID)
    main_engine = _get_main_engine(backend=backend)

    circuit = main_engine.allocate_qureg(3)
    q0, q1, q2 = circuit

    H | q0
    CX | (q0, q1)
    CX | (q1, q2)
    All(Measure) | circuit

    if retrieve_retval is None:
        with pytest.raises(RuntimeError):
            main_engine.flush()
    else:
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

    backend = _get_azure_backend(use_hardware=use_hardware, target_name=target_name, retrieve_execution=ZERO_GUID)
    main_engine = _get_main_engine(backend=backend)

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
def test_error_no_logical_id_tag():
    backend = _get_azure_backend(use_hardware=False, target_name='ionq.simulator')
    main_engine = _get_main_engine(backend=backend)

    q0 = WeakQubitRef(engine=None, idx=0)

    with pytest.raises(RuntimeError):
        main_engine.backend._store(Command(engine=main_engine, gate=Measure, qubits=([q0],)))


@has_azure_quantum
def test_error_invalid_provider():
    backend = _get_azure_backend(use_hardware=False, target_name='ionq.simulator')
    backend._provider_id = 'INVALID'  # NB: this is forcing it... should actually never happen in practice
    main_engine = _get_main_engine(backend=backend)

    q0 = WeakQubitRef(engine=None, idx=0)

    cmd = Command(engine=main_engine, gate=H, qubits=([q0],))
    with pytest.raises(RuntimeError):
        main_engine.backend._store(cmd)

    with pytest.raises(RuntimeError):
        main_engine.backend._input_data

    assert not main_engine.backend.is_available(cmd)
