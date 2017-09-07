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


from projectq import MainEngine
from projectq.cengines import DummyEngine
from projectq.meta import insert_engine, drop_engine_after


def test_insert_then_drop():
    d1 = DummyEngine()
    d2 = DummyEngine()
    d3 = DummyEngine()
    eng = MainEngine(backend=d3, engine_list=[d1])

    assert d1.next_engine is d3
    assert d2.next_engine is None
    assert d3.next_engine is None
    assert d1.main_engine is eng
    assert d2.main_engine is None
    assert d3.main_engine is eng

    insert_engine(d1, d2)
    assert d1.next_engine is d2
    assert d2.next_engine is d3
    assert d3.next_engine is None
    assert d1.main_engine is eng
    assert d2.main_engine is eng
    assert d3.main_engine is eng

    drop_engine_after(d1)
    assert d1.next_engine is d3
    assert d2.next_engine is None
    assert d3.next_engine is None
    assert d1.main_engine is eng
    assert d2.main_engine is None
    assert d3.main_engine is eng
