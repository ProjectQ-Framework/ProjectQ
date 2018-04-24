#include <iostream>
#include <vector>
#include <array>
#include <complex>
#include <omp.h>
#include <cassert>
#include <algorithm>
#include <tuple>
#include <random>
#include <functional>

using calc_type = double;
using complex_type = std::complex<calc_type>;


const double tol = 1e-12;
const complex_type I(0., 1.);

class Gate {
public:
    using gate_type = std::array<std::array<complex_type, 2>, 2>;

    Gate() {};

    Gate(complex_type a, complex_type b, complex_type c, complex_type d) {
        gate_[0][0] = a;
        gate_[0][1] = b;
        gate_[1][0] = c;
        gate_[1][1] = d;
    }

    Gate& operator=(const Gate& o) {
        gate_[0][0] = o.gate_[0][0];
        gate_[0][1] = o.gate_[0][1];
        gate_[1][0] = o.gate_[1][0];
        gate_[1][1] = o.gate_[1][1];
        return *this;
    }

    void mul(const Gate& o) {
        complex_type a = gate_[0][0] * o.gate_[0][0] + gate_[0][1] * o.gate_[1][0];
        complex_type b = gate_[0][0] * o.gate_[0][1] + gate_[0][1] * o.gate_[1][1];
        complex_type c = gate_[1][0] * o.gate_[0][0] + gate_[1][1] * o.gate_[1][0];
        complex_type d = gate_[1][0] * o.gate_[0][1] + gate_[1][1] * o.gate_[1][1];
        gate_[0][0] = a;
        gate_[0][1] = b;
        gate_[1][0] = c;
        gate_[1][1] = d;
    }

    void mul_left(const Gate& o) {
        complex_type a = o.gate_[0][0] * gate_[0][0] + o.gate_[0][1] * gate_[1][0];
        complex_type b = o.gate_[0][0] * gate_[0][1] + o.gate_[0][1] * gate_[1][1];
        complex_type c = o.gate_[1][0] * gate_[0][0] + o.gate_[1][1] * gate_[1][0];
        complex_type d = o.gate_[1][0] * gate_[0][1] + o.gate_[1][1] * gate_[1][1];
        gate_[0][0] = a;
        gate_[0][1] = b;
        gate_[1][0] = c;
        gate_[1][1] = d;
    }

    // matrix containing normalized eigen vectors assuming eigenvalues
    // are (i, -i)
    Gate eigen_vectors() const {
        Gate u;
        if(std::abs(gate_[1][0]) > tol) {
            u.gate_[0][0] = I - gate_[1][1];
            u.gate_[0][1] = -I - gate_[1][1];
            u.gate_[1][0] = gate_[1][0];
            u.gate_[1][1] = gate_[1][0];
        } else if(std::abs(gate_[0][1]) > tol) {
            u.gate_[0][0] = gate_[0][1];
            u.gate_[0][1] = gate_[0][1];
            u.gate_[1][0] = I - gate_[0][0];
            u.gate_[1][1] = -I - gate_[0][0];
        } else {
            if(std::abs(gate_[0][0] - I) < tol) {
                u.gate_[0][0] = 1;
                u.gate_[1][0] = 0;

                u.gate_[0][1] = 0;
                u.gate_[1][1] = 1;
            } else if(std::abs(gate_[0][0] + I) < tol) {
                u.gate_[0][0] = 0;
                u.gate_[1][0] = 1;

                u.gate_[0][1] = 1;
                u.gate_[1][1] = 0;
            } else {
                assert(false);
            }
        }
        u.normalize();
        return u;
    }

    complex_type operator()(unsigned i, unsigned j) const {
        assert(i == 0 || i == 1);
        assert(j == 0 || j == 1);
        return gate_[i][j];
    }

private:
    void normalize() {
        calc_type norm = std::sqrt(std::norm(gate_[0][0]) + std::norm(gate_[1][0]));
        gate_[0][0] /= norm;
        gate_[1][0] /= norm;
        norm = std::sqrt(std::norm(gate_[0][1]) + std::norm(gate_[1][1]));
        gate_[0][1] /= norm;
        gate_[1][1] /= norm;
    }

    gate_type gate_;
};

class MCG {
public:
    unsigned k, s;
    Gate gate;
    bool trivial;

    using Decomposition = Gate;

    MCG(unsigned k, unsigned s) : k(k), s(s), trivial(true) { }

    MCG(const Gate &gate, unsigned k, unsigned s)
        : k(k), s(s), gate(gate), trivial(false) { }

    MCG& operator=(const MCG& other) {
        gate = other.gate;
        trivial = false;
        return *this;
    }

    Decomposition get_decomposition() const {
        return gate;
    }
};

class Diagonal {
public:
    using Decomposition = std::vector<std::vector<calc_type>>;

    unsigned n, k, s;

    Diagonal(std::vector<complex_type> &phases, unsigned n, unsigned k, unsigned s)
        : n(n), k(k), s(s), phases(phases) {
        unsigned target_qubits = n-s;
        assert(1<<target_qubits == phases.size());
        angles = std::vector<calc_type>(1<<target_qubits);
        for(unsigned i = 0; i < (1<<target_qubits); ++i)
            angles[i] = std::arg(phases[i]);
    }

    Decomposition get_decomposition() {
        Decomposition decomposition;
        for(unsigned i = 0; i < n-s; ++i) {
            unsigned length = 1<<(n-s-i);
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
    unsigned n,k,s;

    using Decomposition = std::vector<Gate>;

    UCG(std::vector<Gate> &gates, unsigned n, unsigned k, unsigned s)
        : gates_(gates) {
        unsigned qubits = n-s;
        diagonal_ = std::vector<complex_type>(1<<qubits, 1);
    }

    Decomposition get_decomposition() const {
        assert(decomposed_);
        return gates_;
    }

    void decompose() {
        assert(decomposed_ == false);
        decomposed_ = true;
        ucg_decomposition();
    }

    Gate& operator()(unsigned i) {
        return gates_[i];
    }

    Diagonal get_diagonal() {
        assert(decomposed_ == true);
        return Diagonal(diagonal_, n,k,s);
    }

private:

    std::tuple<Gate,Gate,Gate> ucg_basic_decomposition(Gate a, Gate b) {
        Gate x( // check
            a(0,0)*std::conj(b(0,0)) + a(0,1)*std::conj(b(0,1)),
            a(0,0)*std::conj(b(1,0)) + a(0,1)*std::conj(b(1,1)),
            a(1,0)*std::conj(b(0,0)) + a(1,1)*std::conj(b(0,1)),
            a(1,0)*std::conj(b(1,0)) + a(1,1)*std::conj(b(1,1))
        );
        complex_type det = x(0,0)*x(1,1) - x(1,0)*x(0,1);
        complex_type x11 = x(0,0)/std::sqrt(det);
        calc_type delta = M_PI / 2.0;
        calc_type phi = std::arg(det);
        calc_type psi = std::arg(x11);
        complex_type r1 = std::exp(I * ((delta - phi/2 - psi) / 2));
        complex_type r2 = std::exp(I * ((delta - phi/2 + psi + M_PI) / 2));
        Gate r(r1, 0.0, 0.0, r2);
        Gate rxr(
            r1*r1*x(0,0), r1*r2*x(0,1),
            r1*r2*x(1,0), r2*r2*x(1,1)
        );
        Gate u(rxr.eigen_vectors());
        complex_type z = std::exp(I*calc_type(M_PI/4));
        complex_type z_c = std::conj(z);
        static Gate d(z, 0.0, 0.0, z_c);
        Gate v(
            z*std::conj(r1*u(0,0)), z*std::conj(r2*u(1,0)),
            std::conj(z*r1*u(0,1)), std::conj(z*r2*u(1,1))
        );
        v.mul(b);
        return std::make_tuple(v,u,r);
    }

    void ucg_decomposition() {
        unsigned controls = n-s-1;

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
                    Gate v,u,r;
                    std::tie(v,u,r) = ucg_basic_decomposition(a,b);

                    if(interval == intervals-1) {
                        for(unsigned m = 0; m < intervals; ++m) {
                            unsigned offset2 = m*interval_length;
                            unsigned index = 2*i + 2*offset2;
                            diagonal_[index] *= std::conj(r(0,0));
                            diagonal_[index+1] *= std::conj(r(1,1));
                            index = interval_length + 2*(i+offset2);
                            diagonal_[index] *= r(0,0);
                            diagonal_[index+1] *= r(1,1);
                        }
                    } else {
                        unsigned index = offset + interval_length + i;
                        gates_[index](0,0) *= std::conj(r(0,0));
                        gates_[index](1,0) *= std::conj(r(0,0));
                        gates_[index](0,1) *= std::conj(r(1,1));
                        gates_[index](1,1) *= std::conj(r(1,1));
                        index += interval_length/2;
                        gates_[index](0,0) *= r(0,0);
                        gates_[index](1,0) *= r(0,0);
                        gates_[index](0,1) *= r(1,1);
                        gates_[index](1,1) *= r(1,1);
                    }

                    gates_[offset + i] = v;
                    gates_[offset + i + interval_length/2] = u;
                }
            }
        }

        complex_type I(0,1);
        calc_type x = 1/std::sqrt(2);
        Gate H(x,x,x,-x);
        complex_type z = std::exp(-I*calc_type(M_PI/4));
        Gate R(z,0,0,std::conj(z));
        Gate RH(z*x, z*x, std::conj(z)*x, -std::conj(z)*x);

        gates_[0].mul_left(H);
        for(unsigned i = 0; i < (1<<k)-1; ++i) {
            gates_[i].mul_left(H);
            gates_[i].mul(RH);
        }
        gates_[(1<<k)-1].mul(RH);

        complex_type phase = std::exp(-I*calc_type(((1<<k)-1)*M_PI/4));
        for(auto& d : diagonal_)
            d *= phase;
    }

    std::vector<complex_type> diagonal_;
    std::vector<Gate> gates_;
    bool decomposed_ = false;
};

/*
 Each colum of the isometry is stored in an object of class <Column>
 and all operations are applied to all columns.
 When reducing column k all previous columns are basis vectors and can
 be represented by a complex phase. The phase changes only from
 application of the diagonal gate. The current column is halved in size
 in each step, so we don't compute/store the zero entries.
 */
class Column {
public:
    using StateVector = std::vector<complex_type>;
    using Reduction = std::vector<std::tuple<MCG,UCG>>;

    Column(StateVector& data, unsigned index)
    : vec_(data), k(index) {
        n = static_cast<unsigned>(std::log2(data.size()));
        assert(n >= 1);
        assert(0 <= index && index < (1<<n));
    }

    Reduction reduce() {
        Reduction reduction;
        for(unsigned s = 0; s < n; ++s)
            reduction.push_back(disentangle(s));
        return reduction;
    }

    complex_type get_phase() {
        return vec_[0];
    }

    // O(1)
    void apply_MCG(MCG mcg) {
        if(k < mcg.k)
            return;

        if(k == mcg.k) {
            unsigned s = mcg.s;
            auto c0 = c(2*a(k,s+1));
            auto c1 = c(2*a(k,s+1)+1);
            // norm returns the magnitude squared
            c(2*a(k,s+1)) = std::norm(c0) + std::norm(c1);
            c(2*a(k,s+1)+1) = 0;
        } else {
            unsigned s = mcg.s;
            auto c0 = c(2*a(k,s+1), s);
            auto c1 = c(2*a(k,s+1)+1, s);
            c(2*a(k,s+1), s) = std::norm(c0) + std::norm(c1);
            c(2*a(k,s+1)+1, s) = 0;
        }
    }

    // O(2^n)
    void apply_UCG(UCG ucg) {
        if(k < ucg.k)
            return;

        if(k == ucg.k) { // only store non disentangled qubits
            // TODO: ignore leading ids
            unsigned s = ucg.s;
            for(unsigned hi = a(k,s+1); hi < 1<<(n-1); ++hi) {
                unsigned i0 = hi<<1;
                unsigned i1 = (hi<<1) + 1;
                c(i1>>1) = ucg(hi)(0,0)*c(i0) + ucg(hi)(0,1)*c(i1);
            }
            vec_.resize(n/=2);
        } else {
            unsigned s = ucg.s;
            unsigned dist = 1<<s;
            #pragma omp parallel for collapse(2) schedule(static)
            for(unsigned hi = 0; hi < 1<<(n-1-s); ++hi)
                for(unsigned lo = 0; lo < dist; ++lo) {
                    unsigned i0 = (hi << s) + lo;
                    unsigned i1 = i0 + dist;
                    auto c0 = c(i0);
                    auto c1 = c(i1);
                    c(i0) = ucg(hi)(0,0)*c0 + ucg(hi)(0,1)*c1;
                    c(i0) = ucg(hi)(1,0)*c0 + ucg(hi)(1,1)*c1;
                }
        }
    }

    // O(2^n)
    void apply_diagonal(const Diagonal& diagonal) {
        complex_type I(0.0, 1.0);
        if(k < diagonal.k) {
            c(0) *= diagonal.phase(k);
        } else if(k == diagonal.k) {
            unsigned s = diagonal.s;
            #pragma omp parallel for schedule(static)
            for(unsigned i = 0; i < 1<<(n-s); ++i)
                c(i) *= diagonal.phase(i);
        } else {
            unsigned s = diagonal.s;
            #pragma omp parallel for collapse(2) schedule(static)
            for(unsigned hi = 0; hi < 1<<(n-s); ++hi) {
                for(unsigned lo = 0; lo < 1<<s; ++lo) {
                    c((hi<<s) + lo) *= diagonal.phase(hi);
                }
            }
        }
    }

private:

    std::tuple<MCG,UCG>
    disentangle(unsigned s) {
        MCG mcg(k,s);
        if(b(k,s+1) != 0 && ((k>>s)&1) == 0)
            if(std::abs(c(2*a(k,s+1)+1, s)) > tol)
                mcg = MCG(prepare_disentangle(s), k, s);

        unsigned l_max = std::pow(2,n-s-1);
        unsigned l_min = a(k,s+1) + (b(k,s+1) > 0);

        std::vector<Gate> ucg;
        ucg.reserve(l_max);
        for(unsigned l = 0; l < l_min; ++l)
            ucg.push_back(identity_gate());
        for(unsigned l = l_min; l < l_max; ++l)
            ucg.push_back(to_zero_gate(l,s));

        return std::make_tuple(mcg, UCG(ucg, n, k, s));
    }

    Gate prepare_disentangle(unsigned s) {
        assert(((k >> s) & 1) == 0);
        assert(b(k,s+1) != 0);
        return to_zero_gate(2*a(k,s+1), s);
    }

    Gate identity_gate() {
        return Gate(1,0,
                    0,1);
    }

    Gate to_zero_gate(unsigned l, unsigned s) {
        auto c0 = c(2*l, s);
        auto c1 = c(2*l+1, s);
        return Gate(
            std::conj(c0), std::conj(c1),
                      -c1,           c0
        );
    }

    Gate to_one_gate(unsigned l, unsigned s) {
        auto c0 = c(2*l, s);
        auto c1 = c(2*l+1, s);
        return Gate(
                     -c1,            c0,
            std::conj(c0), std::conj(c1)
        );
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
    complex_type& c(unsigned l, unsigned s=0) {
        unsigned N = vec_.size();
        unsigned index = b(k,s) + l * (1<<s);
        assert(0 <= index && index < N);
        return vec_[index];
    }

    StateVector& vec_;
    Reduction reduction_;
    unsigned n;
    unsigned k;
};

class Decomposer {
public:
    using Isometry = std::vector<std::vector<complex_type>>;
    using Reduction = std::vector<std::tuple<MCG::Decomposition, UCG::Decomposition>>;
    using CompleteReduction = std::vector<Reduction>;
    using Decomposition = std::tuple<CompleteReduction, Diagonal::Decomposition>;

    Decomposer(Isometry &V) {
        n = int(log2(V[0].size()));
        for(unsigned k = 0; k < V.size(); ++k)
            columns_.push_back(Column(V[k], k));
        // assert
    }

    Decomposition run() {
        CompleteReduction complete_reduction;
        for(auto &col : columns_) {
            Column::Reduction reduction = col.reduce();
            apply_reduction(reduction);
            complete_reduction.push_back(decompose_reduction(reduction));
        }

        unsigned n_cols = columns_.size();
        std::vector<complex_type> phases(1<<n, 1);
        for(int k = 0; k < n_cols; ++k)
            phases[k] = columns_[k].get_phase();

        auto diagonal = Diagonal(phases, n, n, 0);
        auto diagonal_decomposition = diagonal.get_decomposition();
        return std::make_tuple(complete_reduction, diagonal_decomposition);
    }

    // can use MPI if we have lots of colums
    void apply_reduction(Column::Reduction &reduction) {
        for(auto& col : columns_) {
            for(auto& op : reduction) {
                col.apply_MCG(std::get<0>(op));
                col.apply_UCG(std::get<1>(op));
            }
        }

        for(auto& op : reduction)
            std::get<1>(op).decompose();

        for(auto& col : columns_)
            for(auto& op : reduction)
                col.apply_diagonal(std::get<1>(op).get_diagonal());
    }

private:
    // UCGs already decomposed
    Reduction decompose_reduction(Column::Reduction reduction) {
        Reduction decomposition;
        decomposition.reserve(reduction.size());
        for(const auto& op : reduction) {
            auto& mcg = std::get<0>(op);
            auto& ucg = std::get<1>(op);
            decomposition.push_back(std::make_tuple(
                mcg.get_decomposition(), ucg.get_decomposition()));
        }
        return decomposition;
    }

    std::vector<Column> columns_;
    unsigned n;
};

/// Tests ///
void test_gate() {
    Gate a(1,2,3,4);
    assert(a(0,0) == complex_type(1));
    assert(a(0,1) == complex_type(2));
    assert(a(1,0) == complex_type(3));
    assert(a(1,1) == complex_type(4));

    Gate b(5,6,7,8);
    a.mul(b);
    assert(a(0,0) == complex_type(19));
    assert(a(0,1) == complex_type(22));
    assert(a(1,0) == complex_type(43));
    assert(a(1,1) == complex_type(50));

    Gate c(1,2,3,4);
    b.mul_left(c);
    assert(b(0,0) == complex_type(19));
    assert(b(0,1) == complex_type(22));
    assert(b(1,0) == complex_type(43));
    assert(b(1,1) == complex_type(50));

    Gate d(I,0,0,-I);
    Gate u = d.eigen_vectors();
    assert(u(0,0) == complex_type(1));
    assert(u(1,0) == complex_type(0));

    assert(u(0,1) == complex_type(0));
    assert(u(1,1) == complex_type(1));

    Gate e(-I,0,0,I);
    u = e.eigen_vectors();
    assert(u(0,0) == complex_type(0));
    assert(u(1,0) == complex_type(1));

    assert(u(0,1) == complex_type(1));
    assert(u(1,1) == complex_type(0));

    Gate f(0,I,I,0);
    u = f.eigen_vectors();
    f.mul(u);
    assert(std::abs(f(0,0)/u(0,0) - I) < tol);
    assert(std::abs(f(1,0)/u(1,0) - I) < tol);
    assert(std::abs(f(0,1)/u(0,1) + I) < tol);
    assert(std::abs(f(1,1)/u(1,1) + I) < tol);
}

template<typename T1, typename T2> bool close(T1 a, T2 b) { return std::abs(a-b) < tol; }

void test_diagonal() {
    std::vector<complex_type> phases = {1, I, 1.+I, 1.-I};
    auto diag = Diagonal(phases, 2, 0, 0);
    assert(close(diag.phase(0), 1.));
    assert(close(diag.phase(1), I));
    assert(close(diag.phase(2), 1.+I));
    assert(close(diag.phase(3), 1.-I));

    Diagonal::Decomposition decomp = diag.get_decomposition();

    assert(decomp.size() == 3);
    assert(decomp[0].size() == 2);
    assert(decomp[1].size() == 1);
    assert(decomp[2].size() == 1);

    calc_type r00 = decomp[0][0];
    calc_type r01 = decomp[0][1];
    calc_type r1 = decomp[1][0];
    calc_type ph = 2*decomp[2][0];

    assert(close(std::exp(I/2.*(-r00-r01-r1+ph)), 1.));
    assert(close(std::exp(I/2.*(+r00+r01-r1+ph)), I));
    assert(close(std::exp(I/2.*(+r00+r01+r1+ph)), (1.+I)/std::sqrt(2)));
    assert(close(std::exp(I/2.*(-r00-r01+r1+ph)), (1.-I)/std::sqrt(2)));
}

void test_ucg() {}

int main() {
    test_gate();
    test_diagonal();
    return 0;
}
