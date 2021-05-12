# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
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
"""Tests for projectq.setup.aqt."""

import pytest


def test_aqt_mapper_in_cengines(monkeypatch):
    import projectq.setups.aqt

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
        return {'aqt_simulator': {'coupling_map': connections, 'version': '0.0.0', 'nq': 32}}

    monkeypatch.setattr(projectq.setups.aqt, "show_devices", mock_show_devices)
    engines_simulator = projectq.setups.aqt.get_engine_list(device='aqt_simulator')
    assert len(engines_simulator) == 13


def test_aqt_errors(monkeypatch):
    import projectq.setups.aqt

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
        return {'aqt_imaginary': {'coupling_map': connections, 'version': '0.0.0', 'nq': 6}}

    monkeypatch.setattr(projectq.setups.aqt, "show_devices", mock_show_devices)
    with pytest.raises(projectq.setups.aqt.DeviceOfflineError):
        projectq.setups.aqt.get_engine_list(device='simulator')
    with pytest.raises(projectq.setups.aqt.DeviceNotHandledError):
        projectq.setups.aqt.get_engine_list(device='aqt_imaginary')
