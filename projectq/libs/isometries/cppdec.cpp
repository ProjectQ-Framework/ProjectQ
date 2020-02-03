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
