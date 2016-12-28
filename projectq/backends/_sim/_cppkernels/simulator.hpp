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

#ifndef SIMULATOR_HPP_
#define SIMULATOR_HPP_

#include <vector>
#include <complex>

#if defined(NOINTRIN) || !defined(INTRIN)
#include "nointrin/kernels.hpp"
#else
#include "intrin/kernels.hpp"
#endif

#include "intrin/alignedallocator.hpp"
#include "fusion.hpp"
#include <map>
#include <cassert>
#include <algorithm>
#include <tuple>
#include <random>
#include <functional>


class Simulator{
public:
	using calc_type = double;
	using complex_type = std::complex<calc_type>;
	using StateVector = std::vector<complex_type, aligned_allocator<complex_type,64>>;
	using Map = std::map<unsigned, unsigned>;
	using RndEngine = std::mt19937;
	
	Simulator(unsigned seed = 1) : N_(0), vec_(1,0.), fusion_qubits_min_(4), fusion_qubits_max_(5), rnd_eng_(seed) {
		vec_[0]=1.; // all-zero initial state
		std::uniform_real_distribution<double> dist(0., 1.);
		rng_ = std::bind(dist, std::ref(rnd_eng_));
	}
	
	void allocate_qubit(unsigned id){
		if (map_.count(id) == 0){
			map_[id] = N_++;
			auto newvec = StateVector(1UL << N_);
			#pragma omp parallel for schedule(static)
			for (std::size_t i = 0; i < newvec.size(); ++i)
				newvec[i] = (i < vec_.size())?vec_[i]:0.;
			vec_ = std::move(newvec);
		}
		else
			throw(std::runtime_error("AllocateQubit: ID already exists. Qubit IDs should be unique."));
	}
	
	bool get_classical_value(unsigned id, calc_type tol = 1.e-12){
		unsigned pos = map_[id];
		std::size_t delta = (1UL << pos);
		
		for (std::size_t i = 0; i < vec_.size(); i += 2*delta){
			for (std::size_t j = 0; j < delta; ++j){
				if (std::norm(vec_[i+j]) > tol)
					return false;
				if (std::norm(vec_[i+j+delta]) > tol)
					return true;
			}
		}
		assert(false); // this will never happen
		return false; // suppress 'control reaches end of non-void...'
	}
	
	bool is_classical(unsigned id, calc_type tol = 1.e-12){
		run();
		unsigned pos = map_[id];
		std::size_t delta = (1UL << pos);
		
		short up = 0, down = 0;
		#pragma omp parallel for schedule(static) reduction(|:up,down)
		for (std::size_t i = 0; i < vec_.size(); i += 2*delta){
			for (std::size_t j = 0; j < delta; ++j){
				up = up | ((std::norm(vec_[i+j]) > tol)&1);
				down = down | ((std::norm(vec_[i+j+delta]) > tol)&1);
			}
		}
		
		return 1 == (up^down);
	}
	
	void collapse_vector(unsigned id, bool value = false, bool shrink = false){
		run();
		unsigned pos = map_[id];
		std::size_t delta = (1UL << pos);
		
		if (!shrink){
			#pragma omp parallel for schedule(static)
			for (std::size_t i = 0; i < vec_.size(); i += 2*delta){
				for (std::size_t j = 0; j < delta; ++j)
					vec_[i+j+static_cast<unsigned>(!value)*delta] = 0.;
			}
		}
		else{
			StateVector newvec((1UL << (N_-1)));
			#pragma omp parallel for schedule(static)
			for (std::size_t i = 0; i < vec_.size(); i += 2*delta)
				std::copy_n(&vec_[i + static_cast<unsigned>(value)*delta], delta, &newvec[i/2]);
			vec_ = std::move(newvec);
			
			for (auto& p : map_){
				if (p.second > pos)
					p.second--;
			}
			map_.erase(id);
			N_--;
		}
	}
	
	void measure_qubits(std::vector<unsigned> const& ids, std::vector<bool> &res){
		run();
		
		std::vector<unsigned> positions(ids.size());
		for (unsigned i = 0; i < ids.size(); ++i)
			positions[i] = map_[ids[i]];
			
		calc_type P = 0.;
		calc_type rnd = rng_();
		
		// pick entry at random with probability |entry|^2
		unsigned pick = 0;
		while (P < rnd && pick < vec_.size())
			P += std::norm(vec_[pick++]);
		
		pick--;
		// determine result vector (boolean values for each qubit)
		// and create mask to detect bad entries (i.e., entries that don't agree with measurement)
		res = std::vector<bool>(ids.size());
		std::size_t mask = 0;
		std::size_t val = 0;
		for (unsigned i = 0; i < ids.size(); ++i){
			bool r = ((pick >> positions[i]) & 1) == 1;
			res[i] = r;
			mask |= (1UL << positions[i]);
			val |= (static_cast<std::size_t>(r&1) << positions[i]);
		}
		// set bad entries to 0
		calc_type N = 0.;
		#pragma omp parallel for reduction(+:N) schedule(static)
		for (std::size_t i = 0; i < vec_.size(); ++i){
			if ((i & mask) != val)
				vec_[i] = 0.;
			else
				N += std::norm(vec_[i]);
		}
		// re-normalize
		N = 1./std::sqrt(N);
		#pragma omp parallel for schedule(static)
		for (std::size_t i = 0; i < vec_.size(); ++i)
			vec_[i] *= N;
	}
	
	std::vector<bool> measure_qubits_return(std::vector<unsigned> const& ids){
		std::vector<bool> ret;
		measure_qubits(ids, ret);
		return ret;
	}
	void deallocate_qubit(unsigned id){
		run();
		assert(map_.count(id) == 1);
		if (!is_classical(id))
			throw(std::runtime_error("Error: Qubit has not been measured / uncomputed! There is most likely a bug in your code."));
		
		bool value = get_classical_value(id);
		collapse_vector(id, value, true);
	}
	
	template <class M>
	void apply_controlled_gate(M const& m, std::vector<unsigned> ids, std::vector<unsigned> ctrl){
		auto fused_gates = fused_gates_;
		fused_gates.insert(m, ids, ctrl);
		
		if (fused_gates.num_qubits() >= fusion_qubits_min_ && fused_gates.num_qubits() <= fusion_qubits_max_){
			fused_gates_ = fused_gates;
			run();
		}
		else if (fused_gates.num_qubits() > fusion_qubits_max_ || (fused_gates.num_qubits()-ids.size())>fused_gates_.num_qubits()){
			run();
			fused_gates_.insert(m, ids, ctrl);
		}
		else
			fused_gates_ = fused_gates;
		//run();
	}
	
	template <class F, class QuReg>
	void emulate_math(F const& f, QuReg quregs, std::vector<unsigned> ctrl, unsigned num_threads=1){
		run();
		auto ctrlmask = get_control_mask(ctrl);
		
		for (unsigned i = 0; i < quregs.size(); ++i)
			for (unsigned j = 0; j < quregs[i].size(); ++j)
				quregs[i][j] = map_[quregs[i][j]];

		StateVector newvec(vec_.size(), 0.);
		std::vector<int> res(quregs.size());
		
		#pragma omp parallel for schedule(static) firstprivate(res) num_threads(num_threads)
		for (std::size_t i = 0; i < vec_.size(); ++i){
			if ((ctrlmask&i) == ctrlmask){
				for (unsigned qr_i = 0; qr_i < quregs.size(); ++qr_i){
					res[qr_i] = 0;
					for (unsigned qb_i = 0; qb_i < quregs[qr_i].size(); ++qb_i)
						res[qr_i] |= ((i >> quregs[qr_i][qb_i])&1) << qb_i;
				}
				f(res);
				auto new_i = i;
				for (unsigned qr_i = 0; qr_i < quregs.size(); ++qr_i){
					for (unsigned qb_i = 0; qb_i < quregs[qr_i].size(); ++qb_i){
						if (!(((new_i >> quregs[qr_i][qb_i])&1) == ((res[qr_i] >> qb_i)&1)))
							new_i ^= (1UL << quregs[qr_i][qb_i]);
					}
				}
				newvec[new_i] += vec_[i];
			}
			else
				newvec[i] += vec_[i];
		}
		vec_ = std::move(newvec);
	}
	
	void run(){
		if (fused_gates_.size() < 1)
			return;
		
		Fusion::Matrix m;
		Fusion::IndexVector ids, ctrls;
		
		fused_gates_.perform_fusion(m, ids, ctrls);
		
		for (auto& id : ids)
			id = map_[id];
		
		auto ctrlmask = get_control_mask(ctrls);
			
		switch (ids.size()){
			case 1:
				#pragma omp parallel
				kernel(vec_, ids[0], m, ctrlmask);
				break;
			case 2:
				#pragma omp parallel
				kernel(vec_, ids[1], ids[0], m, ctrlmask);
				break;
			case 3:
				#pragma omp parallel
				kernel(vec_, ids[2], ids[1], ids[0], m, ctrlmask);
				break;
			case 4:
				#pragma omp parallel
				kernel(vec_, ids[3], ids[2], ids[1], ids[0], m, ctrlmask);
				break;
			case 5:
				#pragma omp parallel
				kernel(vec_, ids[4], ids[3], ids[2], ids[1], ids[0], m, ctrlmask);
				break;
		}
		
		fused_gates_ = Fusion();
	}
	std::tuple<Map, StateVector&> cheat(){
		run();
		return make_tuple(map_, std::ref(vec_));
	}
	~Simulator(){
	}
private:
	std::size_t get_control_mask(std::vector<unsigned> const& ctrls){
		std::size_t ctrlmask = 0;
		for (auto c : ctrls)
			ctrlmask |= (1UL << map_[c]);
		return ctrlmask;
	}
	
	unsigned N_; // #qubits
	StateVector vec_;
	Map map_;
	Fusion fused_gates_;
	unsigned fusion_qubits_min_, fusion_qubits_max_;
	RndEngine rnd_eng_;
	std::function<double()> rng_;
};

#endif
