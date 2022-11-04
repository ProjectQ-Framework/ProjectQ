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
"""Tests for projectq.cengines.__init__.py."""

from unittest.mock import MagicMock

from projectq.cengines import DummyEngine, flushing


def test_with_flushing():
    """Test with flushing() as eng:"""
    with flushing(DummyEngine()) as engine:
        engine.flush = MagicMock()
        assert engine.flush.call_count == 0
    assert engine.flush.call_count == 1


def test_with_flushing_with_exception():
    """Test with flushing() as eng: with an exception raised in the 'with' block."""
    try:
        with flushing(DummyEngine()) as engine:
            engine.flush = MagicMock()
            assert engine.flush.call_count == 0
            raise ValueError("An exception is raised in the 'with' block")
    except ValueError:
        pass
    assert engine.flush.call_count == 1
