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
    using Term = std::vector<std::pair<unsigned, char>>;
    using TermsDict = std::vector<std::pair<Term, calc_type>>;
    using ComplexTermsDict = std::vector<std::pair<Term, complex_type>>;

    Simulator(unsigned seed = 1) : N_(0), vec_(1,0.), fusion_qubits_min_(4),
                                   fusion_qubits_max_(5), rnd_eng_(seed) {
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
            throw(std::runtime_error(
                "AllocateQubit: ID already exists. Qubit IDs should be unique."));
    }

    bool get_classical_value(unsigned id, calc_type tol = 1.e-12){
        run();
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
                    vec_[i+j+static_cast<std::size_t>(!value)*delta] = 0.;
            }
        }
        else{
            StateVector newvec((1UL << (N_-1)));
            #pragma omp parallel for schedule(static)
            for (std::size_t i = 0; i < vec_.size(); i += 2*delta)
                std::copy_n(&vec_[i + static_cast<std::size_t>(value)*delta],
                            delta, &newvec[i/2]);
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
        std::size_t pick = 0;
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
    void apply_controlled_gate(M const& m, std::vector<unsigned> ids,
                               std::vector<unsigned> ctrl){
        auto fused_gates = fused_gates_;
        fused_gates.insert(m, ids, ctrl);

        if (fused_gates.num_qubits() >= fusion_qubits_min_
                && fused_gates.num_qubits() <= fusion_qubits_max_){
            fused_gates_ = fused_gates;
            run();
        }
        else if (fused_gates.num_qubits() > fusion_qubits_max_
                 || (fused_gates.num_qubits() - ids.size()) > fused_gates_.num_qubits()){
            run();
            fused_gates_.insert(m, ids, ctrl);
        }
        else
            fused_gates_ = fused_gates;
    }

    template <class F, class QuReg>
    void emulate_math(F const& f, QuReg quregs, std::vector<unsigned> ctrl,
                      unsigned num_threads=1){
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

    calc_type get_expectation_value(TermsDict const& td, std::vector<unsigned> const& ids){
        run();
        calc_type expectation = 0.;
        auto current_state = vec_;
        for (auto const& term : td){
            auto const& coefficient = term.second;
            apply_term(term.first, ids, {});
            calc_type delta = 0.;
            #pragma omp parallel for reduction(+:delta) schedule(static)
            for (std::size_t i = 0; i < vec_.size(); ++i){
                auto const a1 = std::real(current_state[i]);
                auto const b1 = -std::imag(current_state[i]);
                auto const a2 = std::real(vec_[i]);
                auto const b2 = std::imag(vec_[i]);
                delta += a1 * a2 - b1 * b2;
            }
            expectation += coefficient * delta;
            vec_ = current_state;
        }
        return expectation;
    }

    void apply_qubit_operator(ComplexTermsDict const& td, std::vector<unsigned> const& ids){
        run();
        auto new_state = StateVector(vec_.size(), 0.);
        auto current_state = vec_;
        for (auto const& term : td){
            auto const& coefficient = term.second;
            apply_term(term.first, ids, {});
            #pragma omp parallel for schedule(static)
            for (std::size_t i = 0; i < vec_.size(); ++i){
                new_state[i] += coefficient * vec_[i];
                vec_[i] = current_state[i];
            }
        }
        vec_ = std::move(new_state);
    }

    calc_type get_probability(std::vector<bool> const& bit_string,
                              std::vector<unsigned> const& ids){
        run();
        if (!check_ids(ids))
            throw(std::runtime_error("get_probability(): Unknown qubit id. Please make sure you have called eng.flush()."));
        std::size_t mask = 0, bit_str = 0;
        for (unsigned i = 0; i < ids.size(); ++i){
            mask |= 1UL << map_[ids[i]];
            bit_str |= (bit_string[i]?1UL:0UL) << map_[ids[i]];
        }
        calc_type probability = 0.;
        #pragma omp parallel for reduction(+:probability) schedule(static)
        for (std::size_t i = 0; i < vec_.size(); ++i)
            if ((i & mask) == bit_str)
                probability += std::norm(vec_[i]);
        return probability;
    }

    complex_type const& get_amplitude(std::vector<bool> const& bit_string,
                                      std::vector<unsigned> const& ids){
        run();
        std::size_t chk = 0;
        std::size_t index = 0;
        for (unsigned i = 0; i < ids.size(); ++i){
            if (map_.count(ids[i]) == 0)
                break;
            chk |= 1UL << map_[ids[i]];
            index |= (bit_string[i]?1UL:0UL) << map_[ids[i]];
        }
        if (chk + 1 != vec_.size())
            throw(std::runtime_error("The second argument to get_amplitude() must be a permutation of all allocated qubits. Please make sure you have called eng.flush()."));
        return vec_[index];
    }

    void emulate_time_evolution(TermsDict const& tdict, calc_type const& time,
                                std::vector<unsigned> const& ids,
                                std::vector<unsigned> const& ctrl){
        run();
        complex_type I(0., 1.);
        calc_type tr = 0., op_nrm = 0.;
        TermsDict td;
        for (unsigned i = 0; i < tdict.size(); ++i){
            if (tdict[i].first.size() == 0)
                tr += tdict[i].second;
            else{
                td.push_back(tdict[i]);
                op_nrm += std::abs(tdict[i].second);
            }
        }
        unsigned s = std::abs(time) * op_nrm + 1.;
        complex_type correction = std::exp(-time * I * tr / (double)s);
        auto output_state = vec_;
        for (unsigned i = 0; i < s; ++i){
            calc_type nrm_change = 1.;
            for (unsigned k = 0; nrm_change > 1.e-12; ++k){
                auto coeff = (-time * I) / double(s * (k + 1));
                auto current_state = vec_;
                auto update = StateVector(vec_.size(), 0.);
                for (auto const& tup : td){
                    apply_term(tup.first, ids, ctrl);
                    #pragma omp parallel for schedule(static)
                    for (std::size_t j = 0; j < vec_.size(); ++j){
                        update[j] += vec_[j] * tup.second;
                        vec_[j] = current_state[j];
                    }
                }
                nrm_change = 0.;
                #pragma omp parallel for reduction(+:nrm_change) schedule(static)
                for (std::size_t j = 0; j < vec_.size(); ++j){
                    update[j] *= coeff;
                    vec_[j] = update[j];
                    output_state[j] += update[j];
                    nrm_change += std::norm(update[j]);
                }
                nrm_change = std::sqrt(nrm_change);
            }
            #pragma omp parallel for schedule(static)
            for (std::size_t j = 0; j < vec_.size(); ++j){
                output_state[j] *= correction;
                vec_[j] = output_state[j];
            }
        }
    }

    void set_wavefunction(StateVector const& wavefunction, std::vector<unsigned> const& ordering){
        run();
        // make sure there are 2^n amplitudes for n qubits
        assert(wavefunction.size() == (1UL << ordering.size()));
        // check that all qubits have been allocated previously
        if (map_.size() != ordering.size() || !check_ids(ordering))
            throw(std::runtime_error("set_wavefunction(): Invalid mapping provided. Please make sure all qubits have been allocated previously (call eng.flush())."));

        // set mapping and wavefunction
        for (unsigned i = 0; i < ordering.size(); ++i)
            map_[ordering[i]] = i;
        #pragma omp parallel for schedule(static)
        for (std::size_t i = 0; i < wavefunction.size(); ++i)
            vec_[i] = wavefunction[i];
    }

    void collapse_wavefunction(std::vector<unsigned> const& ids, std::vector<bool> const& values){
        run();
        assert(ids.size() == values.size());
        if (!check_ids(ids))
            throw(std::runtime_error("collapse_wavefunction(): Unknown qubit id(s) provided. Try calling eng.flush() before invoking this function."));
        std::size_t mask = 0, val = 0;
        for (unsigned i = 0; i < ids.size(); ++i){
            mask |= (1UL << map_[ids[i]]);
            val |= ((values[i]?1UL:0UL) << map_[ids[i]]);
        }
        // set bad entries to 0 and compute probability of outcome to renormalize
        calc_type N = 0.;
        #pragma omp parallel for reduction(+:N) schedule(static)
        for (std::size_t i = 0; i < vec_.size(); ++i){
            if ((i & mask) == val)
                N += std::norm(vec_[i]);
        }
        if (N < 1.e-12)
            throw(std::runtime_error("collapse_wavefunction(): Invalid collapse! Probability is ~0."));
        // re-normalize (if possible)
        N = 1./std::sqrt(N);
        #pragma omp parallel for schedule(static)
        for (std::size_t i = 0; i < vec_.size(); ++i){
            if ((i & mask) != val)
                vec_[i] = 0.;
            else
                vec_[i] *= N;
        }
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
    void apply_term(Term const& term, std::vector<unsigned> const& ids,
                    std::vector<unsigned> const& ctrl){
        complex_type I(0., 1.);
        Fusion::Matrix X = {{0., 1.}, {1., 0.}};
        Fusion::Matrix Y = {{0., -I}, {I, 0.}};
        Fusion::Matrix Z = {{1., 0.}, {0., -1.}};
        std::vector<Fusion::Matrix> gates = {X, Y, Z};
        for (auto const& local_op : term){
            unsigned id = ids[local_op.first];
            apply_controlled_gate(gates[local_op.second - 'X'], {id}, ctrl);
        }
        run();
    }
    std::size_t get_control_mask(std::vector<unsigned> const& ctrls){
        std::size_t ctrlmask = 0;
        for (auto c : ctrls)
            ctrlmask |= (1UL << map_[c]);
        return ctrlmask;
    }

    bool check_ids(std::vector<unsigned> const& ids){
        for (auto id : ids)
            if (!map_.count(id))
                return false;
        return true;
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
