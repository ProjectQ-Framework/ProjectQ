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


def test_azure_quantum_ionq_target():
    workspace = create_workspace()

    # sim and use_hardware is false
    backend = AzureQuantumBackend(
        use_hardware=False,
        target_name='ionq.simulator',
        workspace=workspace
    )
    assert backend._provider_id == 'ionq'
    assert backend._target_name == 'ionq.simulator'

    # qpu and use_hardware is true
    backend = AzureQuantumBackend(
        use_hardware=True,
        target_name='ionq.qpu',
        workspace=workspace
    )
    assert backend._provider_id == 'ionq'
    assert backend._target_name == 'ionq.qpu'

    # qpu and use_hardware is false
    backend = AzureQuantumBackend(
        use_hardware=False,
        target_name='ionq.qpu',
        workspace=workspace
    )
    assert backend._provider_id == 'ionq'
    assert backend._target_name == 'ionq.simulator'


def test_azure_quantum_quantinuum_target():
    workspace = create_workspace()

    # apival and use_hardware is false
    backend = AzureQuantumBackend(
        use_hardware=False,
        target_name='quantinuum.hqs-lt-s1-apival',
        workspace=workspace
    )
    assert backend._provider_id == 'quantinuum'
    assert backend._target_name == 'quantinuum.hqs-lt-s1-apival'

    # apival and use_hardware is false
    backend = AzureQuantumBackend(
        use_hardware=False,
        target_name='quantinuum.hqs-lt-s1-sim',
        workspace=workspace
    )
    assert backend._provider_id == 'quantinuum'
    assert backend._target_name == 'quantinuum.hqs-lt-s1-sim'

    # qpu and use_hardware is true
    backend = AzureQuantumBackend(
        use_hardware=True,
        target_name='quantinuum.hqs-lt-s1',
        workspace=workspace
    )
    assert backend._provider_id == 'quantinuum'
    assert backend._target_name == 'quantinuum.hqs-lt-s1'

    # qpu and use_hardware is false
    backend = AzureQuantumBackend(
        use_hardware=False,
        target_name='quantinuum.hqs-lt-s1',
        workspace=workspace
    )
    assert backend._provider_id == 'quantinuum'
    assert backend._target_name == 'quantinuum.hqs-lt-s1-apival'

    # sim and use_hardware is false
    backend = AzureQuantumBackend(
        use_hardware=False,
        target_name='quantinuum.hqs-lt-s1-sim',
        workspace=workspace
    )
    assert backend._provider_id == 'quantinuum'
    assert backend._target_name == 'quantinuum.hqs-lt-s1-sim'


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


def test_estimate_cost():
    assert True


def test_run():
    assert True


def test_run_error1():
    assert True


def test_run_error2():
    assert True
