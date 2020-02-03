# Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from projectq.ops import BasicGate

import numpy as np


def _is_unitary(m):
    return np.allclose(m*m.H, np.eye(2))


# Helper class
class _SingleQubitGate(BasicGate):
    def __init__(self, m):
        self._matrix = m
        self.interchangeable_qubit_indices = []
        self._error = np.linalg.norm(m*m.H - np.eye(2))

    @property
    def matrix(self):
        return self._matrix

    def get_inverse(self):
        return _SingleQubitGate(self._matrix.getH())

    def __str__(self):
        return "U[{:.2f} {:.2f}; {:.2f} {:.2f}]".format(
            abs(self.matrix.item((0, 0))), abs(self.matrix.item((0, 1))),
            abs(self.matrix.item((1, 0))), abs(self.matrix.item((1, 1))))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return np.allclose(self.matrix, other.matrix)
        else:
            return False
