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

""" Test for projectq.backends.__init__.py"""

import builtins
import sys
import pytest

from importlib import reload

@pytest.fixture
def no_boto(monkeypatch):
    import_orig = builtins.__import__
    def moked_import(name, globals, locals, fromlist, level):
        if name == 'boto3':
            raise ModuleNotFoundError()
        return import_orig(name, locals, fromlist, level)
    monkeypatch.setattr(builtins, '__import__', moked_import)

@pytest.mark.usefixtures('no_boto')
def test_boto3_missing():
    with pytest.raises(ImportError):
        reload(sys.modules['projectq.backends._awsbraket'])
