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

from . import (crz2cxandrz,
               entangle,
               globalphase,
               ph2r,
               qft2crandhadamard,
               r2rzandph,
               swap2cnot,
               toffoli2cnotandtgate,
               time_evolution)

all_defined_decomposition_rules = [
    rule
    for module in [crz2cxandrz,
                   entangle,
                   globalphase,
                   ph2r,
                   qft2crandhadamard,
                   r2rzandph,
                   swap2cnot,
                   toffoli2cnotandtgate,
                   time_evolution]
    for rule in module.all_defined_decomposition_rules
]
