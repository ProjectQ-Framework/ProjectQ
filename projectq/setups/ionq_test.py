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
"""Tests for projectq.setup.ionq."""

import pytest

from projectq.backends._ionq._ionq_exc import DeviceOfflineError
from projectq.backends._ionq._ionq_mapper import BoundedQubitMapper


def test_basic_ionq_mapper(monkeypatch):
    import projectq.setups.ionq

    def mock_show_devices(*args, **kwargs):
        return {'dummy': {'nq': 3, 'target': 'dummy'}}

    monkeypatch.setattr(projectq.setups.ionq, 'show_devices', mock_show_devices)
    engine_list = projectq.setups.ionq.get_engine_list(device='dummy')
    assert len(engine_list) > 1
    mapper = engine_list[-1]
    assert isinstance(mapper, BoundedQubitMapper)
    # to match nq in the backend
    assert mapper.max_qubits == 3


def test_ionq_errors(monkeypatch):
    import projectq.setups.ionq

    def mock_show_devices(*args, **kwargs):
        return {'dummy': {'nq': 3, 'target': 'dummy'}}

    monkeypatch.setattr(projectq.setups.ionq, 'show_devices', mock_show_devices)

    with pytest.raises(DeviceOfflineError):
        projectq.setups.ionq.get_engine_list(device='simulator')
