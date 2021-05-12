# -*- coding: utf-8 -*-
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
"""Tests for projectq.setup.ibm."""

import pytest


def test_ibm_cnot_mapper_in_cengines(monkeypatch):
    import projectq.setups.ibm

    def mock_show_devices(*args, **kwargs):
        connections = set(
            [
                (0, 1),
                (1, 0),
                (1, 2),
                (1, 3),
                (1, 4),
                (2, 1),
                (2, 3),
                (2, 4),
                (3, 1),
                (3, 4),
                (4, 3),
            ]
        )
        return {
            'ibmq_burlington': {
                'coupling_map': connections,
                'version': '0.0.0',
                'nq': 5,
            },
            'ibmq_16_melbourne': {
                'coupling_map': connections,
                'version': '0.0.0',
                'nq': 15,
            },
            'ibmq_qasm_simulator': {
                'coupling_map': connections,
                'version': '0.0.0',
                'nq': 32,
            },
        }

    monkeypatch.setattr(projectq.setups.ibm, "show_devices", mock_show_devices)
    engines_5qb = projectq.setups.ibm.get_engine_list(device='ibmq_burlington')
    engines_15qb = projectq.setups.ibm.get_engine_list(device='ibmq_16_melbourne')
    engines_simulator = projectq.setups.ibm.get_engine_list(device='ibmq_qasm_simulator')
    assert len(engines_5qb) == 15
    assert len(engines_15qb) == 16
    assert len(engines_simulator) == 13


def test_ibm_errors(monkeypatch):
    import projectq.setups.ibm

    def mock_show_devices(*args, **kwargs):
        connections = set(
            [
                (0, 1),
                (1, 0),
                (1, 2),
                (1, 3),
                (1, 4),
                (2, 1),
                (2, 3),
                (2, 4),
                (3, 1),
                (3, 4),
                (4, 3),
            ]
        )
        return {'ibmq_imaginary': {'coupling_map': connections, 'version': '0.0.0', 'nq': 6}}

    monkeypatch.setattr(projectq.setups.ibm, "show_devices", mock_show_devices)
    with pytest.raises(projectq.setups.ibm.DeviceOfflineError):
        projectq.setups.ibm.get_engine_list(device='ibmq_burlington')
    with pytest.raises(projectq.setups.ibm.DeviceNotHandledError):
        projectq.setups.ibm.get_engine_list(device='ibmq_imaginary')
