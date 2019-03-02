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
#include <iostream>
#if defined(_OPENMP)
#include <omp.h>
#endif

#include "_cpp/qracksimulator.hpp"

namespace py = pybind11;

using c_type = std::complex<float>;
using ArrayType = std::vector<c_type, aligned_allocator<c_type,64>>;
using MatrixType = std::vector<ArrayType>;

PYBIND11_PLUGIN(_qracksim) {
    py::module m("_qracksim", "_qracksim");
    py::class_<QrackSimulator>(m, "QrackSimulator")
        .def(py::init())
        .def(py::init<unsigned>())
        .def(py::init<unsigned, int>())
        .def(py::init<unsigned, int, int>())
        .def("allocate_qubit", &QrackSimulator::allocate_qubit)
        .def("deallocate_qubit", &QrackSimulator::deallocate_qubit)
        .def("get_classical_value", &QrackSimulator::get_classical_value)
        .def("is_classical", &QrackSimulator::is_classical)
        .def("measure_qubits", &QrackSimulator::measure_qubits_return)
        .def("apply_controlled_gate", &QrackSimulator::apply_controlled_gate<MatrixType>)
        .def("apply_controlled_swap", &QrackSimulator::apply_controlled_swap)
        .def("apply_controlled_sqrtswap", &QrackSimulator::apply_controlled_sqrtswap)
        .def("apply_controlled_phase_gate", &QrackSimulator::apply_controlled_phase_gate)
        .def("apply_uniformly_controlled_ry", &QrackSimulator::apply_uniformly_controlled_ry)
        .def("apply_uniformly_controlled_rz", &QrackSimulator::apply_uniformly_controlled_rz)
        .def("apply_controlled_inc", &QrackSimulator::apply_controlled_inc)
        .def("apply_controlled_dec", &QrackSimulator::apply_controlled_dec)
        .def("apply_controlled_mul", &QrackSimulator::apply_controlled_mul)
        .def("apply_controlled_div", &QrackSimulator::apply_controlled_div)
        .def("get_expectation_value", &QrackSimulator::get_expectation_value)
        .def("apply_qubit_operator", &QrackSimulator::apply_qubit_operator)
        .def("get_probability", &QrackSimulator::get_probability)
        .def("get_amplitude", &QrackSimulator::get_amplitude)
        .def("set_wavefunction", &QrackSimulator::set_wavefunction)
        .def("collapse_wavefunction", &QrackSimulator::collapse_wavefunction)
        .def("prepare_state", &QrackSimulator::prepare_state)
        .def("run", &QrackSimulator::run)
        .def("cheat", &QrackSimulator::cheat)
        ;
    return m.ptr();
}
