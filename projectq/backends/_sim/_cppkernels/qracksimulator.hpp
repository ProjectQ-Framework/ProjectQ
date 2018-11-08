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

#ifndef QRACK_SIMULATOR_HPP_
#define QRACK_SIMULATOR_HPP_

#include "qrack/qfactory.hpp"

#include <vector>
#include <complex>

#include "intrin/alignedallocator.hpp"
#include <map>
#include <cassert>
#include <algorithm>
#include <tuple>
#include <random>
#include <functional>

#if defined(_OPENMP)
#include <omp.h>
#endif

class QrackSimulator{
public:
    using calc_type = real1;
    using complex_type = complex;
    using StateVector = std::vector<complex_type, aligned_allocator<complex_type,64>>;
    using Map = std::map<unsigned, unsigned>;
    using RndEngine = std::default_random_engine;
    enum Qrack::QInterfaceEngine QrackEngine = Qrack::QINTERFACE_QUNIT;
    enum Qrack::QInterfaceEngine QrackSubengine = Qrack::QINTERFACE_OPENCL;
    typedef std::function<void(bitLenInt start, bitLenInt size, bitLenInt* ctrlArray, bitLenInt ctrlSize)> CINTFunc;
    typedef std::function<void(bitLenInt start, bitLenInt carryStart, bitLenInt size, bitLenInt* ctrlArray, bitLenInt ctrlSize)> CMULXFunc;

    QrackSimulator(unsigned seed = 1, const int& dev = -1) {
        rnd_eng_ = std::make_shared<std::default_random_engine>();
    	rnd_eng_->seed(seed);

        // Initialize OpenCL engine, and set the default device context.
        Qrack::OCLEngine::Instance()->SetDefaultDeviceContext(Qrack::OCLEngine::Instance()->GetDeviceContextPtr(dev));
        //if (dev == -1) {
        //    std::cout<<"Using default OpenCL device."<<std::endl;
        //} else {
        //    std::cout<<"Using OpenCL device #"<<dev<<"."<<std::endl;
        //}
    }

    void allocate_qubit(unsigned id){
        if (map_.count(id) == 0) {
            if (qReg == NULL) {
                map_[id] = 0;
                qReg = Qrack::CreateQuantumInterface(QrackEngine, QrackSubengine, 1, 0, rnd_eng_); 
            } else {
                map_[id] = qReg->GetQubitCount();
                qReg->Cohere(Qrack::CreateQuantumInterface(QrackSubengine, QrackSubengine, 1, 0, rnd_eng_));
            }
        }
        else
            throw(std::runtime_error(
                "AllocateQubit: ID already exists. Qubit IDs should be unique."));
    }

    bool get_classical_value(unsigned id, calc_type tol = min_norm){
        if (qReg->Prob(map_[id]) < 0.5) {
            return false;
        } else {
            return true;
        }
    }

    bool is_classical(unsigned id, calc_type tol = 1e-6){
        calc_type p = qReg->Prob(map_[id]);
        if ((p < tol) || ((ONE_R1 - p) < tol)) {
            // Difference in phase (for amplitudes not below the rounding tolerance)
            // prevents separability in the permutation basis.
            //
            // For example, 3 bits could be in the simulator. One bit could have a 100% chance being "true,"
            // split between 4 basis vectors including the other two bits, all at different phases.
            // Such a state for the 100% bit is still not necessarily separable, or "classical."
            //
            // Qrack::QUnit tries to track phase separability of bits:
            //
            // return qReg->IsPhaseSeparable((bitLenInt)map_[id]);
            //
            // However, the above method was intended for optimization purposes. It might err on the side of
            // guessing that a bit's phase relationships might not separable, when they actually can be.
            // It takes a maximal Schmidt decomposition to determine whether or not a bit is really separable.
            // This can be computationally expensive, so Qrack makes an inexpensive guess, erring on the side
            // of assuming too much irreducibility of any register state.
            //
            // As such, the above method might throw a false exception, but just checking probability can
            // fail to recognize real irreducibility:
            return true;
        } else {
            return false;
        }
    }

    void measure_qubits(std::vector<unsigned> const& ids, std::vector<bool> &res){
        bitLenInt i;
        bitLenInt* bits = new bitLenInt[ids.size()];
        for (i = 0; i < ids.size(); i++) {
            bits[i] = map_[ids[i]];
        }
        bitCapInt allRes = qReg->M(bits, ids.size());
        res.resize(ids.size());
        for (i = 0; i < ids.size(); i++) {
            res[i] = !(!(allRes & (1U << bits[i])));
        }
    }

    std::vector<bool> measure_qubits_return(std::vector<unsigned> const& ids){
        std::vector<bool> ret;
        measure_qubits(ids, ret);
        return ret;
    }

    void deallocate_qubit(unsigned id){
        if (map_.count(id) == 0)
            throw(std::runtime_error("Error: No qubit with given ID, to deallocate."));
        if (!is_classical(id))
            throw(std::runtime_error("Error: Qubit has not been measured / uncomputed! There is most likely a bug in your code."));

        if (qReg->GetQubitCount() == 1) {
            qReg = NULL;
        } else {
            qReg->Dispose(map_[id], 1U);
        }

        bitLenInt mapped = map_[id];
        map_.erase(id);

        Map::iterator it;
        for (it = map_.begin(); it != map_.end(); it++) {
            if (mapped < (it->second)) {
                it->second--;
            }
        }
    }

    template <class M>
    void apply_controlled_gate(M const& m, std::vector<unsigned> ids,
                               std::vector<unsigned> ctrl){
        complex mArray[4] = {
            complex(real(m[0][0]), imag(m[0][0])), complex(real(m[0][1]), imag(m[0][1])),
            complex(real(m[1][0]), imag(m[1][0])), complex(real(m[1][1]), imag(m[1][1]))
        };

        bitLenInt* ctrlArray = new bitLenInt[ctrl.size()];
        for (bitLenInt i = 0; i < ctrl.size(); i++) {
            ctrlArray[i] = map_[ctrl[i]];
        }

        for (bitLenInt i = 0; i < ids.size(); i++) {
            qReg->ApplyControlledSingleBit(ctrlArray, ctrl.size(), map_[ids[i]], mArray);
        }

        delete[] ctrlArray;
    }

    void apply_controlled_swap(std::vector<unsigned> ids1,
                               std::vector<unsigned> ids2,
                               std::vector<unsigned> ctrl){

        assert(ids1.size() == ids2.size());

        bitLenInt* ctrlArray = new bitLenInt[ctrl.size()];
        for (bitLenInt i = 0; i < ctrl.size(); i++) {
            ctrlArray[i] = map_[ctrl[i]];
        }

        for (bitLenInt i = 0; i < ids1.size(); i++) {
            qReg->CSwap(ctrlArray, ctrl.size(), map_[ids1[i]], map_[ids2[i]]);
        }

        delete[] ctrlArray;
    }

    void apply_controlled_sqrtswap(std::vector<unsigned> ids1,
                               std::vector<unsigned> ids2,
                               std::vector<unsigned> ctrl){

        assert(ids1.size() == ids2.size());

        bitLenInt* ctrlArray = new bitLenInt[ctrl.size()];
        for (bitLenInt i = 0; i < ctrl.size(); i++) {
            ctrlArray[i] = map_[ctrl[i]];
        }

        for (bitLenInt i = 0; i < ids1.size(); i++) {
            qReg->CSqrtSwap(ctrlArray, ctrl.size(), map_[ids1[i]], map_[ids2[i]]);
        }

        delete[] ctrlArray;
    }

    void apply_controlled_inc(std::vector<unsigned> ids, std::vector<unsigned> ctrl, bitCapInt toAdd){
        apply_controlled_int([&](bitLenInt start, bitLenInt size, bitLenInt* ctrlArray, bitLenInt ctrlSize) {
            qReg->CINC(toAdd, start, size, ctrlArray, ctrlSize);
        }, ids, ctrl);
    }

    void apply_controlled_dec(std::vector<unsigned> ids, std::vector<unsigned> ctrl, bitCapInt toSub){
        apply_controlled_int([&](bitLenInt start, bitLenInt size, bitLenInt* ctrlArray, bitLenInt ctrlSize) {
            qReg->CDEC(toSub, start, size, ctrlArray, ctrlSize);
        }, ids, ctrl);
    }

    void apply_controlled_mul(std::vector<unsigned> ids, std::vector<unsigned> ctrl, bitCapInt toMul){
        apply_controlled_mulx([&](bitLenInt start, bitLenInt carryStart, bitLenInt size, bitLenInt* ctrlArray, bitLenInt ctrlSize) {
            qReg->CMUL(toMul, start, carryStart, size, ctrlArray, ctrlSize);
        }, ids, ctrl);
    }

    void apply_controlled_div(std::vector<unsigned> ids, std::vector<unsigned> ctrl, bitCapInt toDiv){
        apply_controlled_mulx([&](bitLenInt start, bitLenInt carryStart, bitLenInt size, bitLenInt* ctrlArray, bitLenInt ctrlSize) {
            qReg->CDIV(toDiv, start, carryStart, size, ctrlArray, ctrlSize);
        }, ids, ctrl);
    }

    calc_type get_probability(std::vector<bool> const& bit_string,
                              std::vector<unsigned> const& ids){
        if (!check_ids(ids))
            throw(std::runtime_error("get_probability(): Unknown qubit id."));
        std::size_t mask = 0, bit_str = 0;
        for (unsigned i = 0; i < ids.size(); i++){
            mask |= 1UL << map_[ids[i]];
            bit_str |= bit_string[i]? (1UL << map_[ids[i]]) : 0UL;
        }
        return qReg->ProbMask(mask, bit_str);
    }

    complex_type get_amplitude(std::vector<bool> const& bit_string,
                                      std::vector<unsigned> const& ids){
        std::size_t chk = 0;
        std::size_t index = 0;
        for (unsigned i = 0; i < ids.size(); i++){
            if (map_.count(ids[i]) == 0)
                break;
            chk |= 1UL << map_[ids[i]];
            index |= bit_string[i]? (1UL << map_[ids[i]]) : 0UL;
        }
        if (chk + 1 != (qReg->GetMaxQPower()))
            throw(std::runtime_error("The second argument to get_amplitude() must be a permutation of all allocated qubits. Please make sure you have called eng.flush()."));
        return qReg->GetAmplitude(index);
    }

    void set_wavefunction(StateVector const& wavefunction, std::vector<unsigned> const& ordering){
        // make sure there are 2^n amplitudes for n qubits
        assert(wavefunction.size() == (1UL << ordering.size()));
        // check that all qubits have been allocated previously
        if (map_.size() != ordering.size() || !check_ids(ordering))
            throw(std::runtime_error("set_wavefunction(): Invalid mapping provided. Please make sure all qubits have been allocated previously."));

        // set mapping and wavefunction
        for (unsigned i = 0; i < ordering.size(); i++)
            map_[ordering[i]] = i;
        
        complex* wfArray = new complex[wavefunction.size()];
        #pragma omp parallel for schedule(static)
        for (std::size_t i = 0; i < wavefunction.size(); i++)
            wfArray[i] = complex(real(wavefunction[i]), imag(wavefunction[i]));

        qReg = Qrack::CreateQuantumInterface(QrackEngine, QrackSubengine, ordering.size(), 0, rnd_eng_);
        qReg->SetQuantumState(wfArray);

        delete[] wfArray;
    }

    void collapse_wavefunction(std::vector<unsigned> const& ids, std::vector<bool> const& values){
        assert(ids.size() == values.size());
        if (!check_ids(ids))
            throw(std::runtime_error("collapse_wavefunction(): Unknown qubit id(s) provided. Try calling eng.flush() before invoking this function."));
        bitCapInt mask = 0, val = 0;
        bitLenInt* idsArray = new bitLenInt[ids.size()];
        bool* valuesArray = new bool[values.size()];
        for (bitLenInt i = 0; i < ids.size(); i++){
            idsArray[i] = map_[ids[i]];
            mask |= (1UL << map_[ids[i]]);
            val |= ((values[i]?1UL:0UL) << map_[ids[i]]);
            valuesArray[i] = values[i];
        }
        calc_type N = qReg->ProbMask(mask, val);
        if (N < 1.e-12)
            throw(std::runtime_error("collapse_wavefunction(): Invalid collapse! Probability is ~0."));

        qReg->ForceM(idsArray, ids.size(), valuesArray);

        delete[] idsArray;
        delete[] valuesArray;
    }

    std::tuple<Map, StateVector> cheat(){
        if (qReg == NULL) {
            StateVector vec(1, 0.);
            return make_tuple(map_, std::move(vec));
        }

        complex* wfArray = new complex[qReg->GetMaxQPower()];
        qReg->GetQuantumState(wfArray);
        StateVector vec(qReg->GetMaxQPower());

        #pragma omp parallel for schedule(static)
        for (std::size_t i = 0; i < vec.size(); i++)
            vec[i] = complex_type(real(wfArray[i]), imag(wfArray[i]));

        delete[] wfArray;

        return make_tuple(map_, std::move(vec));
    }

    ~QrackSimulator(){
    }

private:
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

    void apply_controlled_int(CINTFunc fn, std::vector<unsigned> ids, std::vector<unsigned> ctrl){
        bitLenInt i;
        Map invMap;
        for (Map::iterator it = map_.begin(); it != map_.end(); it++) {
            invMap[it->second] = it->first;
        }

        bitLenInt tempMap;
        for (i = 0; i < ids.size(); i++) {
            qReg->Swap(i, map_[ids[i]]);

            tempMap = map_[ids[i]];
            std::swap(map_[ids[i]], map_[invMap[i]]);
            std::swap(invMap[i], invMap[tempMap]);
        }

        bitLenInt* ctrlArray = new bitLenInt[ctrl.size()];
        for (i = 0; i < ctrl.size(); i++) {
            ctrlArray[i] = map_[ctrl[i]];
        }

        fn(0, (bitLenInt)ids.size(), ctrlArray, (bitLenInt)ctrl.size());

        delete[] ctrlArray;
    }

    void apply_controlled_mulx(CMULXFunc fn, std::vector<unsigned> ids, std::vector<unsigned> ctrl){
        assert((ids.size() % 2) == 0);

        bitLenInt i;
        Map invMap;
        for (Map::iterator it = map_.begin(); it != map_.end(); it++) {
            invMap[it->second] = it->first;
        }

        bitLenInt tempMap;
        for (i = 0; i < ids.size(); i++) {
            qReg->Swap(i, map_[ids[i]]);

            tempMap = map_[ids[i]];
            std::swap(map_[ids[i]], map_[invMap[i]]);
            std::swap(invMap[i], invMap[tempMap]);
        }

        bitLenInt* ctrlArray = new bitLenInt[ctrl.size()];
        for (i = 0; i < ctrl.size(); i++) {
            ctrlArray[i] = map_[ctrl[i]];
        }

        fn(0, (bitLenInt)(ids.size() / 2), (bitLenInt)(ids.size() / 2), ctrlArray, (bitLenInt)ctrl.size());

        delete[] ctrlArray;
    }

    Map map_;
    std::shared_ptr<RndEngine> rnd_eng_;
    Qrack::QInterfacePtr qReg;
};

#endif
