# -*- coding: utf-8 -*-
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

from . import (
    arb1qubit2rzandry,
    barrier,
    carb1qubit2cnotrzandry,
    crz2cxandrz,
    cnot2rxx,
    cnot2cz,
    cnu2toffoliandcu,
    controlstate,
    entangle,
    globalphase,
    h2rx,
    ph2r,
    qubitop2onequbit,
    qft2crandhadamard,
    r2rzandph,
    rx2rz,
    ry2rz,
    rz2rx,
    sqrtswap2cnot,
    stateprep2cnot,
    swap2cnot,
    toffoli2cnotandtgate,
    time_evolution,
    uniformlycontrolledr2cnot,
    phaseestimation,
    amplitudeamplification,
)

all_defined_decomposition_rules = [
    rule
    for module in [
        arb1qubit2rzandry,
        barrier,
        carb1qubit2cnotrzandry,
        crz2cxandrz,
        cnot2rxx,
        cnot2cz,
        cnu2toffoliandcu,
        controlstate,
        entangle,
        globalphase,
        h2rx,
        ph2r,
        qubitop2onequbit,
        qft2crandhadamard,
        r2rzandph,
        rx2rz,
        ry2rz,
        rz2rx,
        sqrtswap2cnot,
        stateprep2cnot,
        swap2cnot,
        toffoli2cnotandtgate,
        time_evolution,
        uniformlycontrolledr2cnot,
        phaseestimation,
        amplitudeamplification,
    ]
    for rule in module.all_defined_decomposition_rules
]
