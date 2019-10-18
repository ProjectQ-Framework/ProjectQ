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

from ._basics import BasicGate


class QPE(BasicGate):
    """
    Quantum Phase Estimation gate.

    See setups.decompositions for the complete implementation
    """
    def __init__(self, unitary):
        BasicGate.__init__(self)
        self.unitary = unitary

    def __str__(self):
        return 'QPE({})'.format(str(self.unitary))
