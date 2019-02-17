#include <iostream>
#include <vector>
#include <array>
#include <complex>
#include <cassert>
#include <algorithm>
#include <tuple>
#include <random>
#include <chrono>
#include <functional>

using calc_type = double;
using complex_type = std::complex<calc_type>;
using gate_type = std::array<std::array<complex_type, 2>, 2>;

const double tol = 1e-12;
const complex_type I(0., 1.);


double get_time() {
    using Clock = std::chrono::high_resolution_clock;
    return std::chrono::duration<double>(Clock::now().time_since_epoch()).count();
}

gate_type operator*(const gate_type& l, const gate_type& r) {
    complex_type a = l[0][0] * r[0][0] + l[0][1] * r[1][0];
    complex_type b = l[0][0] * r[0][1] + l[0][1] * r[1][1];
    complex_type c = l[1][0] * r[0][0] + l[1][1] * r[1][0];
    complex_type d = l[1][0] * r[0][1] + l[1][1] * r[1][1];
    return {{a,b,c,d}};
}

gate_type operator*(complex_type c, const gate_type& g) {
    return { c*g[0][0], c*g[0][1],
             c*g[1][0], c*g[1][1] };
}

gate_type operator+(const gate_type& a, const gate_type& b) {
    return { a[0][0]+b[0][0], a[0][1]+b[0][1],
             a[1][0]+b[1][0], a[1][1]+b[1][1] };
}


gate_type dagger(const gate_type& g) {
    return { std::conj(g[0][0]), std::conj(g[1][0]),
             std::conj(g[0][1]), std::conj(g[1][1]) };
}

// matrix containing normalized eigen vectors assuming eigenvalues
// are (i, -i)
gate_type eigen_vectors(const gate_type& gate) {
    gate_type u;
    if(std::abs(gate[1][0]) > tol) {
        u[0][0] = I - gate[1][1];
        u[0][1] = -I - gate[1][1];
        u[1][0] = gate[1][0];
        u[1][1] = gate[1][0];
    } else if(std::abs(gate[0][1]) > tol) {
        u[0][0] = gate[0][1];
        u[0][1] = gate[0][1];
        u[1][0] = I - gate[0][0];
        u[1][1] = -I - gate[0][0];
    } else {
        if(std::abs(gate[0][0] - I) < tol) {
            u[0][0] = 1;
            u[1][0] = 0;

            u[0][1] = 0;
            u[1][1] = 1;
        } else if(std::abs(gate[0][0] + I) < tol) {
            u[0][0] = 0;
            u[1][0] = 1;

            u[0][1] = 1;
            u[1][1] = 0;
        } else {
            assert(false);
        }
        return u;
    }

    calc_type norm = std::sqrt(std::norm(u[0][0]) + std::norm(u[1][0]));
    u[0][0] /= norm;
    u[1][0] /= norm;
    norm = std::sqrt(std::norm(u[0][1]) + std::norm(u[1][1]));
    u[0][1] /= norm;
    u[1][1] /= norm;

    return u;
}

class MCG {
public:
    gate_type gate;
    using PartialDecomposition = std::vector<gate_type>;
    using Decomposition = std::tuple<PartialDecomposition,
                                     std::vector<complex_type>>;

    MCG() { gate = {1,0,0,1}; }
    MCG(const gate_type& gate) : gate(gate) { }

    MCG& operator=(const MCG& other) {
        gate = other.gate;
        return *this;
    }

    Decomposition get_decomposition() const {
        return std::make_tuple(std::vector<gate_type>(1,gate),
                               std::vector<complex_type>(0));
    }
};

class Diagonal {
public:
    using Decomposition = std::vector<std::vector<calc_type>>;

    unsigned n;

    Diagonal(std::vector<complex_type> &phases) : phases(phases) {
        unsigned N = phases.size();
        n = static_cast<unsigned>(std::log2(N));
        assert(1<<n == N);
    }

    Decomposition get_decomposition() {
        unsigned N = phases.size();
        angles = std::vector<calc_type>(N);
        for(unsigned i = 0; i < N; ++i)
            angles[i] = std::arg(phases[i]);

        Decomposition decomposition;
        for(unsigned i = 0; i < n; ++i) {
            unsigned length = 1<<(n-i);
            std::vector<calc_type> rotations(length/2);
            for(unsigned j = 0; j < length/2; ++j)
                std::tie(angles[j], rotations[j])
                    = basic_decomposition(angles[2*j], angles[2*j+1]);
            angles.resize(length/2);
            decompose_rotations(rotations);
            decomposition.push_back(rotations);
        }

        // last angle is global phase
        std::vector<calc_type> ph(1,angles[0]);
        decomposition.push_back(ph);
        return decomposition;
    }

    complex_type phase(unsigned index) const { return phases[index]; }

private:


    // global and relative phase
    std::tuple<calc_type, calc_type>
    basic_decomposition(calc_type phi1, calc_type phi2) const {
        return std::make_tuple((phi1+phi2)/2, phi2-phi1);
    }

    std::tuple<calc_type, calc_type>
    rotation_decomposition(calc_type phi1, calc_type phi2) const {
        return std::make_tuple((phi1+phi2)/2, (phi1-phi2)/2);
    }

    void decompose_rotations(std::vector<calc_type> &rotations) {
        decompose_rotations_rec(rotations.begin(), rotations.end());
    }

    template<typename Iter>
    void decompose_rotations_rec(Iter a, Iter b, bool reversed = false) {
        unsigned N = std::distance(a,b);
        if(N <= 1)
            return;
        if(reversed == false)
            for(Iter i = a; i != a+N/2; ++i)
                std::tie(*i, *(i+N/2)) =
                    rotation_decomposition(*i, *(i+N/2));
        else
            for(Iter i = a; i != a+N/2; ++i)
                std::tie(*(i+N/2), *i) =
                    rotation_decomposition(*i, *(i+N/2));

        decompose_rotations_rec(a, a+N/2, false);
        decompose_rotations_rec(a+N/2, b, true);
    }

    std::vector<complex_type> phases;
    std::vector<calc_type> angles;
};

class UCG {
public:
    unsigned n;

    using PartialDecomposition = std::vector<gate_type>;
    using Decomposition = std::tuple<PartialDecomposition,
                                     std::vector<complex_type>>;

    UCG(std::vector<gate_type> &gates) : gates_(gates) {
        n = 1 + static_cast<unsigned>(std::log2(gates.size()));
    }

    Decomposition get_decomposition() {
        if(decomposed_ == false)
            decompose();
        return std::make_tuple(gates_, phases_);
    }

    void decompose() {
        assert(decomposed_ == false);
        decomposed_ = true;
        ucg_decomposition();
    }

    gate_type operator()(unsigned i) const {
        if(i >= gates_.size())
            std::cout << "Illegal UCG Index" << std::endl;
        return gates_[i];
    }

    Diagonal get_diagonal() {
        assert(decomposed_ == true);
        return Diagonal(phases_);
    }

private:

    std::tuple<gate_type, gate_type, gate_type>
    ucg_basic_decomposition(const gate_type& a, const gate_type& b) {
        gate_type x = {
            a[0][0]*std::conj(b[0][0]) + a[0][1]*std::conj(b[0][1]),
            a[0][0]*std::conj(b[1][0]) + a[0][1]*std::conj(b[1][1]),
            a[1][0]*std::conj(b[0][0]) + a[1][1]*std::conj(b[0][1]),
            a[1][0]*std::conj(b[1][0]) + a[1][1]*std::conj(b[1][1])
        };
        complex_type det = x[0][0]*x[1][1] - x[1][0]*x[0][1];
        complex_type x11 = x[0][0]/std::sqrt(det);
        calc_type delta = M_PI / 2.0;
        calc_type phi = std::arg(det);
        calc_type psi = std::arg(x11);
        complex_type r1 = std::exp(I * ((delta - phi/2 - psi) / 2));
        complex_type r2 = std::exp(I * ((delta - phi/2 + psi + M_PI) / 2));
        gate_type r = {r1, 0.0, 0.0, r2};
        gate_type rxr = {
            r1*r1*x[0][0], r1*r2*x[0][1],
            r1*r2*x[1][0], r2*r2*x[1][1]
        };
        gate_type u = eigen_vectors(rxr);
        complex_type z = std::exp(I*calc_type(M_PI/4));
        gate_type v = {
            z*std::conj(r1*u[0][0]), z*std::conj(r2*u[1][0]),
            std::conj(z*r1*u[0][1]), std::conj(z*r2*u[1][1])
        };
        v = v*b;

        return std::make_tuple(v,u,r);
    }

    complex_type dot(const gate_type& a, const gate_type& b) {
        return std::conj(a[0][0]) * b[0][0]
             + std::conj(a[0][1]) * b[0][1]
             + std::conj(a[1][0]) * b[1][0]
             + std::conj(a[1][1]) * b[1][1];
    }

    void project_gate(gate_type& gate) {
        calc_type norm = std::sqrt(std::norm(gate[0][1]) + std::norm(gate[1][1]));
        gate[0][1] /= norm;
        gate[1][1] /= norm;

        complex_type inner = std::conj(gate[0][1])*gate[0][0] + std::conj(gate[1][1])*gate[1][0];
        gate[0][0] -= inner*gate[0][1];
        gate[1][0] -= inner*gate[1][1];

        norm = std::sqrt(std::norm(gate[0][0]) + std::norm(gate[1][0]));
        gate[0][0] /= norm;
        gate[1][0] /= norm;
    }

    void ucg_decomposition() {
        phases_ = std::vector<complex_type>(1<<n, 1);

        unsigned controls = n-1;
        if(controls == 0)
            return;

        for(unsigned level = 0; level < controls; ++level) {
            unsigned intervals = 1UL << level;
            unsigned interval_length = 1UL << (controls-level);

            for(unsigned interval = 0; interval < intervals; ++interval) {
                #pragma omp parallel for schedule(static) if(interval_length >= 4)
                for(unsigned i = 0; i < interval_length/2; ++i) {
                    unsigned offset = interval*interval_length;
                    auto& a = gates_[offset+i];
                    auto& b = gates_[offset+interval_length/2+i];
                    gate_type v,u,r;
                    std::tie(v,u,r) = ucg_basic_decomposition(a,b);

                    if(interval == intervals-1) {
                        for(unsigned m = 0; m < intervals; ++m) {
                            unsigned offset2 = m*interval_length;
                            unsigned index = 2*i + 2*offset2;
                            phases_[index] *= std::conj(r[0][0]);
                            phases_[index+1] *= std::conj(r[1][1]);
                            index = interval_length + 2*(i+offset2);
                            phases_[index] *= r[0][0];
                            phases_[index+1] *= r[1][1];
                        }
                    } else {
                        unsigned index = offset + interval_length + i;
                        gates_[index][0][0] *= std::conj(r[0][0]);
                        gates_[index][1][0] *= std::conj(r[0][0]);
                        gates_[index][0][1] *= std::conj(r[1][1]);
                        gates_[index][1][1] *= std::conj(r[1][1]);
                        index += interval_length/2;
                        gates_[index][0][0] *= r[0][0];
                        gates_[index][1][0] *= r[0][0];
                        gates_[index][0][1] *= r[1][1];
                        gates_[index][1][1] *= r[1][1];
                    }

                    gates_[offset + i] = v;
                    gates_[offset + i + interval_length/2] = u;

                    project_gate(gates_[offset + i]);
                    project_gate(gates_[offset + i + interval_length/2]);
                }
            }
        }

        complex_type I(0,1);
        calc_type x = 1.0/std::sqrt(2);
        gate_type H = {x,x,x,-x};
        complex_type z = std::exp(I*calc_type(M_PI/4));
        gate_type RH = {z*x, z*x, std::conj(z)*x, -std::conj(z)*x};

        gates_[0] = H * gates_[0];
        for(unsigned i = 1; i < (1<<controls)-1; ++i) {
            gates_[i] = H * gates_[i];
            gates_[i] = gates_[i] * RH;
        }
        unsigned last = (1<<controls)-1;
        gates_[last] = gates_[last] * RH;

        complex_type phi = std::exp(I*calc_type(M_PI/4));
        unsigned N = 1<<n;
        if(controls >= 1) {
            std::transform(phases_.begin(), phases_.begin() + N/2, phases_.begin(), [&](complex_type d){ return d * phi; });
            std::transform(phases_.begin() + N/2, phases_.end(), phases_.begin() + N/2, [&](complex_type d){ return d / phi; });
        } if(controls >= 2) {
            std::transform(phases_.begin(), phases_.begin() + N/4, phases_.begin(), [&](complex_type d){ return d * I; });
            std::transform(phases_.begin() + N/4, phases_.begin() + N/2, phases_.begin() + N/4, [&](complex_type d){ return d * -I; });
            std::transform(phases_.begin() + N/2, phases_.begin() + 3*N/4, phases_.begin() + N/2, [&](complex_type d){ return d * I; });
            std::transform(phases_.begin() + 3*N/4, phases_.end(), phases_.begin() + 3*N/4, [&](complex_type d){ return d * -I; });
        }

        complex_type phase = std::exp(-I*calc_type(((1<<controls)-1)*M_PI/4));
        if(controls >= 3)
            phase *= -1;
        for(auto& d : phases_)
            d *= phase;
    }

    std::vector<complex_type> phases_;
    std::vector<gate_type> gates_;
    bool decomposed_ = false;
};

class DecomposeIsometry {

public:
    using StateVector = std::vector<complex_type>;
    using Isometry = std::vector<StateVector>;

    using ReductionStep = std::tuple<MCG,UCG>;
    using Reduction = std::vector<ReductionStep>;

    using ReductionStepDecomposition = std::tuple<MCG::Decomposition, UCG::Decomposition>;
    using ReductionDecomposition = std::vector<ReductionStepDecomposition>;
    using CompleteReductionDecomposition = std::vector<ReductionDecomposition>;
    using Decomposition = std::tuple<CompleteReductionDecomposition, Diagonal::Decomposition>;

    Isometry V; // list of column vectors
    unsigned threshold, n;

    DecomposeIsometry(Isometry V, unsigned threshold) : V(V), threshold(threshold) {
        n = int(log2(V[0].size()));
    }

    Decomposition get_decomposition() {
        double time = get_time();
        CompleteReductionDecomposition complete_reduction_decomposition;
        for(unsigned k = 0; k < V.size(); ++k) {
            auto reduction_decomposition = reduce_column(k);
            complete_reduction_decomposition.push_back(reduction_decomposition);
        }

        std::vector<complex_type> phases(1<<n, 1);
        for(int k = 0; k < V.size(); ++k)
            phases[k] = 1.0 / V[k][0]; // normalize?
        auto diagonal = Diagonal(phases);
        auto diagonal_decomposition = diagonal.get_decomposition();

        return std::make_tuple(complete_reduction_decomposition, diagonal_decomposition);
    }

private:

    void debug() {
        std::cout << "--- Debug: ---" << std::endl;

        for(unsigned k = 0; k < V.size(); ++k) {
            for(unsigned i = 0; i < V[k].size(); ++i)
                std::cout << V[k][i] << ", ";
            std::cout << std::endl;
        }
        std::cout << std::endl << "--- /Debug: ---" << std::endl;
    }

    ReductionDecomposition reduce_column(unsigned k) {
        ReductionDecomposition reduction_decomposition;
        for(unsigned s = 0; s < n; ++s)
            reduction_decomposition.push_back(disentangle(k,s));
        return reduction_decomposition;
    }

    ReductionStepDecomposition disentangle(unsigned k, unsigned s) {
        auto mcg_decomposition = prepare_disentangle(k, s);

        for(unsigned l = 0; l < a(k,s); ++l)
            assert(std::abs(c(k, l)) < tol);

        unsigned l_max = 1 << (n-1-s);
        unsigned l_min = a(k,s+1);
        if(b(k,s+1) > 0)
            l_min += 1;

        unsigned target_bit = a(k,s) & 1;
        std::vector<gate_type> gates;
        gates.reserve(l_max);
        for(unsigned l = 0; l < l_min; ++l)
            gates.push_back(identity_gate());
        if(target_bit == 0)
            for(unsigned l = l_min; l < l_max; ++l)
                gates.push_back(to_zero_gate(k, l));
        else
            for(unsigned l = l_min; l < l_max; ++l)
                gates.push_back(to_one_gate(k, l));
        UCG ucg(gates);
        apply_UCG_up_to_diagonal_to_all(ucg, k, s);

        return std::make_tuple(mcg_decomposition,
                               ucg.get_decomposition());
    }

    unsigned _count_one_bits(unsigned mask) {
        unsigned cnt = 0;
        while(mask) {
            if(mask & 1)
                ++cnt;
            mask >>= 1;
        }
        return cnt;
    }

    MCG::Decomposition prepare_disentangle(unsigned k, unsigned s) {
        if(b(k,s+1) == 0 || ((k>>s)&1) != 0)
            return MCG(identity_gate()).get_decomposition();
        if(std::abs(c(k, 2*a(k,s+1)+1)) <= tol)
            return MCG(identity_gate()).get_decomposition();

        for(unsigned l = 0; l < a(k,s); ++l)
            assert(std::abs(c(k, l)) < tol);

        gate_type U(to_zero_gate(k, a(k,s+1)));

        unsigned mask = k; //& ~(1<<s)
        unsigned ctrl = _count_one_bits(mask);

        if(ctrl > 0 and ctrl < threshold) {
            auto gates = std::vector<gate_type>((1 << ctrl) - 1, identity_gate());
            gates.push_back(U);
            UCG ucg(gates);
            apply_MCG_to_all(U, k, s);
            apply_MCG_as_UCG_to_all(ucg.get_decomposition(), k, s);
            return ucg.get_decomposition();
        } else {
            apply_MCG_to_all(U, k, s);
            MCG mcg(U);
            return mcg.get_decomposition();
        }

        assert(false);
    }

    void apply_MCG_as_UCG_to_all(const MCG::Decomposition& mcg_decomposition, unsigned k, unsigned s) {
        for(unsigned col = 0; col < V.size(); ++col)
            apply_MCG_as_UCG(mcg_decomposition, k, s, col);
    }

    void apply_UCG_up_to_diagonal_to_all(UCG& ucg, unsigned k, unsigned s) {
        apply_UCG_to_all(ucg, k, s);
        ucg.decompose();
        apply_inv_diagonal_to_all(ucg.get_diagonal(), k, s);
    }

    void apply_MCG_to_all(const MCG& mcg, unsigned k, unsigned s) {
        for(unsigned col = 0; col < V.size(); ++col)
            apply_MCG(mcg, k, s, col);
    }

    void apply_UCG_to_all(const UCG& ucg, unsigned k, unsigned s) {
        for(unsigned col = 0; col < V.size(); ++col)
            apply_UCG(ucg, k, s, col);
    }

    void apply_inv_diagonal_to_all(const Diagonal& diagonal, unsigned k, unsigned s) {
        for(unsigned col = 0; col < V.size(); ++col)
            apply_inv_diagonal(diagonal, k, s, col);
    }

    std::vector<unsigned> _get_one_ids(unsigned k) {
        std::vector<unsigned> ids;
        for(unsigned i = 0; i < n; ++i)
            if((k>>i) & 1)
                ids.push_back(i);
        return ids;
    }

    void apply_MCG_as_UCG(const MCG::Decomposition& mcg_decomposition, unsigned k, unsigned s, unsigned col) {
        assert(((k>>s)&1) == 0);
        auto ids = _get_one_ids(k);
        ids.insert(ids.begin(), s);

        // apply inverse diagonal
        auto diagonal = std::get<1>(mcg_decomposition);
        if(col < k) {
            unsigned a = 0;
            for(unsigned i = 0; i < ids.size(); ++i)
                a |= ((col >> ids[i]) & 1) << i;
            c(col, 0) *= std::conj(diagonal[a]);
        } else if (col == k) {
            #pragma omp parallel for schedule(static)
            for(unsigned j = 0; j < (1<<(n-s)); ++j) {
                unsigned entry = (j << s) + b(k,s);
                unsigned a = 0;
                for(std::size_t i = 0; i < ids.size(); ++i)
                    a |= ((entry >> ids[i]) & 1) << i;
                c(col, j) *= std::conj(diagonal[a]);
            }
        } else {
            #pragma omp parallel for schedule(static)
            for(std::size_t entry = 0; entry < (1<<n); ++entry) {
                unsigned a = 0;
                for(std::size_t i = 0; i < ids.size(); ++i)
                    a |= ((entry >> ids[i]) & 1) << i;
                c(col, entry) *= std::conj(diagonal[a]);
            }
        }
    }

    void apply_MCG(const MCG& mcg, unsigned k, unsigned s, unsigned col) {
        if(col < k)
            return;

        unsigned hi = 2*a(k,s+1);
        unsigned lo = b(k,s);
        unsigned diff = 1 << s;
        unsigned mask = (hi<<s) | lo;

        if(k == col) {
            for(unsigned i = 0; i < (1<<(n-s)); i+=2) {
                if((i & hi) != hi)
                    continue;
                auto c0 = c(col, i);
                auto c1 = c(col, i+1);
                c(col, i)   = mcg.gate[0][0]*c0 + mcg.gate[0][1]*c1;
                c(col, i+1) = mcg.gate[1][0]*c0 + mcg.gate[1][1]*c1;
            }
        } else {
            for(unsigned i = 0; i < (1<<n); ++i) {
                if((i & mask) != mask || (i & (1<<s)) != 0)
                    continue;
                auto c0 = c(col, i);
                auto c1 = c(col, i+diff);
                c(col, i)      = mcg.gate[0][0]*c0 + mcg.gate[0][1]*c1;
                c(col, i+diff) = mcg.gate[1][0]*c0 + mcg.gate[1][1]*c1;
            }
        }
    }

    // O(2^n)
    void apply_UCG(const UCG& ucg, unsigned k, unsigned s, unsigned col) {
        if(col < k)
            return;
        if(col == k) {
            // TODO: ignore leading ids
            unsigned ctrl = n-1-s;
            unsigned target_bit = a(k,s) & 1;
            for(unsigned hi = 0; hi < (1<<ctrl); ++hi) {
                unsigned i0 = hi<<1;
                unsigned i1 = (hi<<1) + 1;
                if(target_bit == 0)
                    c(col, hi) = ucg(hi)[0][0]*c(col, i0) + ucg(hi)[0][1]*c(col, i1);
                else
                    c(col, hi) = ucg(hi)[1][0]*c(col, i0) + ucg(hi)[1][1]*c(col, i1);
            }
            V[k].resize(V[k].size()/2);
        } else {
            unsigned dist = 1<<s;
            #pragma omp parallel for collapse(2) schedule(static)
            for(unsigned hi = 0; hi < 1<<(n-1-s); ++hi)
                for(unsigned lo = 0; lo < dist; ++lo) {
                    unsigned i0 = (hi << (s+1)) | lo;
                    unsigned i1 = i0 + dist;
                    auto c0 = c(col, i0);
                    auto c1 = c(col, i1);
                    c(col, i0) = ucg(hi)[0][0]*c0 + ucg(hi)[0][1]*c1;
                    c(col, i1) = ucg(hi)[1][0]*c0 + ucg(hi)[1][1]*c1;
                }
        }
    }

    // O(2^n)
    void apply_inv_diagonal(const Diagonal& diagonal, unsigned k, unsigned s, unsigned col) {
        for(unsigned q = 0; q < 1<<(n-s); ++q)
            if(std::abs(std::abs(std::conj(diagonal.phase(q)))-1.0) > tol)
                std::cout << "bad phase: " << diagonal.phase(q) << std::endl;
        if(col < k) {
            c(col, 0) *= std::conj(diagonal.phase(col>>s));
        } else if(col == k) {
            unsigned target_bit = (k >> s) & 1;
            #pragma omp parallel for schedule(static)
            for(unsigned i = 0; i < 1<<(n-s-1); ++i)
                c(col, i) *= std::conj(diagonal.phase(2*i+target_bit));
        } else {
            #pragma omp parallel for collapse(2) schedule(static)
            for(unsigned hi = 0; hi < 1<<(n-s); ++hi)
                for(unsigned lo = 0; lo < 1<<s; ++lo)
                    c(col, (hi<<s) + lo) *= std::conj(diagonal.phase(hi));
        }
    }

    gate_type identity_gate() {
        return {1,0,0,1};
    }

    gate_type to_zero_gate(unsigned col, unsigned l) {
        auto c0 = c(col, 2*l);
        auto c1 = c(col, 2*l+1);
        auto r = std::sqrt(std::norm(c0) + std::norm(c1));
        if(r < tol)
            return identity_gate();
        c0 /= r;
        c1 /= r;
        return {
            std::conj(c0), std::conj(c1),
                      -c1,           c0
        };
    }

    gate_type to_one_gate(unsigned col, unsigned l) {
        auto c0 = c(col, 2*l);
        auto c1 = c(col, 2*l+1);
        auto r = std::sqrt(std::norm(c0) + std::norm(c1));
        if(r < tol)
            return identity_gate();
        c0 /= r;
        c1 /= r;
        return {
                     -c1,            c0 ,
            std::conj(c0), std::conj(c1)
        };
    }

    // k = (a(k,s)<<s) + b(k,s)
    unsigned a(unsigned k, unsigned s) {
        return k >> s;
    }

    // return s least significant bits
    unsigned b(unsigned k, unsigned s) {
        return k & ((1<<s)-1);
    }

    // coefficient l of vec where the s least significant bit are assumed
    // to be disentangled in the state k
    complex_type& c(unsigned col, unsigned l, unsigned k=0, unsigned s=0) {
        unsigned N = V[col].size();
        unsigned index = b(k,s) + l * (1<<s);
        if(!(0 <= index && index < N))
            std::cout << "Illegal Index C++" << std::endl;
        return V[col][index];
    }
};
