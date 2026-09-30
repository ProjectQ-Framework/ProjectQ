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

import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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


@pytest.mark.parametrize('dry_run', [False, True])
def test_clang_tidy_spawn_compatibility(dry_run):
    """Clang-Tidy respects dry runs without relying on removed spawn arguments."""
    from setuptools import Distribution

    setup_path = Path(__file__).resolve().parents[1] / 'setup.py'
    if not setup_path.is_file():
        pytest.skip('Requires a source checkout')
    with patch('setuptools.setup'):
        namespace = runpy.run_path(str(setup_path))
    command = namespace['ClangTidy'](Distribution())
    command.distribution.ext_modules = []
    command.dry_run = dry_run
    command.warning_as_errors = True
    build = SimpleNamespace(run=lambda: None)
    calls = []

    def spawn(args):
        calls.append(args)

    with patch.object(command, 'get_finalized_command', return_value=build):
        with patch.dict(command.run.__globals__, spawn=spawn):
            command.run()
    assert calls == ([] if dry_run else [['clang-tidy', '--warnings-as-errors=*']])
