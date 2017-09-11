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
inline void kernel_core(V &psi, std::size_t I, std::size_t d0, std::size_t d1, std::size_t d2, std::size_t d3, std::size_t d4, M const& m)
{
    std::complex<double> v[4];
    v[0] = psi[I];
    v[1] = psi[I + d0];
    v[2] = psi[I + d1];
    v[3] = psi[I + d0 + d1];

    std::complex<double> tmp[32];

    tmp[0] = add(mul(v[0], m[0][0]), add(mul(v[1], m[0][1]), add(mul(v[2], m[0][2]), mul(v[3], m[0][3]))));
    tmp[1] = add(mul(v[0], m[1][0]), add(mul(v[1], m[1][1]), add(mul(v[2], m[1][2]), mul(v[3], m[1][3]))));
    tmp[2] = add(mul(v[0], m[2][0]), add(mul(v[1], m[2][1]), add(mul(v[2], m[2][2]), mul(v[3], m[2][3]))));
    tmp[3] = add(mul(v[0], m[3][0]), add(mul(v[1], m[3][1]), add(mul(v[2], m[3][2]), mul(v[3], m[3][3]))));
    tmp[4] = add(mul(v[0], m[4][0]), add(mul(v[1], m[4][1]), add(mul(v[2], m[4][2]), mul(v[3], m[4][3]))));
    tmp[5] = add(mul(v[0], m[5][0]), add(mul(v[1], m[5][1]), add(mul(v[2], m[5][2]), mul(v[3], m[5][3]))));
    tmp[6] = add(mul(v[0], m[6][0]), add(mul(v[1], m[6][1]), add(mul(v[2], m[6][2]), mul(v[3], m[6][3]))));
    tmp[7] = add(mul(v[0], m[7][0]), add(mul(v[1], m[7][1]), add(mul(v[2], m[7][2]), mul(v[3], m[7][3]))));
    tmp[8] = add(mul(v[0], m[8][0]), add(mul(v[1], m[8][1]), add(mul(v[2], m[8][2]), mul(v[3], m[8][3]))));
    tmp[9] = add(mul(v[0], m[9][0]), add(mul(v[1], m[9][1]), add(mul(v[2], m[9][2]), mul(v[3], m[9][3]))));
    tmp[10] = add(mul(v[0], m[10][0]), add(mul(v[1], m[10][1]), add(mul(v[2], m[10][2]), mul(v[3], m[10][3]))));
    tmp[11] = add(mul(v[0], m[11][0]), add(mul(v[1], m[11][1]), add(mul(v[2], m[11][2]), mul(v[3], m[11][3]))));
    tmp[12] = add(mul(v[0], m[12][0]), add(mul(v[1], m[12][1]), add(mul(v[2], m[12][2]), mul(v[3], m[12][3]))));
    tmp[13] = add(mul(v[0], m[13][0]), add(mul(v[1], m[13][1]), add(mul(v[2], m[13][2]), mul(v[3], m[13][3]))));
    tmp[14] = add(mul(v[0], m[14][0]), add(mul(v[1], m[14][1]), add(mul(v[2], m[14][2]), mul(v[3], m[14][3]))));
    tmp[15] = add(mul(v[0], m[15][0]), add(mul(v[1], m[15][1]), add(mul(v[2], m[15][2]), mul(v[3], m[15][3]))));
    tmp[16] = add(mul(v[0], m[16][0]), add(mul(v[1], m[16][1]), add(mul(v[2], m[16][2]), mul(v[3], m[16][3]))));
    tmp[17] = add(mul(v[0], m[17][0]), add(mul(v[1], m[17][1]), add(mul(v[2], m[17][2]), mul(v[3], m[17][3]))));
    tmp[18] = add(mul(v[0], m[18][0]), add(mul(v[1], m[18][1]), add(mul(v[2], m[18][2]), mul(v[3], m[18][3]))));
    tmp[19] = add(mul(v[0], m[19][0]), add(mul(v[1], m[19][1]), add(mul(v[2], m[19][2]), mul(v[3], m[19][3]))));
    tmp[20] = add(mul(v[0], m[20][0]), add(mul(v[1], m[20][1]), add(mul(v[2], m[20][2]), mul(v[3], m[20][3]))));
    tmp[21] = add(mul(v[0], m[21][0]), add(mul(v[1], m[21][1]), add(mul(v[2], m[21][2]), mul(v[3], m[21][3]))));
    tmp[22] = add(mul(v[0], m[22][0]), add(mul(v[1], m[22][1]), add(mul(v[2], m[22][2]), mul(v[3], m[22][3]))));
    tmp[23] = add(mul(v[0], m[23][0]), add(mul(v[1], m[23][1]), add(mul(v[2], m[23][2]), mul(v[3], m[23][3]))));
    tmp[24] = add(mul(v[0], m[24][0]), add(mul(v[1], m[24][1]), add(mul(v[2], m[24][2]), mul(v[3], m[24][3]))));
    tmp[25] = add(mul(v[0], m[25][0]), add(mul(v[1], m[25][1]), add(mul(v[2], m[25][2]), mul(v[3], m[25][3]))));
    tmp[26] = add(mul(v[0], m[26][0]), add(mul(v[1], m[26][1]), add(mul(v[2], m[26][2]), mul(v[3], m[26][3]))));
    tmp[27] = add(mul(v[0], m[27][0]), add(mul(v[1], m[27][1]), add(mul(v[2], m[27][2]), mul(v[3], m[27][3]))));
    tmp[28] = add(mul(v[0], m[28][0]), add(mul(v[1], m[28][1]), add(mul(v[2], m[28][2]), mul(v[3], m[28][3]))));
    tmp[29] = add(mul(v[0], m[29][0]), add(mul(v[1], m[29][1]), add(mul(v[2], m[29][2]), mul(v[3], m[29][3]))));
    tmp[30] = add(mul(v[0], m[30][0]), add(mul(v[1], m[30][1]), add(mul(v[2], m[30][2]), mul(v[3], m[30][3]))));
    tmp[31] = add(mul(v[0], m[31][0]), add(mul(v[1], m[31][1]), add(mul(v[2], m[31][2]), mul(v[3], m[31][3]))));

    v[0] = psi[I + d2];
    v[1] = psi[I + d0 + d2];
    v[2] = psi[I + d1 + d2];
    v[3] = psi[I + d0 + d1 + d2];

    tmp[0] = add(tmp[0], add(mul(v[0], m[0][4]), add(mul(v[1], m[0][5]), add(mul(v[2], m[0][6]), mul(v[3], m[0][7])))));
    tmp[1] = add(tmp[1], add(mul(v[0], m[1][4]), add(mul(v[1], m[1][5]), add(mul(v[2], m[1][6]), mul(v[3], m[1][7])))));
    tmp[2] = add(tmp[2], add(mul(v[0], m[2][4]), add(mul(v[1], m[2][5]), add(mul(v[2], m[2][6]), mul(v[3], m[2][7])))));
    tmp[3] = add(tmp[3], add(mul(v[0], m[3][4]), add(mul(v[1], m[3][5]), add(mul(v[2], m[3][6]), mul(v[3], m[3][7])))));
    tmp[4] = add(tmp[4], add(mul(v[0], m[4][4]), add(mul(v[1], m[4][5]), add(mul(v[2], m[4][6]), mul(v[3], m[4][7])))));
    tmp[5] = add(tmp[5], add(mul(v[0], m[5][4]), add(mul(v[1], m[5][5]), add(mul(v[2], m[5][6]), mul(v[3], m[5][7])))));
    tmp[6] = add(tmp[6], add(mul(v[0], m[6][4]), add(mul(v[1], m[6][5]), add(mul(v[2], m[6][6]), mul(v[3], m[6][7])))));
    tmp[7] = add(tmp[7], add(mul(v[0], m[7][4]), add(mul(v[1], m[7][5]), add(mul(v[2], m[7][6]), mul(v[3], m[7][7])))));
    tmp[8] = add(tmp[8], add(mul(v[0], m[8][4]), add(mul(v[1], m[8][5]), add(mul(v[2], m[8][6]), mul(v[3], m[8][7])))));
    tmp[9] = add(tmp[9], add(mul(v[0], m[9][4]), add(mul(v[1], m[9][5]), add(mul(v[2], m[9][6]), mul(v[3], m[9][7])))));
    tmp[10] = add(tmp[10], add(mul(v[0], m[10][4]), add(mul(v[1], m[10][5]), add(mul(v[2], m[10][6]), mul(v[3], m[10][7])))));
    tmp[11] = add(tmp[11], add(mul(v[0], m[11][4]), add(mul(v[1], m[11][5]), add(mul(v[2], m[11][6]), mul(v[3], m[11][7])))));
    tmp[12] = add(tmp[12], add(mul(v[0], m[12][4]), add(mul(v[1], m[12][5]), add(mul(v[2], m[12][6]), mul(v[3], m[12][7])))));
    tmp[13] = add(tmp[13], add(mul(v[0], m[13][4]), add(mul(v[1], m[13][5]), add(mul(v[2], m[13][6]), mul(v[3], m[13][7])))));
    tmp[14] = add(tmp[14], add(mul(v[0], m[14][4]), add(mul(v[1], m[14][5]), add(mul(v[2], m[14][6]), mul(v[3], m[14][7])))));
    tmp[15] = add(tmp[15], add(mul(v[0], m[15][4]), add(mul(v[1], m[15][5]), add(mul(v[2], m[15][6]), mul(v[3], m[15][7])))));
    tmp[16] = add(tmp[16], add(mul(v[0], m[16][4]), add(mul(v[1], m[16][5]), add(mul(v[2], m[16][6]), mul(v[3], m[16][7])))));
    tmp[17] = add(tmp[17], add(mul(v[0], m[17][4]), add(mul(v[1], m[17][5]), add(mul(v[2], m[17][6]), mul(v[3], m[17][7])))));
    tmp[18] = add(tmp[18], add(mul(v[0], m[18][4]), add(mul(v[1], m[18][5]), add(mul(v[2], m[18][6]), mul(v[3], m[18][7])))));
    tmp[19] = add(tmp[19], add(mul(v[0], m[19][4]), add(mul(v[1], m[19][5]), add(mul(v[2], m[19][6]), mul(v[3], m[19][7])))));
    tmp[20] = add(tmp[20], add(mul(v[0], m[20][4]), add(mul(v[1], m[20][5]), add(mul(v[2], m[20][6]), mul(v[3], m[20][7])))));
    tmp[21] = add(tmp[21], add(mul(v[0], m[21][4]), add(mul(v[1], m[21][5]), add(mul(v[2], m[21][6]), mul(v[3], m[21][7])))));
    tmp[22] = add(tmp[22], add(mul(v[0], m[22][4]), add(mul(v[1], m[22][5]), add(mul(v[2], m[22][6]), mul(v[3], m[22][7])))));
    tmp[23] = add(tmp[23], add(mul(v[0], m[23][4]), add(mul(v[1], m[23][5]), add(mul(v[2], m[23][6]), mul(v[3], m[23][7])))));
    tmp[24] = add(tmp[24], add(mul(v[0], m[24][4]), add(mul(v[1], m[24][5]), add(mul(v[2], m[24][6]), mul(v[3], m[24][7])))));
    tmp[25] = add(tmp[25], add(mul(v[0], m[25][4]), add(mul(v[1], m[25][5]), add(mul(v[2], m[25][6]), mul(v[3], m[25][7])))));
    tmp[26] = add(tmp[26], add(mul(v[0], m[26][4]), add(mul(v[1], m[26][5]), add(mul(v[2], m[26][6]), mul(v[3], m[26][7])))));
    tmp[27] = add(tmp[27], add(mul(v[0], m[27][4]), add(mul(v[1], m[27][5]), add(mul(v[2], m[27][6]), mul(v[3], m[27][7])))));
    tmp[28] = add(tmp[28], add(mul(v[0], m[28][4]), add(mul(v[1], m[28][5]), add(mul(v[2], m[28][6]), mul(v[3], m[28][7])))));
    tmp[29] = add(tmp[29], add(mul(v[0], m[29][4]), add(mul(v[1], m[29][5]), add(mul(v[2], m[29][6]), mul(v[3], m[29][7])))));
    tmp[30] = add(tmp[30], add(mul(v[0], m[30][4]), add(mul(v[1], m[30][5]), add(mul(v[2], m[30][6]), mul(v[3], m[30][7])))));
    tmp[31] = add(tmp[31], add(mul(v[0], m[31][4]), add(mul(v[1], m[31][5]), add(mul(v[2], m[31][6]), mul(v[3], m[31][7])))));

    v[0] = psi[I + d3];
    v[1] = psi[I + d0 + d3];
    v[2] = psi[I + d1 + d3];
    v[3] = psi[I + d0 + d1 + d3];

    tmp[0] = add(tmp[0], add(mul(v[0], m[0][8]), add(mul(v[1], m[0][9]), add(mul(v[2], m[0][10]), mul(v[3], m[0][11])))));
    tmp[1] = add(tmp[1], add(mul(v[0], m[1][8]), add(mul(v[1], m[1][9]), add(mul(v[2], m[1][10]), mul(v[3], m[1][11])))));
    tmp[2] = add(tmp[2], add(mul(v[0], m[2][8]), add(mul(v[1], m[2][9]), add(mul(v[2], m[2][10]), mul(v[3], m[2][11])))));
    tmp[3] = add(tmp[3], add(mul(v[0], m[3][8]), add(mul(v[1], m[3][9]), add(mul(v[2], m[3][10]), mul(v[3], m[3][11])))));
    tmp[4] = add(tmp[4], add(mul(v[0], m[4][8]), add(mul(v[1], m[4][9]), add(mul(v[2], m[4][10]), mul(v[3], m[4][11])))));
    tmp[5] = add(tmp[5], add(mul(v[0], m[5][8]), add(mul(v[1], m[5][9]), add(mul(v[2], m[5][10]), mul(v[3], m[5][11])))));
    tmp[6] = add(tmp[6], add(mul(v[0], m[6][8]), add(mul(v[1], m[6][9]), add(mul(v[2], m[6][10]), mul(v[3], m[6][11])))));
    tmp[7] = add(tmp[7], add(mul(v[0], m[7][8]), add(mul(v[1], m[7][9]), add(mul(v[2], m[7][10]), mul(v[3], m[7][11])))));
    tmp[8] = add(tmp[8], add(mul(v[0], m[8][8]), add(mul(v[1], m[8][9]), add(mul(v[2], m[8][10]), mul(v[3], m[8][11])))));
    tmp[9] = add(tmp[9], add(mul(v[0], m[9][8]), add(mul(v[1], m[9][9]), add(mul(v[2], m[9][10]), mul(v[3], m[9][11])))));
    tmp[10] = add(tmp[10], add(mul(v[0], m[10][8]), add(mul(v[1], m[10][9]), add(mul(v[2], m[10][10]), mul(v[3], m[10][11])))));
    tmp[11] = add(tmp[11], add(mul(v[0], m[11][8]), add(mul(v[1], m[11][9]), add(mul(v[2], m[11][10]), mul(v[3], m[11][11])))));
    tmp[12] = add(tmp[12], add(mul(v[0], m[12][8]), add(mul(v[1], m[12][9]), add(mul(v[2], m[12][10]), mul(v[3], m[12][11])))));
    tmp[13] = add(tmp[13], add(mul(v[0], m[13][8]), add(mul(v[1], m[13][9]), add(mul(v[2], m[13][10]), mul(v[3], m[13][11])))));
    tmp[14] = add(tmp[14], add(mul(v[0], m[14][8]), add(mul(v[1], m[14][9]), add(mul(v[2], m[14][10]), mul(v[3], m[14][11])))));
    tmp[15] = add(tmp[15], add(mul(v[0], m[15][8]), add(mul(v[1], m[15][9]), add(mul(v[2], m[15][10]), mul(v[3], m[15][11])))));
    tmp[16] = add(tmp[16], add(mul(v[0], m[16][8]), add(mul(v[1], m[16][9]), add(mul(v[2], m[16][10]), mul(v[3], m[16][11])))));
    tmp[17] = add(tmp[17], add(mul(v[0], m[17][8]), add(mul(v[1], m[17][9]), add(mul(v[2], m[17][10]), mul(v[3], m[17][11])))));
    tmp[18] = add(tmp[18], add(mul(v[0], m[18][8]), add(mul(v[1], m[18][9]), add(mul(v[2], m[18][10]), mul(v[3], m[18][11])))));
    tmp[19] = add(tmp[19], add(mul(v[0], m[19][8]), add(mul(v[1], m[19][9]), add(mul(v[2], m[19][10]), mul(v[3], m[19][11])))));
    tmp[20] = add(tmp[20], add(mul(v[0], m[20][8]), add(mul(v[1], m[20][9]), add(mul(v[2], m[20][10]), mul(v[3], m[20][11])))));
    tmp[21] = add(tmp[21], add(mul(v[0], m[21][8]), add(mul(v[1], m[21][9]), add(mul(v[2], m[21][10]), mul(v[3], m[21][11])))));
    tmp[22] = add(tmp[22], add(mul(v[0], m[22][8]), add(mul(v[1], m[22][9]), add(mul(v[2], m[22][10]), mul(v[3], m[22][11])))));
    tmp[23] = add(tmp[23], add(mul(v[0], m[23][8]), add(mul(v[1], m[23][9]), add(mul(v[2], m[23][10]), mul(v[3], m[23][11])))));
    tmp[24] = add(tmp[24], add(mul(v[0], m[24][8]), add(mul(v[1], m[24][9]), add(mul(v[2], m[24][10]), mul(v[3], m[24][11])))));
    tmp[25] = add(tmp[25], add(mul(v[0], m[25][8]), add(mul(v[1], m[25][9]), add(mul(v[2], m[25][10]), mul(v[3], m[25][11])))));
    tmp[26] = add(tmp[26], add(mul(v[0], m[26][8]), add(mul(v[1], m[26][9]), add(mul(v[2], m[26][10]), mul(v[3], m[26][11])))));
    tmp[27] = add(tmp[27], add(mul(v[0], m[27][8]), add(mul(v[1], m[27][9]), add(mul(v[2], m[27][10]), mul(v[3], m[27][11])))));
    tmp[28] = add(tmp[28], add(mul(v[0], m[28][8]), add(mul(v[1], m[28][9]), add(mul(v[2], m[28][10]), mul(v[3], m[28][11])))));
    tmp[29] = add(tmp[29], add(mul(v[0], m[29][8]), add(mul(v[1], m[29][9]), add(mul(v[2], m[29][10]), mul(v[3], m[29][11])))));
    tmp[30] = add(tmp[30], add(mul(v[0], m[30][8]), add(mul(v[1], m[30][9]), add(mul(v[2], m[30][10]), mul(v[3], m[30][11])))));
    tmp[31] = add(tmp[31], add(mul(v[0], m[31][8]), add(mul(v[1], m[31][9]), add(mul(v[2], m[31][10]), mul(v[3], m[31][11])))));

    v[0] = psi[I + d2 + d3];
    v[1] = psi[I + d0 + d2 + d3];
    v[2] = psi[I + d1 + d2 + d3];
    v[3] = psi[I + d0 + d1 + d2 + d3];

    tmp[0] = add(tmp[0], add(mul(v[0], m[0][12]), add(mul(v[1], m[0][13]), add(mul(v[2], m[0][14]), mul(v[3], m[0][15])))));
    tmp[1] = add(tmp[1], add(mul(v[0], m[1][12]), add(mul(v[1], m[1][13]), add(mul(v[2], m[1][14]), mul(v[3], m[1][15])))));
    tmp[2] = add(tmp[2], add(mul(v[0], m[2][12]), add(mul(v[1], m[2][13]), add(mul(v[2], m[2][14]), mul(v[3], m[2][15])))));
    tmp[3] = add(tmp[3], add(mul(v[0], m[3][12]), add(mul(v[1], m[3][13]), add(mul(v[2], m[3][14]), mul(v[3], m[3][15])))));
    tmp[4] = add(tmp[4], add(mul(v[0], m[4][12]), add(mul(v[1], m[4][13]), add(mul(v[2], m[4][14]), mul(v[3], m[4][15])))));
    tmp[5] = add(tmp[5], add(mul(v[0], m[5][12]), add(mul(v[1], m[5][13]), add(mul(v[2], m[5][14]), mul(v[3], m[5][15])))));
    tmp[6] = add(tmp[6], add(mul(v[0], m[6][12]), add(mul(v[1], m[6][13]), add(mul(v[2], m[6][14]), mul(v[3], m[6][15])))));
    tmp[7] = add(tmp[7], add(mul(v[0], m[7][12]), add(mul(v[1], m[7][13]), add(mul(v[2], m[7][14]), mul(v[3], m[7][15])))));
    tmp[8] = add(tmp[8], add(mul(v[0], m[8][12]), add(mul(v[1], m[8][13]), add(mul(v[2], m[8][14]), mul(v[3], m[8][15])))));
    tmp[9] = add(tmp[9], add(mul(v[0], m[9][12]), add(mul(v[1], m[9][13]), add(mul(v[2], m[9][14]), mul(v[3], m[9][15])))));
    tmp[10] = add(tmp[10], add(mul(v[0], m[10][12]), add(mul(v[1], m[10][13]), add(mul(v[2], m[10][14]), mul(v[3], m[10][15])))));
    tmp[11] = add(tmp[11], add(mul(v[0], m[11][12]), add(mul(v[1], m[11][13]), add(mul(v[2], m[11][14]), mul(v[3], m[11][15])))));
    tmp[12] = add(tmp[12], add(mul(v[0], m[12][12]), add(mul(v[1], m[12][13]), add(mul(v[2], m[12][14]), mul(v[3], m[12][15])))));
    tmp[13] = add(tmp[13], add(mul(v[0], m[13][12]), add(mul(v[1], m[13][13]), add(mul(v[2], m[13][14]), mul(v[3], m[13][15])))));
    tmp[14] = add(tmp[14], add(mul(v[0], m[14][12]), add(mul(v[1], m[14][13]), add(mul(v[2], m[14][14]), mul(v[3], m[14][15])))));
    tmp[15] = add(tmp[15], add(mul(v[0], m[15][12]), add(mul(v[1], m[15][13]), add(mul(v[2], m[15][14]), mul(v[3], m[15][15])))));
    tmp[16] = add(tmp[16], add(mul(v[0], m[16][12]), add(mul(v[1], m[16][13]), add(mul(v[2], m[16][14]), mul(v[3], m[16][15])))));
    tmp[17] = add(tmp[17], add(mul(v[0], m[17][12]), add(mul(v[1], m[17][13]), add(mul(v[2], m[17][14]), mul(v[3], m[17][15])))));
    tmp[18] = add(tmp[18], add(mul(v[0], m[18][12]), add(mul(v[1], m[18][13]), add(mul(v[2], m[18][14]), mul(v[3], m[18][15])))));
    tmp[19] = add(tmp[19], add(mul(v[0], m[19][12]), add(mul(v[1], m[19][13]), add(mul(v[2], m[19][14]), mul(v[3], m[19][15])))));
    tmp[20] = add(tmp[20], add(mul(v[0], m[20][12]), add(mul(v[1], m[20][13]), add(mul(v[2], m[20][14]), mul(v[3], m[20][15])))));
    tmp[21] = add(tmp[21], add(mul(v[0], m[21][12]), add(mul(v[1], m[21][13]), add(mul(v[2], m[21][14]), mul(v[3], m[21][15])))));
    tmp[22] = add(tmp[22], add(mul(v[0], m[22][12]), add(mul(v[1], m[22][13]), add(mul(v[2], m[22][14]), mul(v[3], m[22][15])))));
    tmp[23] = add(tmp[23], add(mul(v[0], m[23][12]), add(mul(v[1], m[23][13]), add(mul(v[2], m[23][14]), mul(v[3], m[23][15])))));
    tmp[24] = add(tmp[24], add(mul(v[0], m[24][12]), add(mul(v[1], m[24][13]), add(mul(v[2], m[24][14]), mul(v[3], m[24][15])))));
    tmp[25] = add(tmp[25], add(mul(v[0], m[25][12]), add(mul(v[1], m[25][13]), add(mul(v[2], m[25][14]), mul(v[3], m[25][15])))));
    tmp[26] = add(tmp[26], add(mul(v[0], m[26][12]), add(mul(v[1], m[26][13]), add(mul(v[2], m[26][14]), mul(v[3], m[26][15])))));
    tmp[27] = add(tmp[27], add(mul(v[0], m[27][12]), add(mul(v[1], m[27][13]), add(mul(v[2], m[27][14]), mul(v[3], m[27][15])))));
    tmp[28] = add(tmp[28], add(mul(v[0], m[28][12]), add(mul(v[1], m[28][13]), add(mul(v[2], m[28][14]), mul(v[3], m[28][15])))));
    tmp[29] = add(tmp[29], add(mul(v[0], m[29][12]), add(mul(v[1], m[29][13]), add(mul(v[2], m[29][14]), mul(v[3], m[29][15])))));
    tmp[30] = add(tmp[30], add(mul(v[0], m[30][12]), add(mul(v[1], m[30][13]), add(mul(v[2], m[30][14]), mul(v[3], m[30][15])))));
    tmp[31] = add(tmp[31], add(mul(v[0], m[31][12]), add(mul(v[1], m[31][13]), add(mul(v[2], m[31][14]), mul(v[3], m[31][15])))));

    v[0] = psi[I + d4];
    v[1] = psi[I + d0 + d4];
    v[2] = psi[I + d1 + d4];
    v[3] = psi[I + d0 + d1 + d4];

    tmp[0] = add(tmp[0], add(mul(v[0], m[0][16]), add(mul(v[1], m[0][17]), add(mul(v[2], m[0][18]), mul(v[3], m[0][19])))));
    tmp[1] = add(tmp[1], add(mul(v[0], m[1][16]), add(mul(v[1], m[1][17]), add(mul(v[2], m[1][18]), mul(v[3], m[1][19])))));
    tmp[2] = add(tmp[2], add(mul(v[0], m[2][16]), add(mul(v[1], m[2][17]), add(mul(v[2], m[2][18]), mul(v[3], m[2][19])))));
    tmp[3] = add(tmp[3], add(mul(v[0], m[3][16]), add(mul(v[1], m[3][17]), add(mul(v[2], m[3][18]), mul(v[3], m[3][19])))));
    tmp[4] = add(tmp[4], add(mul(v[0], m[4][16]), add(mul(v[1], m[4][17]), add(mul(v[2], m[4][18]), mul(v[3], m[4][19])))));
    tmp[5] = add(tmp[5], add(mul(v[0], m[5][16]), add(mul(v[1], m[5][17]), add(mul(v[2], m[5][18]), mul(v[3], m[5][19])))));
    tmp[6] = add(tmp[6], add(mul(v[0], m[6][16]), add(mul(v[1], m[6][17]), add(mul(v[2], m[6][18]), mul(v[3], m[6][19])))));
    tmp[7] = add(tmp[7], add(mul(v[0], m[7][16]), add(mul(v[1], m[7][17]), add(mul(v[2], m[7][18]), mul(v[3], m[7][19])))));
    tmp[8] = add(tmp[8], add(mul(v[0], m[8][16]), add(mul(v[1], m[8][17]), add(mul(v[2], m[8][18]), mul(v[3], m[8][19])))));
    tmp[9] = add(tmp[9], add(mul(v[0], m[9][16]), add(mul(v[1], m[9][17]), add(mul(v[2], m[9][18]), mul(v[3], m[9][19])))));
    tmp[10] = add(tmp[10], add(mul(v[0], m[10][16]), add(mul(v[1], m[10][17]), add(mul(v[2], m[10][18]), mul(v[3], m[10][19])))));
    tmp[11] = add(tmp[11], add(mul(v[0], m[11][16]), add(mul(v[1], m[11][17]), add(mul(v[2], m[11][18]), mul(v[3], m[11][19])))));
    tmp[12] = add(tmp[12], add(mul(v[0], m[12][16]), add(mul(v[1], m[12][17]), add(mul(v[2], m[12][18]), mul(v[3], m[12][19])))));
    tmp[13] = add(tmp[13], add(mul(v[0], m[13][16]), add(mul(v[1], m[13][17]), add(mul(v[2], m[13][18]), mul(v[3], m[13][19])))));
    tmp[14] = add(tmp[14], add(mul(v[0], m[14][16]), add(mul(v[1], m[14][17]), add(mul(v[2], m[14][18]), mul(v[3], m[14][19])))));
    tmp[15] = add(tmp[15], add(mul(v[0], m[15][16]), add(mul(v[1], m[15][17]), add(mul(v[2], m[15][18]), mul(v[3], m[15][19])))));
    tmp[16] = add(tmp[16], add(mul(v[0], m[16][16]), add(mul(v[1], m[16][17]), add(mul(v[2], m[16][18]), mul(v[3], m[16][19])))));
    tmp[17] = add(tmp[17], add(mul(v[0], m[17][16]), add(mul(v[1], m[17][17]), add(mul(v[2], m[17][18]), mul(v[3], m[17][19])))));
    tmp[18] = add(tmp[18], add(mul(v[0], m[18][16]), add(mul(v[1], m[18][17]), add(mul(v[2], m[18][18]), mul(v[3], m[18][19])))));
    tmp[19] = add(tmp[19], add(mul(v[0], m[19][16]), add(mul(v[1], m[19][17]), add(mul(v[2], m[19][18]), mul(v[3], m[19][19])))));
    tmp[20] = add(tmp[20], add(mul(v[0], m[20][16]), add(mul(v[1], m[20][17]), add(mul(v[2], m[20][18]), mul(v[3], m[20][19])))));
    tmp[21] = add(tmp[21], add(mul(v[0], m[21][16]), add(mul(v[1], m[21][17]), add(mul(v[2], m[21][18]), mul(v[3], m[21][19])))));
    tmp[22] = add(tmp[22], add(mul(v[0], m[22][16]), add(mul(v[1], m[22][17]), add(mul(v[2], m[22][18]), mul(v[3], m[22][19])))));
    tmp[23] = add(tmp[23], add(mul(v[0], m[23][16]), add(mul(v[1], m[23][17]), add(mul(v[2], m[23][18]), mul(v[3], m[23][19])))));
    tmp[24] = add(tmp[24], add(mul(v[0], m[24][16]), add(mul(v[1], m[24][17]), add(mul(v[2], m[24][18]), mul(v[3], m[24][19])))));
    tmp[25] = add(tmp[25], add(mul(v[0], m[25][16]), add(mul(v[1], m[25][17]), add(mul(v[2], m[25][18]), mul(v[3], m[25][19])))));
    tmp[26] = add(tmp[26], add(mul(v[0], m[26][16]), add(mul(v[1], m[26][17]), add(mul(v[2], m[26][18]), mul(v[3], m[26][19])))));
    tmp[27] = add(tmp[27], add(mul(v[0], m[27][16]), add(mul(v[1], m[27][17]), add(mul(v[2], m[27][18]), mul(v[3], m[27][19])))));
    tmp[28] = add(tmp[28], add(mul(v[0], m[28][16]), add(mul(v[1], m[28][17]), add(mul(v[2], m[28][18]), mul(v[3], m[28][19])))));
    tmp[29] = add(tmp[29], add(mul(v[0], m[29][16]), add(mul(v[1], m[29][17]), add(mul(v[2], m[29][18]), mul(v[3], m[29][19])))));
    tmp[30] = add(tmp[30], add(mul(v[0], m[30][16]), add(mul(v[1], m[30][17]), add(mul(v[2], m[30][18]), mul(v[3], m[30][19])))));
    tmp[31] = add(tmp[31], add(mul(v[0], m[31][16]), add(mul(v[1], m[31][17]), add(mul(v[2], m[31][18]), mul(v[3], m[31][19])))));

    v[0] = psi[I + d2 + d4];
    v[1] = psi[I + d0 + d2 + d4];
    v[2] = psi[I + d1 + d2 + d4];
    v[3] = psi[I + d0 + d1 + d2 + d4];

    tmp[0] = add(tmp[0], add(mul(v[0], m[0][20]), add(mul(v[1], m[0][21]), add(mul(v[2], m[0][22]), mul(v[3], m[0][23])))));
    tmp[1] = add(tmp[1], add(mul(v[0], m[1][20]), add(mul(v[1], m[1][21]), add(mul(v[2], m[1][22]), mul(v[3], m[1][23])))));
    tmp[2] = add(tmp[2], add(mul(v[0], m[2][20]), add(mul(v[1], m[2][21]), add(mul(v[2], m[2][22]), mul(v[3], m[2][23])))));
    tmp[3] = add(tmp[3], add(mul(v[0], m[3][20]), add(mul(v[1], m[3][21]), add(mul(v[2], m[3][22]), mul(v[3], m[3][23])))));
    tmp[4] = add(tmp[4], add(mul(v[0], m[4][20]), add(mul(v[1], m[4][21]), add(mul(v[2], m[4][22]), mul(v[3], m[4][23])))));
    tmp[5] = add(tmp[5], add(mul(v[0], m[5][20]), add(mul(v[1], m[5][21]), add(mul(v[2], m[5][22]), mul(v[3], m[5][23])))));
    tmp[6] = add(tmp[6], add(mul(v[0], m[6][20]), add(mul(v[1], m[6][21]), add(mul(v[2], m[6][22]), mul(v[3], m[6][23])))));
    tmp[7] = add(tmp[7], add(mul(v[0], m[7][20]), add(mul(v[1], m[7][21]), add(mul(v[2], m[7][22]), mul(v[3], m[7][23])))));
    tmp[8] = add(tmp[8], add(mul(v[0], m[8][20]), add(mul(v[1], m[8][21]), add(mul(v[2], m[8][22]), mul(v[3], m[8][23])))));
    tmp[9] = add(tmp[9], add(mul(v[0], m[9][20]), add(mul(v[1], m[9][21]), add(mul(v[2], m[9][22]), mul(v[3], m[9][23])))));
    tmp[10] = add(tmp[10], add(mul(v[0], m[10][20]), add(mul(v[1], m[10][21]), add(mul(v[2], m[10][22]), mul(v[3], m[10][23])))));
    tmp[11] = add(tmp[11], add(mul(v[0], m[11][20]), add(mul(v[1], m[11][21]), add(mul(v[2], m[11][22]), mul(v[3], m[11][23])))));
    tmp[12] = add(tmp[12], add(mul(v[0], m[12][20]), add(mul(v[1], m[12][21]), add(mul(v[2], m[12][22]), mul(v[3], m[12][23])))));
    tmp[13] = add(tmp[13], add(mul(v[0], m[13][20]), add(mul(v[1], m[13][21]), add(mul(v[2], m[13][22]), mul(v[3], m[13][23])))));
    tmp[14] = add(tmp[14], add(mul(v[0], m[14][20]), add(mul(v[1], m[14][21]), add(mul(v[2], m[14][22]), mul(v[3], m[14][23])))));
    tmp[15] = add(tmp[15], add(mul(v[0], m[15][20]), add(mul(v[1], m[15][21]), add(mul(v[2], m[15][22]), mul(v[3], m[15][23])))));
    tmp[16] = add(tmp[16], add(mul(v[0], m[16][20]), add(mul(v[1], m[16][21]), add(mul(v[2], m[16][22]), mul(v[3], m[16][23])))));
    tmp[17] = add(tmp[17], add(mul(v[0], m[17][20]), add(mul(v[1], m[17][21]), add(mul(v[2], m[17][22]), mul(v[3], m[17][23])))));
    tmp[18] = add(tmp[18], add(mul(v[0], m[18][20]), add(mul(v[1], m[18][21]), add(mul(v[2], m[18][22]), mul(v[3], m[18][23])))));
    tmp[19] = add(tmp[19], add(mul(v[0], m[19][20]), add(mul(v[1], m[19][21]), add(mul(v[2], m[19][22]), mul(v[3], m[19][23])))));
    tmp[20] = add(tmp[20], add(mul(v[0], m[20][20]), add(mul(v[1], m[20][21]), add(mul(v[2], m[20][22]), mul(v[3], m[20][23])))));
    tmp[21] = add(tmp[21], add(mul(v[0], m[21][20]), add(mul(v[1], m[21][21]), add(mul(v[2], m[21][22]), mul(v[3], m[21][23])))));
    tmp[22] = add(tmp[22], add(mul(v[0], m[22][20]), add(mul(v[1], m[22][21]), add(mul(v[2], m[22][22]), mul(v[3], m[22][23])))));
    tmp[23] = add(tmp[23], add(mul(v[0], m[23][20]), add(mul(v[1], m[23][21]), add(mul(v[2], m[23][22]), mul(v[3], m[23][23])))));
    tmp[24] = add(tmp[24], add(mul(v[0], m[24][20]), add(mul(v[1], m[24][21]), add(mul(v[2], m[24][22]), mul(v[3], m[24][23])))));
    tmp[25] = add(tmp[25], add(mul(v[0], m[25][20]), add(mul(v[1], m[25][21]), add(mul(v[2], m[25][22]), mul(v[3], m[25][23])))));
    tmp[26] = add(tmp[26], add(mul(v[0], m[26][20]), add(mul(v[1], m[26][21]), add(mul(v[2], m[26][22]), mul(v[3], m[26][23])))));
    tmp[27] = add(tmp[27], add(mul(v[0], m[27][20]), add(mul(v[1], m[27][21]), add(mul(v[2], m[27][22]), mul(v[3], m[27][23])))));
    tmp[28] = add(tmp[28], add(mul(v[0], m[28][20]), add(mul(v[1], m[28][21]), add(mul(v[2], m[28][22]), mul(v[3], m[28][23])))));
    tmp[29] = add(tmp[29], add(mul(v[0], m[29][20]), add(mul(v[1], m[29][21]), add(mul(v[2], m[29][22]), mul(v[3], m[29][23])))));
    tmp[30] = add(tmp[30], add(mul(v[0], m[30][20]), add(mul(v[1], m[30][21]), add(mul(v[2], m[30][22]), mul(v[3], m[30][23])))));
    tmp[31] = add(tmp[31], add(mul(v[0], m[31][20]), add(mul(v[1], m[31][21]), add(mul(v[2], m[31][22]), mul(v[3], m[31][23])))));

    v[0] = psi[I + d3 + d4];
    v[1] = psi[I + d0 + d3 + d4];
    v[2] = psi[I + d1 + d3 + d4];
    v[3] = psi[I + d0 + d1 + d3 + d4];

    tmp[0] = add(tmp[0], add(mul(v[0], m[0][24]), add(mul(v[1], m[0][25]), add(mul(v[2], m[0][26]), mul(v[3], m[0][27])))));
    tmp[1] = add(tmp[1], add(mul(v[0], m[1][24]), add(mul(v[1], m[1][25]), add(mul(v[2], m[1][26]), mul(v[3], m[1][27])))));
    tmp[2] = add(tmp[2], add(mul(v[0], m[2][24]), add(mul(v[1], m[2][25]), add(mul(v[2], m[2][26]), mul(v[3], m[2][27])))));
    tmp[3] = add(tmp[3], add(mul(v[0], m[3][24]), add(mul(v[1], m[3][25]), add(mul(v[2], m[3][26]), mul(v[3], m[3][27])))));
    tmp[4] = add(tmp[4], add(mul(v[0], m[4][24]), add(mul(v[1], m[4][25]), add(mul(v[2], m[4][26]), mul(v[3], m[4][27])))));
    tmp[5] = add(tmp[5], add(mul(v[0], m[5][24]), add(mul(v[1], m[5][25]), add(mul(v[2], m[5][26]), mul(v[3], m[5][27])))));
    tmp[6] = add(tmp[6], add(mul(v[0], m[6][24]), add(mul(v[1], m[6][25]), add(mul(v[2], m[6][26]), mul(v[3], m[6][27])))));
    tmp[7] = add(tmp[7], add(mul(v[0], m[7][24]), add(mul(v[1], m[7][25]), add(mul(v[2], m[7][26]), mul(v[3], m[7][27])))));
    tmp[8] = add(tmp[8], add(mul(v[0], m[8][24]), add(mul(v[1], m[8][25]), add(mul(v[2], m[8][26]), mul(v[3], m[8][27])))));
    tmp[9] = add(tmp[9], add(mul(v[0], m[9][24]), add(mul(v[1], m[9][25]), add(mul(v[2], m[9][26]), mul(v[3], m[9][27])))));
    tmp[10] = add(tmp[10], add(mul(v[0], m[10][24]), add(mul(v[1], m[10][25]), add(mul(v[2], m[10][26]), mul(v[3], m[10][27])))));
    tmp[11] = add(tmp[11], add(mul(v[0], m[11][24]), add(mul(v[1], m[11][25]), add(mul(v[2], m[11][26]), mul(v[3], m[11][27])))));
    tmp[12] = add(tmp[12], add(mul(v[0], m[12][24]), add(mul(v[1], m[12][25]), add(mul(v[2], m[12][26]), mul(v[3], m[12][27])))));
    tmp[13] = add(tmp[13], add(mul(v[0], m[13][24]), add(mul(v[1], m[13][25]), add(mul(v[2], m[13][26]), mul(v[3], m[13][27])))));
    tmp[14] = add(tmp[14], add(mul(v[0], m[14][24]), add(mul(v[1], m[14][25]), add(mul(v[2], m[14][26]), mul(v[3], m[14][27])))));
    tmp[15] = add(tmp[15], add(mul(v[0], m[15][24]), add(mul(v[1], m[15][25]), add(mul(v[2], m[15][26]), mul(v[3], m[15][27])))));
    tmp[16] = add(tmp[16], add(mul(v[0], m[16][24]), add(mul(v[1], m[16][25]), add(mul(v[2], m[16][26]), mul(v[3], m[16][27])))));
    tmp[17] = add(tmp[17], add(mul(v[0], m[17][24]), add(mul(v[1], m[17][25]), add(mul(v[2], m[17][26]), mul(v[3], m[17][27])))));
    tmp[18] = add(tmp[18], add(mul(v[0], m[18][24]), add(mul(v[1], m[18][25]), add(mul(v[2], m[18][26]), mul(v[3], m[18][27])))));
    tmp[19] = add(tmp[19], add(mul(v[0], m[19][24]), add(mul(v[1], m[19][25]), add(mul(v[2], m[19][26]), mul(v[3], m[19][27])))));
    tmp[20] = add(tmp[20], add(mul(v[0], m[20][24]), add(mul(v[1], m[20][25]), add(mul(v[2], m[20][26]), mul(v[3], m[20][27])))));
    tmp[21] = add(tmp[21], add(mul(v[0], m[21][24]), add(mul(v[1], m[21][25]), add(mul(v[2], m[21][26]), mul(v[3], m[21][27])))));
    tmp[22] = add(tmp[22], add(mul(v[0], m[22][24]), add(mul(v[1], m[22][25]), add(mul(v[2], m[22][26]), mul(v[3], m[22][27])))));
    tmp[23] = add(tmp[23], add(mul(v[0], m[23][24]), add(mul(v[1], m[23][25]), add(mul(v[2], m[23][26]), mul(v[3], m[23][27])))));
    tmp[24] = add(tmp[24], add(mul(v[0], m[24][24]), add(mul(v[1], m[24][25]), add(mul(v[2], m[24][26]), mul(v[3], m[24][27])))));
    tmp[25] = add(tmp[25], add(mul(v[0], m[25][24]), add(mul(v[1], m[25][25]), add(mul(v[2], m[25][26]), mul(v[3], m[25][27])))));
    tmp[26] = add(tmp[26], add(mul(v[0], m[26][24]), add(mul(v[1], m[26][25]), add(mul(v[2], m[26][26]), mul(v[3], m[26][27])))));
    tmp[27] = add(tmp[27], add(mul(v[0], m[27][24]), add(mul(v[1], m[27][25]), add(mul(v[2], m[27][26]), mul(v[3], m[27][27])))));
    tmp[28] = add(tmp[28], add(mul(v[0], m[28][24]), add(mul(v[1], m[28][25]), add(mul(v[2], m[28][26]), mul(v[3], m[28][27])))));
    tmp[29] = add(tmp[29], add(mul(v[0], m[29][24]), add(mul(v[1], m[29][25]), add(mul(v[2], m[29][26]), mul(v[3], m[29][27])))));
    tmp[30] = add(tmp[30], add(mul(v[0], m[30][24]), add(mul(v[1], m[30][25]), add(mul(v[2], m[30][26]), mul(v[3], m[30][27])))));
    tmp[31] = add(tmp[31], add(mul(v[0], m[31][24]), add(mul(v[1], m[31][25]), add(mul(v[2], m[31][26]), mul(v[3], m[31][27])))));

    v[0] = psi[I + d2 + d3 + d4];
    v[1] = psi[I + d0 + d2 + d3 + d4];
    v[2] = psi[I + d1 + d2 + d3 + d4];
    v[3] = psi[I + d0 + d1 + d2 + d3 + d4];

    psi[I] = (add(tmp[0], add(mul(v[0], m[0][28]), add(mul(v[1], m[0][29]), add(mul(v[2], m[0][30]), mul(v[3], m[0][31]))))));
    psi[I + d0] = (add(tmp[1], add(mul(v[0], m[1][28]), add(mul(v[1], m[1][29]), add(mul(v[2], m[1][30]), mul(v[3], m[1][31]))))));
    psi[I + d1] = (add(tmp[2], add(mul(v[0], m[2][28]), add(mul(v[1], m[2][29]), add(mul(v[2], m[2][30]), mul(v[3], m[2][31]))))));
    psi[I + d0 + d1] = (add(tmp[3], add(mul(v[0], m[3][28]), add(mul(v[1], m[3][29]), add(mul(v[2], m[3][30]), mul(v[3], m[3][31]))))));
    psi[I + d2] = (add(tmp[4], add(mul(v[0], m[4][28]), add(mul(v[1], m[4][29]), add(mul(v[2], m[4][30]), mul(v[3], m[4][31]))))));
    psi[I + d0 + d2] = (add(tmp[5], add(mul(v[0], m[5][28]), add(mul(v[1], m[5][29]), add(mul(v[2], m[5][30]), mul(v[3], m[5][31]))))));
    psi[I + d1 + d2] = (add(tmp[6], add(mul(v[0], m[6][28]), add(mul(v[1], m[6][29]), add(mul(v[2], m[6][30]), mul(v[3], m[6][31]))))));
    psi[I + d0 + d1 + d2] = (add(tmp[7], add(mul(v[0], m[7][28]), add(mul(v[1], m[7][29]), add(mul(v[2], m[7][30]), mul(v[3], m[7][31]))))));
    psi[I + d3] = (add(tmp[8], add(mul(v[0], m[8][28]), add(mul(v[1], m[8][29]), add(mul(v[2], m[8][30]), mul(v[3], m[8][31]))))));
    psi[I + d0 + d3] = (add(tmp[9], add(mul(v[0], m[9][28]), add(mul(v[1], m[9][29]), add(mul(v[2], m[9][30]), mul(v[3], m[9][31]))))));
    psi[I + d1 + d3] = (add(tmp[10], add(mul(v[0], m[10][28]), add(mul(v[1], m[10][29]), add(mul(v[2], m[10][30]), mul(v[3], m[10][31]))))));
    psi[I + d0 + d1 + d3] = (add(tmp[11], add(mul(v[0], m[11][28]), add(mul(v[1], m[11][29]), add(mul(v[2], m[11][30]), mul(v[3], m[11][31]))))));
    psi[I + d2 + d3] = (add(tmp[12], add(mul(v[0], m[12][28]), add(mul(v[1], m[12][29]), add(mul(v[2], m[12][30]), mul(v[3], m[12][31]))))));
    psi[I + d0 + d2 + d3] = (add(tmp[13], add(mul(v[0], m[13][28]), add(mul(v[1], m[13][29]), add(mul(v[2], m[13][30]), mul(v[3], m[13][31]))))));
    psi[I + d1 + d2 + d3] = (add(tmp[14], add(mul(v[0], m[14][28]), add(mul(v[1], m[14][29]), add(mul(v[2], m[14][30]), mul(v[3], m[14][31]))))));
    psi[I + d0 + d1 + d2 + d3] = (add(tmp[15], add(mul(v[0], m[15][28]), add(mul(v[1], m[15][29]), add(mul(v[2], m[15][30]), mul(v[3], m[15][31]))))));
    psi[I + d4] = (add(tmp[16], add(mul(v[0], m[16][28]), add(mul(v[1], m[16][29]), add(mul(v[2], m[16][30]), mul(v[3], m[16][31]))))));
    psi[I + d0 + d4] = (add(tmp[17], add(mul(v[0], m[17][28]), add(mul(v[1], m[17][29]), add(mul(v[2], m[17][30]), mul(v[3], m[17][31]))))));
    psi[I + d1 + d4] = (add(tmp[18], add(mul(v[0], m[18][28]), add(mul(v[1], m[18][29]), add(mul(v[2], m[18][30]), mul(v[3], m[18][31]))))));
    psi[I + d0 + d1 + d4] = (add(tmp[19], add(mul(v[0], m[19][28]), add(mul(v[1], m[19][29]), add(mul(v[2], m[19][30]), mul(v[3], m[19][31]))))));
    psi[I + d2 + d4] = (add(tmp[20], add(mul(v[0], m[20][28]), add(mul(v[1], m[20][29]), add(mul(v[2], m[20][30]), mul(v[3], m[20][31]))))));
    psi[I + d0 + d2 + d4] = (add(tmp[21], add(mul(v[0], m[21][28]), add(mul(v[1], m[21][29]), add(mul(v[2], m[21][30]), mul(v[3], m[21][31]))))));
    psi[I + d1 + d2 + d4] = (add(tmp[22], add(mul(v[0], m[22][28]), add(mul(v[1], m[22][29]), add(mul(v[2], m[22][30]), mul(v[3], m[22][31]))))));
    psi[I + d0 + d1 + d2 + d4] = (add(tmp[23], add(mul(v[0], m[23][28]), add(mul(v[1], m[23][29]), add(mul(v[2], m[23][30]), mul(v[3], m[23][31]))))));
    psi[I + d3 + d4] = (add(tmp[24], add(mul(v[0], m[24][28]), add(mul(v[1], m[24][29]), add(mul(v[2], m[24][30]), mul(v[3], m[24][31]))))));
    psi[I + d0 + d3 + d4] = (add(tmp[25], add(mul(v[0], m[25][28]), add(mul(v[1], m[25][29]), add(mul(v[2], m[25][30]), mul(v[3], m[25][31]))))));
    psi[I + d1 + d3 + d4] = (add(tmp[26], add(mul(v[0], m[26][28]), add(mul(v[1], m[26][29]), add(mul(v[2], m[26][30]), mul(v[3], m[26][31]))))));
    psi[I + d0 + d1 + d3 + d4] = (add(tmp[27], add(mul(v[0], m[27][28]), add(mul(v[1], m[27][29]), add(mul(v[2], m[27][30]), mul(v[3], m[27][31]))))));
    psi[I + d2 + d3 + d4] = (add(tmp[28], add(mul(v[0], m[28][28]), add(mul(v[1], m[28][29]), add(mul(v[2], m[28][30]), mul(v[3], m[28][31]))))));
    psi[I + d0 + d2 + d3 + d4] = (add(tmp[29], add(mul(v[0], m[29][28]), add(mul(v[1], m[29][29]), add(mul(v[2], m[29][30]), mul(v[3], m[29][31]))))));
    psi[I + d1 + d2 + d3 + d4] = (add(tmp[30], add(mul(v[0], m[30][28]), add(mul(v[1], m[30][29]), add(mul(v[2], m[30][30]), mul(v[3], m[30][31]))))));
    psi[I + d0 + d1 + d2 + d3 + d4] = (add(tmp[31], add(mul(v[0], m[31][28]), add(mul(v[1], m[31][29]), add(mul(v[2], m[31][30]), mul(v[3], m[31][31]))))));

}

// bit indices id[.] are given from high to low (e.g. control first for CNOT)
template <class V, class M>
void kernel(V &psi, unsigned id4, unsigned id3, unsigned id2, unsigned id1, unsigned id0, M const& m, std::size_t ctrlmask)
{
    std::size_t n = psi.size();
    std::size_t d0 = 1UL << id0;
    std::size_t d1 = 1UL << id1;
    std::size_t d2 = 1UL << id2;
    std::size_t d3 = 1UL << id3;
    std::size_t d4 = 1UL << id4;
    std::size_t dsorted[] = {d0 , d1, d2, d3, d4};
    std::sort(dsorted, dsorted + 5, std::greater<std::size_t>());

    if (ctrlmask == 0){
        #pragma omp for collapse(LOOP_COLLAPSE5) schedule(static)
        for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
            for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
                for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
                    for (std::size_t i3 = 0; i3 < dsorted[2]; i3 += 2 * dsorted[3]){
                        for (std::size_t i4 = 0; i4 < dsorted[3]; i4 += 2 * dsorted[4]){
                            for (std::size_t i5 = 0; i5 < dsorted[4]; ++i5){
                                kernel_core(psi, i0 + i1 + i2 + i3 + i4 + i5, d0, d1, d2, d3, d4, m);
                            }
                        }
                    }
                }
            }
        }
    }
    else{
        #pragma omp for collapse(LOOP_COLLAPSE5) schedule(static)
        for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
            for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
                for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
                    for (std::size_t i3 = 0; i3 < dsorted[2]; i3 += 2 * dsorted[3]){
                        for (std::size_t i4 = 0; i4 < dsorted[3]; i4 += 2 * dsorted[4]){
                            for (std::size_t i5 = 0; i5 < dsorted[4]; ++i5){
                                if (((i0 + i1 + i2 + i3 + i4 + i5)&ctrlmask) == ctrlmask)
                                    kernel_core(psi, i0 + i1 + i2 + i3 + i4 + i5, d0, d1, d2, d3, d4, m);
                            }
                        }
                    }
                }
            }
        }
    }
}

