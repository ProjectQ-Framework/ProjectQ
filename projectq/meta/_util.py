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


def insert_engine(prev_engine, engine_to_insert):
    """
    Inserts an engine into the singly-linked list of engines.

    It also sets the correct main_engine for engine_to_insert.

    Args:
        prev_engine (projectq.cengines.BasicEngine):
            The engine just before the insertion point.
        engine_to_insert (projectq.cengines.BasicEngine):
            The engine to insert at the insertion point.
    """
    engine_to_insert.main_engine = prev_engine.main_engine
    engine_to_insert.next_engine = prev_engine.next_engine
    prev_engine.next_engine = engine_to_insert


def drop_engine_after(prev_engine):
    """
    Removes an engine from the singly-linked list of engines.

    Args:
        prev_engine (projectq.cengines.BasicEngine):
            The engine just before the engine to drop.
    Returns:
        Engine: The dropped engine.
    """
    dropped_engine = prev_engine.next_engine
    prev_engine.next_engine = dropped_engine.next_engine
    dropped_engine.next_engine = None
    dropped_engine.main_engine = None
    return dropped_engine
