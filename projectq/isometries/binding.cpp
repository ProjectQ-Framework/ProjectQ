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



using c_type = std::complex<double>;
using ArrayType = std::vector<c_type, aligned_allocator<c_type,64>>;
using MatrixType = std::vector<ArrayType>;
using QuRegs = std::vector<std::vector<unsigned>>;

PYBIND11_PLUGIN(decomposition) {
    py::module m("decomposition", "decomposition");
    
    py::class_<Diagonal>(m, "_DecomposeDiagonal")
        .def(py::init<std::vector<complex_type>())
        .def("get_decomposition", &Diagonal::get_decomposition)
        ;

    py::class_<Simulator>(m, "Simulator")
        .def(py::init<unsigned>())
        .def("allocate_qubit", &Simulator::allocate_qubit)
        .def("deallocate_qubit", &Simulator::deallocate_qubit)
        .def("get_classical_value", &Simulator::get_classical_value)
        .def("is_classical", &Simulator::is_classical)
        .def("measure_qubits", &Simulator::measure_qubits_return)
        .def("apply_controlled_gate", &Simulator::apply_controlled_gate<MatrixType>)
        .def("apply_uniformly_controlled_gate", &Simulator::apply_uniformly_controlled_gate<MatrixType>)
        .def("apply_diagonal_gate", &Simulator::apply_diagonal_gate<MatrixType>)
        .def("emulate_math", &emulate_math_wrapper<QuRegs>)
        .def("get_expectation_value", &Simulator::get_expectation_value)
        .def("apply_qubit_operator", &Simulator::apply_qubit_operator)
        .def("emulate_time_evolution", &Simulator::emulate_time_evolution)
        .def("get_probability", &Simulator::get_probability)
        .def("get_amplitude", &Simulator::get_amplitude)
        .def("set_wavefunction", &Simulator::set_wavefunction)
        .def("collapse_wavefunction", &Simulator::collapse_wavefunction)
        .def("run", &Simulator::run)
        .def("cheat", &Simulator::cheat)
        ;
    return m.ptr();
}
