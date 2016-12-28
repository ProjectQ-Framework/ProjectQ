template <class V, class M>
inline void kernel_core(V &psi, unsigned I, unsigned d0, M const& m)
{
	std::complex<double> v[2];
	v[0] = psi[I];
	v[1] = psi[I + d0];

	psi[I] = (add(mul(v[0], m[0][0]), mul(v[1], m[0][1])));
	psi[I + d0] = (add(mul(v[0], m[1][0]), mul(v[1], m[1][1])));

}

// bit indices id[.] are given from high to low (e.g. control first for CNOT)
template <class V, class M>
void kernel(V &psi, unsigned id0, M const& m, std::size_t ctrlmask)
{
	std::size_t n = psi.size();
	std::size_t d0 = 1UL << id0;
	std::size_t dsorted[] = {d0 };
	std::sort(dsorted, dsorted + 1, std::greater<std::size_t>());

	if (ctrlmask == 0){
		#pragma omp for collapse(LOOP_COLLAPSE1) schedule(static)
		for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
			for (std::size_t i1 = 0; i1 < dsorted[0]; ++i1){
				kernel_core(psi, i0 + i1, d0, m);
			}
		}
	}
	else{
		#pragma omp for collapse(LOOP_COLLAPSE1) schedule(static)
		for (std::size_t i0 = 0; i0 < n; i0 += 2 * dsorted[0]){
			for (std::size_t i1 = 0; i1 < dsorted[0]; ++i1){
				if (((i0 + i1)&ctrlmask) == ctrlmask)
					kernel_core(psi, i0 + i1, d0, m);
			}
		}
	}
}

