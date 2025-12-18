#include "engine.h"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace sa {

Engine::Engine() {}
Engine::~Engine() {}

std::string Engine::greet(const std::string &name) {
  return "Hello from C++ (Scientific Analysis Engine), " + name + "!";
}

} // namespace sa

PYBIND11_MODULE(sa_engine, m) {
  m.doc() = "Scientific Analysis Agent Engine (C++17)";

  py::class_<sa::Engine>(m, "Engine")
      .def(py::init<>())
      .def("greet", &sa::Engine::greet);
}
