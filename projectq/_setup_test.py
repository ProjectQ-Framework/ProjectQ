#   Copyright 2017, 2021 ProjectQ-Framework (www.projectq.ch)
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
"""Regression tests for source-tree packaging commands."""

import subprocess
import sys
from pathlib import Path

import pytest


def test_requirements_fallback_preserves_marker_quotes(tmp_path):
    """Requirement generation must work without an optional TOML parser."""
    setup_path = Path(__file__).resolve().parents[1] / 'setup.py'
    if not setup_path.is_file():
        pytest.skip('Requires a source checkout')
    script = """
import runpy
import sys
import setuptools

sys.modules['tomllib'] = None
sys.modules['toml'] = None
sys.argv = [sys.argv[1], 'gen_reqfile', '--include-extras=azure-quantum']
runpy.run_path(sys.argv[0], run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, '-c', script, str(setup_path)], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    requirements = (tmp_path / 'requirements.txt').read_text().splitlines()
    assert 'azure-quantum <= 3.5.0; python_version <= "3.8"' in requirements
    assert 'azure-quantum; python_version > "3.8"' in requirements
