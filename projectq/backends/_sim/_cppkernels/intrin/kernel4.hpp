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
inline void kernel_core(V &psi, std::size_t I, std::size_t d0, std::size_t d1, std::size_t d2, std::size_t d3, M const& m, M const& mt)
{
    __m256d v[4];

    v[0] = load2(&psi[I]);
    v[1] = load2(&psi[I + d0]);
    v[2] = load2(&psi[I + d1]);
    v[3] = load2(&psi[I + d0 + d1]);

    __m256d tmp[8];

    tmp[0] = add(mul(v[0], m[0], mt[0]), add(mul(v[1], m[1], mt[1]), add(mul(v[2], m[2], mt[2]), mul(v[3], m[3], mt[3]))));
    tmp[1] = add(mul(v[0], m[4], mt[4]), add(mul(v[1], m[5], mt[5]), add(mul(v[2], m[6], mt[6]), mul(v[3], m[7], mt[7]))));
    tmp[2] = add(mul(v[0], m[8], mt[8]), add(mul(v[1], m[9], mt[9]), add(mul(v[2], m[10], mt[10]), mul(v[3], m[11], mt[11]))));
    tmp[3] = add(mul(v[0], m[12], mt[12]), add(mul(v[1], m[13], mt[13]), add(mul(v[2], m[14], mt[14]), mul(v[3], m[15], mt[15]))));
    tmp[4] = add(mul(v[0], m[16], mt[16]), add(mul(v[1], m[17], mt[17]), add(mul(v[2], m[18], mt[18]), mul(v[3], m[19], mt[19]))));
    tmp[5] = add(mul(v[0], m[20], mt[20]), add(mul(v[1], m[21], mt[21]), add(mul(v[2], m[22], mt[22]), mul(v[3], m[23], mt[23]))));
    tmp[6] = add(mul(v[0], m[24], mt[24]), add(mul(v[1], m[25], mt[25]), add(mul(v[2], m[26], mt[26]), mul(v[3], m[27], mt[27]))));
    tmp[7] = add(mul(v[0], m[28], mt[28]), add(mul(v[1], m[29], mt[29]), add(mul(v[2], m[30], mt[30]), mul(v[3], m[31], mt[31]))));

    v[0] = load2(&psi[I + d2]);
    v[1] = load2(&psi[I + d0 + d2]);
    v[2] = load2(&psi[I + d1 + d2]);
    v[3] = load2(&psi[I + d0 + d1 + d2]);

    tmp[0] = add(tmp[0], add(mul(v[0], m[32], mt[32]), add(mul(v[1], m[33], mt[33]), add(mul(v[2], m[34], mt[34]), mul(v[3], m[35], mt[35])))));
    tmp[1] = add(tmp[1], add(mul(v[0], m[36], mt[36]), add(mul(v[1], m[37], mt[37]), add(mul(v[2], m[38], mt[38]), mul(v[3], m[39], mt[39])))));
    tmp[2] = add(tmp[2], add(mul(v[0], m[40], mt[40]), add(mul(v[1], m[41], mt[41]), add(mul(v[2], m[42], mt[42]), mul(v[3], m[43], mt[43])))));
    tmp[3] = add(tmp[3], add(mul(v[0], m[44], mt[44]), add(mul(v[1], m[45], mt[45]), add(mul(v[2], m[46], mt[46]), mul(v[3], m[47], mt[47])))));
    tmp[4] = add(tmp[4], add(mul(v[0], m[48], mt[48]), add(mul(v[1], m[49], mt[49]), add(mul(v[2], m[50], mt[50]), mul(v[3], m[51], mt[51])))));
    tmp[5] = add(tmp[5], add(mul(v[0], m[52], mt[52]), add(mul(v[1], m[53], mt[53]), add(mul(v[2], m[54], mt[54]), mul(v[3], m[55], mt[55])))));
    tmp[6] = add(tmp[6], add(mul(v[0], m[56], mt[56]), add(mul(v[1], m[57], mt[57]), add(mul(v[2], m[58], mt[58]), mul(v[3], m[59], mt[59])))));
    tmp[7] = add(tmp[7], add(mul(v[0], m[60], mt[60]), add(mul(v[1], m[61], mt[61]), add(mul(v[2], m[62], mt[62]), mul(v[3], m[63], mt[63])))));

    v[0] = load2(&psi[I + d3]);
    v[1] = load2(&psi[I + d0 + d3]);
    v[2] = load2(&psi[I + d1 + d3]);
    v[3] = load2(&psi[I + d0 + d1 + d3]);

    tmp[0] = add(tmp[0], add(mul(v[0], m[64], mt[64]), add(mul(v[1], m[65], mt[65]), add(mul(v[2], m[66], mt[66]), mul(v[3], m[67], mt[67])))));
    tmp[1] = add(tmp[1], add(mul(v[0], m[68], mt[68]), add(mul(v[1], m[69], mt[69]), add(mul(v[2], m[70], mt[70]), mul(v[3], m[71], mt[71])))));
    tmp[2] = add(tmp[2], add(mul(v[0], m[72], mt[72]), add(mul(v[1], m[73], mt[73]), add(mul(v[2], m[74], mt[74]), mul(v[3], m[75], mt[75])))));
    tmp[3] = add(tmp[3], add(mul(v[0], m[76], mt[76]), add(mul(v[1], m[77], mt[77]), add(mul(v[2], m[78], mt[78]), mul(v[3], m[79], mt[79])))));
    tmp[4] = add(tmp[4], add(mul(v[0], m[80], mt[80]), add(mul(v[1], m[81], mt[81]), add(mul(v[2], m[82], mt[82]), mul(v[3], m[83], mt[83])))));
    tmp[5] = add(tmp[5], add(mul(v[0], m[84], mt[84]), add(mul(v[1], m[85], mt[85]), add(mul(v[2], m[86], mt[86]), mul(v[3], m[87], mt[87])))));
    tmp[6] = add(tmp[6], add(mul(v[0], m[88], mt[88]), add(mul(v[1], m[89], mt[89]), add(mul(v[2], m[90], mt[90]), mul(v[3], m[91], mt[91])))));
    tmp[7] = add(tmp[7], add(mul(v[0], m[92], mt[92]), add(mul(v[1], m[93], mt[93]), add(mul(v[2], m[94], mt[94]), mul(v[3], m[95], mt[95])))));

    v[0] = load2(&psi[I + d2 + d3]);
    v[1] = load2(&psi[I + d0 + d2 + d3]);
    v[2] = load2(&psi[I + d1 + d2 + d3]);
    v[3] = load2(&psi[I + d0 + d1 + d2 + d3]);

    _mm256_storeu2_m128d((double*)&psi[I + d0], (double*)&psi[I], add(tmp[0], add(mul(v[0], m[96], mt[96]), add(mul(v[1], m[97], mt[97]), add(mul(v[2], m[98], mt[98]), mul(v[3], m[99], mt[99]))))));
    _mm256_storeu2_m128d((double*)&psi[I + d0 + d1], (double*)&psi[I + d1], add(tmp[1], add(mul(v[0], m[100], mt[100]), add(mul(v[1], m[101], mt[101]), add(mul(v[2], m[102], mt[102]), mul(v[3], m[103], mt[103]))))));
    _mm256_storeu2_m128d((double*)&psi[I + d0 + d2], (double*)&psi[I + d2], add(tmp[2], add(mul(v[0], m[104], mt[104]), add(mul(v[1], m[105], mt[105]), add(mul(v[2], m[106], mt[106]), mul(v[3], m[107], mt[107]))))));
    _mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d2], (double*)&psi[I + d1 + d2], add(tmp[3], add(mul(v[0], m[108], mt[108]), add(mul(v[1], m[109], mt[109]), add(mul(v[2], m[110], mt[110]), mul(v[3], m[111], mt[111]))))));
    _mm256_storeu2_m128d((double*)&psi[I + d0 + d3], (double*)&psi[I + d3], add(tmp[4], add(mul(v[0], m[112], mt[112]), add(mul(v[1], m[113], mt[113]), add(mul(v[2], m[114], mt[114]), mul(v[3], m[115], mt[115]))))));
    _mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d3], (double*)&psi[I + d1 + d3], add(tmp[5], add(mul(v[0], m[116], mt[116]), add(mul(v[1], m[117], mt[117]), add(mul(v[2], m[118], mt[118]), mul(v[3], m[119], mt[119]))))));
    _mm256_storeu2_m128d((double*)&psi[I + d0 + d2 + d3], (double*)&psi[I + d2 + d3], add(tmp[6], add(mul(v[0], m[120], mt[120]), add(mul(v[1], m[121], mt[121]), add(mul(v[2], m[122], mt[122]), mul(v[3], m[123], mt[123]))))));
    _mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d2 + d3], (double*)&psi[I + d1 + d2 + d3], add(tmp[7], add(mul(v[0], m[124], mt[124]), add(mul(v[1], m[125], mt[125]), add(mul(v[2], m[126], mt[126]), mul(v[3], m[127], mt[127]))))));

}

// bit indices id[.] are given from high to low (e.g. control first for CNOT)
template <class V, class M>
void kernel(V &psi, unsigned id3, unsigned id2, unsigned id1, unsigned id0, M const& m, std::size_t ctrlmask)
{
    std::size_t n = psi.size();
    std::size_t d0 = 1UL << id0;
    std::size_t d1 = 1UL << id1;
    std::size_t d2 = 1UL << id2;
    std::size_t d3 = 1UL << id3;

    __m256d mm[] = {load(&m[0][0], &m[1][0]), load(&m[0][1], &m[1][1]), load(&m[0][2], &m[1][2]), load(&m[0][3], &m[1][3]), load(&m[2][0], &m[3][0]), load(&m[2][1], &m[3][1]), load(&m[2][2], &m[3][2]), load(&m[2][3], &m[3][3]), load(&m[4][0], &m[5][0]), load(&m[4][1], &m[5][1]), load(&m[4][2], &m[5][2]), load(&m[4][3], &m[5][3]), load(&m[6][0], &m[7][0]), load(&m[6][1], &m[7][1]), load(&m[6][2], &m[7][2]), load(&m[6][3], &m[7][3]), load(&m[8][0], &m[9][0]), load(&m[8][1], &m[9][1]), load(&m[8][2], &m[9][2]), load(&m[8][3], &m[9][3]), load(&m[10][0], &m[11][0]), load(&m[10][1], &m[11][1]), load(&m[10][2], &m[11][2]), load(&m[10][3], &m[11][3]), load(&m[12][0], &m[13][0]), load(&m[12][1], &m[13][1]), load(&m[12][2], &m[13][2]), load(&m[12][3], &m[13][3]), load(&m[14][0], &m[15][0]), load(&m[14][1], &m[15][1]), load(&m[14][2], &m[15][2]), load(&m[14][3], &m[15][3]), load(&m[0][4], &m[1][4]), load(&m[0][5], &m[1][5]), load(&m[0][6], &m[1][6]), load(&m[0][7], &m[1][7]), load(&m[2][4], &m[3][4]), load(&m[2][5], &m[3][5]), load(&m[2][6], &m[3][6]), load(&m[2][7], &m[3][7]), load(&m[4][4], &m[5][4]), load(&m[4][5], &m[5][5]), load(&m[4][6], &m[5][6]), load(&m[4][7], &m[5][7]), load(&m[6][4], &m[7][4]), load(&m[6][5], &m[7][5]), load(&m[6][6], &m[7][6]), load(&m[6][7], &m[7][7]), load(&m[8][4], &m[9][4]), load(&m[8][5], &m[9][5]), load(&m[8][6], &m[9][6]), load(&m[8][7], &m[9][7]), load(&m[10][4], &m[11][4]), load(&m[10][5], &m[11][5]), load(&m[10][6], &m[11][6]), load(&m[10][7], &m[11][7]), load(&m[12][4], &m[13][4]), load(&m[12][5], &m[13][5]), load(&m[12][6], &m[13][6]), load(&m[12][7], &m[13][7]), load(&m[14][4], &m[15][4]), load(&m[14][5], &m[15][5]), load(&m[14][6], &m[15][6]), load(&m[14][7], &m[15][7]), load(&m[0][8], &m[1][8]), load(&m[0][9], &m[1][9]), load(&m[0][10], &m[1][10]), load(&m[0][11], &m[1][11]), load(&m[2][8], &m[3][8]), load(&m[2][9], &m[3][9]), load(&m[2][10], &m[3][10]), load(&m[2][11], &m[3][11]), load(&m[4][8], &m[5][8]), load(&m[4][9], &m[5][9]), load(&m[4][10], &m[5][10]), load(&m[4][11], &m[5][11]), load(&m[6][8], &m[7][8]), load(&m[6][9], &m[7][9]), load(&m[6][10], &m[7][10]), load(&m[6][11], &m[7][11]), load(&m[8][8], &m[9][8]), load(&m[8][9], &m[9][9]), load(&m[8][10], &m[9][10]), load(&m[8][11], &m[9][11]), load(&m[10][8], &m[11][8]), load(&m[10][9], &m[11][9]), load(&m[10][10], &m[11][10]), load(&m[10][11], &m[11][11]), load(&m[12][8], &m[13][8]), load(&m[12][9], &m[13][9]), load(&m[12][10], &m[13][10]), load(&m[12][11], &m[13][11]), load(&m[14][8], &m[15][8]), load(&m[14][9], &m[15][9]), load(&m[14][10], &m[15][10]), load(&m[14][11], &m[15][11]), load(&m[0][12], &m[1][12]), load(&m[0][13], &m[1][13]), load(&m[0][14], &m[1][14]), load(&m[0][15], &m[1][15]), load(&m[2][12], &m[3][12]), load(&m[2][13], &m[3][13]), load(&m[2][14], &m[3][14]), load(&m[2][15], &m[3][15]), load(&m[4][12], &m[5][12]), load(&m[4][13], &m[5][13]), load(&m[4][14], &m[5][14]), load(&m[4][15], &m[5][15]), load(&m[6][12], &m[7][12]), load(&m[6][13], &m[7][13]), load(&m[6][14], &m[7][14]), load(&m[6][15], &m[7][15]), load(&m[8][12], &m[9][12]), load(&m[8][13], &m[9][13]), load(&m[8][14], &m[9][14]), load(&m[8][15], &m[9][15]), load(&m[10][12], &m[11][12]), load(&m[10][13], &m[11][13]), load(&m[10][14], &m[11][14]), load(&m[10][15], &m[11][15]), load(&m[12][12], &m[13][12]), load(&m[12][13], &m[13][13]), load(&m[12][14], &m[13][14]), load(&m[12][15], &m[13][15]), load(&m[14][12], &m[15][12]), load(&m[14][13], &m[15][13]), load(&m[14][14], &m[15][14]), load(&m[14][15], &m[15][15])};
    __m256d mmt[128];

    __m256d neg = _mm256_setr_pd(1.0, -1.0, 1.0, -1.0);
    for (unsigned i = 0; i < 128; ++i){
        auto badc = _mm256_permute_pd(mm[i], 5);
        mmt[i] = _mm256_mul_pd(badc, neg);
    }

    std::size_t dsorted[] = {d0 , d1, d2, d3};
    std::sort(dsorted, dsorted + 4, std::greater<std::size_t>());

    if (ctrlmask == 0){
        #pragma omp for collapse(LOOP_COLLAPSE4) schedule(static)
        for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
            for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
                for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
                    for (std::size_t i3 = 0; i3 < dsorted[2]; i3 += 2 * dsorted[3]){
                        for (std::size_t i4 = 0; i4 < dsorted[3]; ++i4){
                            kernel_core(psi, i0 + i1 + i2 + i3 + i4, d0, d1, d2, d3, mm, mmt);
                        }
                    }
                }
            }
        }
    }
    else{
        #pragma omp for collapse(LOOP_COLLAPSE4) schedule(static)
        for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
            for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
                for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
                    for (std::size_t i3 = 0; i3 < dsorted[2]; i3 += 2 * dsorted[3]){
                        for (std::size_t i4 = 0; i4 < dsorted[3]; ++i4){
                            if (((i0 + i1 + i2 + i3 + i4)&ctrlmask) == ctrlmask)
                                kernel_core(psi, i0 + i1 + i2 + i3 + i4, d0, d1, d2, d3, mm, mmt);
                        }
                    }
                }
            }
        }
    }
}

