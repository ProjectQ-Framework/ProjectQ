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

import copy
import math
import cmath
import numpy as np


def _is_power_of_2(N):
    return (N != 0) and ((N & (N - 1)) == 0)


class _DecomposeDiagonal(object):
    def __init__(self, phases):
        self._angles = [cmath.phase(p) for p in phases]
        assert _is_power_of_2(len(phases))

    def get_decomposition(self):
        decomposition = []

        angles = self._angles
        N = len(angles)

        while N >= 2:
            rotations = []
            for i in range(0, N, 2):
                angles[i//2], rot = _basic_decomposition(angles[i],
                                                         angles[i+1])
                rotations.append(rot)
            _decompose_rotations(rotations, 0, N//2)
            decomposition.append(rotations)
            N //= 2

        decomposition.append([angles[0]])
        return decomposition


# global and relative phase
def _basic_decomposition(phi1, phi2):
    return (phi1+phi2)/2.0, phi2-phi1


# uniformly controlled rotation (one choice qubit)
def _decompose_rotation(phi1, phi2):
    return (phi1 + phi2) / 2.0, (phi1 - phi2) / 2.0


def _decompose_rotations(angles, a, b):
    N = b-a
    if N <= 1:
        return
    for i in range(a, a+N//2):
        angles[i], angles[i+N//2] = _decompose_rotation(angles[i],
                                                        angles[i+N//2])
    _decompose_rotations(angles, a, a+N//2)
    _decompose_rotations_reversed(angles, a+N//2, b)


def _decompose_rotations_reversed(angles, a, b):
    N = b-a
    if N <= 1:
        return
    for i in range(a, a+N//2):
        angles[i+N//2], angles[i] = _decompose_rotation(angles[i],
                                                        angles[i+N//2])
    _decompose_rotations(angles, a, a+N//2)
    _decompose_rotations_reversed(angles, a+N//2, b)
