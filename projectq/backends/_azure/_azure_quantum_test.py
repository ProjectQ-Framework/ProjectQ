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

from azure.quantum import Workspace
from azure.identity import ClientSecretCredential

from projectq.backends import AzureQuantumBackend
from projectq.backends._azure._exceptions import AzureQuantumTargetNotFoundError

import pytest


ZERO_GUID = '00000000-0000-0000-0000-000000000000'


def create_workspace(**kwargs):
    default_credential = ClientSecretCredential(
        tenant_id=ZERO_GUID,
        client_id=ZERO_GUID,
        client_secret=ZERO_GUID
    )

    workspace = Workspace(
        credential=default_credential,
        subscription_id=ZERO_GUID,
        resource_group='test-rg',
        name='test-workspace',
        location='east us',
        **kwargs
    )

    workspace.append_user_agent("test-app")
    return workspace


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
    "target_name, expected_result",
    [
        ('ionq.simulator', 1.0),
        ('ionq.qpu', 10.0),
        ('quantinuum.hqs-lt-s1-apival', 1.0),
        ('quantinuum.hqs-lt-s1-sim', 1.0),
        ('quantinuum.hqs-lt-s1', 10.0),
    ],
)
def test_estimate_cost(target_name, expected_result):
    assert True


def test_run():
    assert True


def test_run_error1():
    assert True


def test_run_error2():
    assert True
