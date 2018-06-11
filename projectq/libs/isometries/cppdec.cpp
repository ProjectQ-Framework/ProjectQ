#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/complex.h>
#include <pybind11/stl.h>
#include <pybind11/pytypes.h>
#include <vector>
#include <complex>
#include <iostream>
#if defined(_OPENMP)
#include <omp.h>
#endif
#include "decomposition.hpp"

namespace py = pybind11;

PYBIND11_PLUGIN(cppdec) {
    py::module m("cppdec", "cppdec");

    py::class_<Diagonal>(m, "_DecomposeDiagonal")
        .def(py::init<std::vector<complex_type>&>())
        .def("get_decomposition", &Diagonal::get_decomposition)
        ;

    py::class_<UCG>(m, "_BackendDecomposeUCG")
        .def(py::init<std::vector<gate_type> &>())
        .def("get_decomposition", &UCG::get_decomposition)
        ;

    py::class_<DecomposeIsometry>(m, "_BackendDecomposeIsometry")
        .def(py::init<DecomposeIsometry::Isometry&, unsigned>())
        .def("get_decomposition", &DecomposeIsometry::get_decomposition)
        ;

    return m.ptr();
}
