#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
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

"""
Defines LogicalQubitIDTag to annotate a MeasureGate for mapped qubits.
"""


class LogicalQubitIDTag(object):
    """
    LogicalQubitIDTag for a mapped qubit to annotate a MeasureGate.

    Attributes:
        logical_qubit_id (int): Logical qubit id
    """
    def __init__(self, logical_qubit_id):
        self.logical_qubit_id = logical_qubit_id

    def __eq__(self, other):
        return (isinstance(other, LogicalQubitIDTag) and
                self.logical_qubit_id == other.logical_qubit_id)

    def __ne__(self, other):
        return not self.__eq__(other)
