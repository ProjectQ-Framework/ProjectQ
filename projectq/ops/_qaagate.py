#   Copyright 2019 ProjectQ-Framework (www.projectq.ch)
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


class QAA(BasicGate):
    """
    Quantum Aplitude Aplification gate.

    See setups.decompositions for the complete implementation
    """
    def __init__(self, algorithm, algorithm_inverse, oracle):
        BasicGate.__init__(self)
        self.algorithm = algorithm
        self.algorithm_inverse = algorithm_inverse
        self.oracle = oracle

    def __str__(self):
        return 'QAA(Algorithm = {0}, Oracle = {1})'.format(str(self.algorithm.__name__), str(self.oracle.__name__))
