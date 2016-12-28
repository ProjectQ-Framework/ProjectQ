template <class V, class M>
inline void kernel_core(V &psi, unsigned I, unsigned d0, unsigned d1, unsigned d2, M const& m, M const& mt)
{
	__m256d v[4];

	v[0] = load2(&psi[I]);
	v[1] = load2(&psi[I + d0]);
	v[2] = load2(&psi[I + d1]);
	v[3] = load2(&psi[I + d0 + d1]);

	__m256d tmp[4];

	tmp[0] = add(mul(v[0], m[0], mt[0]), add(mul(v[1], m[1], mt[1]), add(mul(v[2], m[2], mt[2]), mul(v[3], m[3], mt[3]))));
	tmp[1] = add(mul(v[0], m[4], mt[4]), add(mul(v[1], m[5], mt[5]), add(mul(v[2], m[6], mt[6]), mul(v[3], m[7], mt[7]))));
	tmp[2] = add(mul(v[0], m[8], mt[8]), add(mul(v[1], m[9], mt[9]), add(mul(v[2], m[10], mt[10]), mul(v[3], m[11], mt[11]))));
	tmp[3] = add(mul(v[0], m[12], mt[12]), add(mul(v[1], m[13], mt[13]), add(mul(v[2], m[14], mt[14]), mul(v[3], m[15], mt[15]))));

	v[0] = load2(&psi[I + d2]);
	v[1] = load2(&psi[I + d0 + d2]);
	v[2] = load2(&psi[I + d1 + d2]);
	v[3] = load2(&psi[I + d0 + d1 + d2]);

	_mm256_storeu2_m128d((double*)&psi[I + d0], (double*)&psi[I], add(tmp[0], add(mul(v[0], m[16], mt[16]), add(mul(v[1], m[17], mt[17]), add(mul(v[2], m[18], mt[18]), mul(v[3], m[19], mt[19]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1], (double*)&psi[I + d1], add(tmp[1], add(mul(v[0], m[20], mt[20]), add(mul(v[1], m[21], mt[21]), add(mul(v[2], m[22], mt[22]), mul(v[3], m[23], mt[23]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d2], (double*)&psi[I + d2], add(tmp[2], add(mul(v[0], m[24], mt[24]), add(mul(v[1], m[25], mt[25]), add(mul(v[2], m[26], mt[26]), mul(v[3], m[27], mt[27]))))));
	_mm256_storeu2_m128d((double*)&psi[I + d0 + d1 + d2], (double*)&psi[I + d1 + d2], add(tmp[3], add(mul(v[0], m[28], mt[28]), add(mul(v[1], m[29], mt[29]), add(mul(v[2], m[30], mt[30]), mul(v[3], m[31], mt[31]))))));

}

// bit indices id[.] are given from high to low (e.g. control first for CNOT)
template <class V, class M>
void kernel(V &psi, unsigned id2, unsigned id1, unsigned id0, M const& m, std::size_t ctrlmask)
{
	std::size_t n = psi.size();
	std::size_t d0 = 1UL << id0;
	std::size_t d1 = 1UL << id1;
	std::size_t d2 = 1UL << id2;

	__m256d mm[] = {load(&m[0][0], &m[1][0]), load(&m[0][1], &m[1][1]), load(&m[0][2], &m[1][2]), load(&m[0][3], &m[1][3]), load(&m[2][0], &m[3][0]), load(&m[2][1], &m[3][1]), load(&m[2][2], &m[3][2]), load(&m[2][3], &m[3][3]), load(&m[4][0], &m[5][0]), load(&m[4][1], &m[5][1]), load(&m[4][2], &m[5][2]), load(&m[4][3], &m[5][3]), load(&m[6][0], &m[7][0]), load(&m[6][1], &m[7][1]), load(&m[6][2], &m[7][2]), load(&m[6][3], &m[7][3]), load(&m[0][4], &m[1][4]), load(&m[0][5], &m[1][5]), load(&m[0][6], &m[1][6]), load(&m[0][7], &m[1][7]), load(&m[2][4], &m[3][4]), load(&m[2][5], &m[3][5]), load(&m[2][6], &m[3][6]), load(&m[2][7], &m[3][7]), load(&m[4][4], &m[5][4]), load(&m[4][5], &m[5][5]), load(&m[4][6], &m[5][6]), load(&m[4][7], &m[5][7]), load(&m[6][4], &m[7][4]), load(&m[6][5], &m[7][5]), load(&m[6][6], &m[7][6]), load(&m[6][7], &m[7][7])};
	__m256d mmt[32];

	__m256d neg = _mm256_setr_pd(1.0, -1.0, 1.0, -1.0);
	for (unsigned i = 0; i < 32; ++i){
		auto badc = _mm256_permute_pd(mm[i], 5);
		mmt[i] = _mm256_mul_pd(badc, neg);
	}

	std::size_t dsorted[] = {d0 , d1, d2};
	std::sort(dsorted, dsorted + 3, std::greater<std::size_t>());

	if (ctrlmask == 0){
		#pragma omp for collapse(LOOP_COLLAPSE3) schedule(static)
		for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
			for (std::size_t i1 = 0; i1 < dsorted[0]; i1 += 2 * dsorted[1]){
				for (std::size_t i2 = 0; i2 < dsorted[1]; i2 += 2 * dsorted[2]){
					for (std::size_t i3 = 0; i3 < dsorted[2]; ++i3){
						kernel_core(psi, i0 + i1 + i2 + i3, d0, d1, d2, mm, mmt);
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
							kernel_core(psi, i0 + i1 + i2 + i3, d0, d1, d2, mm, mmt);
					}
				}
			}
		}
	}
}

