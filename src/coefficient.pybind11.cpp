#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "coefficient.cpp"

namespace py = pybind11;

PYBIND11_MODULE(widmark_bindings, m)
{
    m.doc() = "Widmark Coefficient Estimation Models";

    py::enum_<Sex>(m, "Sex")
        .value("M", Sex::M)
        .value("F", Sex::F)
        .export_values();

    py::class_<abc_Widmark>(m, "abc_Widmark")
        .def("forward_F", &abc_Widmark::forward_F)
        .def("forward_M", &abc_Widmark::forward_M)
        .def("__call__", &abc_Widmark::operator());

    py::class_<Widmark, abc_Widmark>(m, "Widmark")
        .def(py::init<>());

    py::class_<Watson, abc_Widmark>(m, "Watson")
        .def(py::init<>());

    py::class_<Forrest, abc_Widmark>(m, "Forrest")
        .def(py::init<>());

    py::class_<Seidl, abc_Widmark>(m, "Seidl")
        .def(py::init<>());

    py::class_<Ulrich, abc_Widmark>(m, "Ulrich")
        .def(py::init<>());

    py::class_<Average, abc_Widmark>(m, "Average")
        .def(py::init<>());
}
