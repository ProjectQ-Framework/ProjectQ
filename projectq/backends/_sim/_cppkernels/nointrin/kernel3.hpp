// Copyright 2017 ProjectQ-Framework (www.projectq.ch)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

template <class V, class M>
inline void kernel_core(V &psi, std::size_t I, std::size_t d0, std::size_t d1, std::size_t d2, M const& m)
{
    std::complex<double> v[4];
    v[0] = psi[I];
    v[1] = psi[I + d0];
    v[2] = psi[I + d1];
    v[3] = psi[I + d0 + d1];

    std::complex<double> tmp[8];

    tmp[0] = add(mul(v[0], m[0][0]), add(mul(v[1], m[0][1]), add(mul(v[2], m[0][2]), mul(v[3], m[0][3]))));
    tmp[1] = add(mul(v[0], m[1][0]), add(mul(v[1], m[1][1]), add(mul(v[2], m[1][2]), mul(v[3], m[1][3]))));
    tmp[2] = add(mul(v[0], m[2][0]), add(mul(v[1], m[2][1]), add(mul(v[2], m[2][2]), mul(v[3], m[2][3]))));
    tmp[3] = add(mul(v[0], m[3][0]), add(mul(v[1], m[3][1]), add(mul(v[2], m[3][2]), mul(v[3], m[3][3]))));
    tmp[4] = add(mul(v[0], m[4][0]), add(mul(v[1], m[4][1]), add(mul(v[2], m[4][2]), mul(v[3], m[4][3]))));
    tmp[5] = add(mul(v[0], m[5][0]), add(mul(v[1], m[5][1]), add(mul(v[2], m[5][2]), mul(v[3], m[5][3]))));
    tmp[6] = add(mul(v[0], m[6][0]), add(mul(v[1], m[6][1]), add(mul(v[2], m[6][2]), mul(v[3], m[6][3]))));
    tmp[7] = add(mul(v[0], m[7][0]), add(mul(v[1], m[7][1]), add(mul(v[2], m[7][2]), mul(v[3], m[7][3]))));

    v[0] = psi[I + d2];
    v[1] = psi[I + d0 + d2];
    v[2] = psi[I + d1 + d2];
    v[3] = psi[I + d0 + d1 + d2];

    psi[I] = (add(tmp[0], add(mul(v[0], m[0][4]), add(mul(v[1], m[0][5]), add(mul(v[2], m[0][6]), mul(v[3], m[0][7]))))));
    psi[I + d0] = (add(tmp[1], add(mul(v[0], m[1][4]), add(mul(v[1], m[1][5]), add(mul(v[2], m[1][6]), mul(v[3], m[1][7]))))));
    psi[I + d1] = (add(tmp[2], add(mul(v[0], m[2][4]), add(mul(v[1], m[2][5]), add(mul(v[2], m[2][6]), mul(v[3], m[2][7]))))));
    psi[I + d0 + d1] = (add(tmp[3], add(mul(v[0], m[3][4]), add(mul(v[1], m[3][5]), add(mul(v[2], m[3][6]), mul(v[3], m[3][7]))))));
    psi[I + d2] = (add(tmp[4], add(mul(v[0], m[4][4]), add(mul(v[1], m[4][5]), add(mul(v[2], m[4][6]), mul(v[3], m[4][7]))))));
    psi[I + d0 + d2] = (add(tmp[5], add(mul(v[0], m[5][4]), add(mul(v[1], m[5][5]), add(mul(v[2], m[5][6]), mul(v[3], m[5][7]))))));
    psi[I + d1 + d2] = (add(tmp[6], add(mul(v[0], m[6][4]), add(mul(v[1], m[6][5]), add(mul(v[2], m[6][6]), mul(v[3], m[6][7]))))));
    psi[I + d0 + d1 + d2] = (add(tmp[7], add(mul(v[0], m[7][4]), add(mul(v[1], m[7][5]), add(mul(v[2], m[7][6]), mul(v[3], m[7][7]))))));

}

// bit indices id[.] are given from high to low (e.g. control first for CNOT)
template <class V, class M>
void kernel(V &psi, unsigned id2, unsigned id1, unsigned id0, M const& m, std::size_t ctrlmask)
{
    std::size_t n = psi.size();
    std::size_t d0 = 1UL << id0;
    std::size_t d1 = 1UL << id1;
    std::size_t d2 = 1UL << id2;
    std::size_t dsorted[] = {d0 , d1, d2};
    std::sort(dsorted, dsorted + 3, std::greater<std::size_t>());

    if (ctrlmask == 0){
        #pragma omp for collapse(LOOP_COLLAPSE3) schedule(static)
        for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
            for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
                for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
                    for (std::size_t i3 = 0; i3 < dsorted[2]; ++i3){
                        kernel_core(psi, i0 + i1 + i2 + i3, d0, d1, d2, m);
                    }
                }
            }
        }
    }
    else{
        #pragma omp for collapse(LOOP_COLLAPSE3) schedule(static)
        for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
            for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
                for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
                    for (std::size_t i3 = 0; i3 < dsorted[2]; ++i3){
                        if (((i0 + i1 + i2 + i3)&ctrlmask) == ctrlmask)
                            kernel_core(psi, i0 + i1 + i2 + i3, d0, d1, d2, m);
                    }
                }
            }
        }
    }
}

