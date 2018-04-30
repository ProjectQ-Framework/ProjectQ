#include <vector>
#include <complex>
#include <iostream>
#if defined(_OPENMP)
#include <omp.h>
#endif
#include "decomposition.hpp"

/// Tests ///
// void test_gate() {
//     Gate a(1,2,3,4);
//     assert(a(0,0) == complex_type(1));
//     assert(a(0,1) == complex_type(2));
//     assert(a(1,0) == complex_type(3));
//     assert(a(1,1) == complex_type(4));
//
//     Gate b(5,6,7,8);
//     a.mul(b);
//     assert(a(0,0) == complex_type(19));
//     assert(a(0,1) == complex_type(22));
//     assert(a(1,0) == complex_type(43));
//     assert(a(1,1) == complex_type(50));
//
//     Gate c(1,2,3,4);
//     b.mul_left(c);
//     assert(b(0,0) == complex_type(19));
//     assert(b(0,1) == complex_type(22));
//     assert(b(1,0) == complex_type(43));
//     assert(b(1,1) == complex_type(50));
//
//     Gate d(I,0,0,-I);
//     Gate u = d.eigen_vectors();
//     assert(u(0,0) == complex_type(1));
//     assert(u(1,0) == complex_type(0));
//
//     assert(u(0,1) == complex_type(0));
//     assert(u(1,1) == complex_type(1));
//
//     Gate e(-I,0,0,I);
//     u = e.eigen_vectors();
//     assert(u(0,0) == complex_type(0));
//     assert(u(1,0) == complex_type(1));
//
//     assert(u(0,1) == complex_type(1));
//     assert(u(1,1) == complex_type(0));
//
//     Gate f(0,I,I,0);
//     u = f.eigen_vectors();
//     f.mul(u);
//     assert(std::abs(f(0,0)/u(0,0) - I) < tol);
//     assert(std::abs(f(1,0)/u(1,0) - I) < tol);
//     assert(std::abs(f(0,1)/u(0,1) + I) < tol);
//     assert(std::abs(f(1,1)/u(1,1) + I) < tol);
// }

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

using gate_t = std::array<std::array<complex_type, 2>, 2>;

int main() {
    //test_gate();
    test_diagonal();

    gate_t gate = {1,2,3,4};
    std::cout << gate[0][0] << " " << gate[0][1] << std::endl;
    std::cout << gate[1][0] << " " << gate[1][1] << std::endl;

    gate_t res = gate*gate;
    std::cout << res[0][0] << " " << res[0][1] << std::endl;
    std::cout << res[1][0] << " " << res[1][1] << std::endl;

    return 0;
}
