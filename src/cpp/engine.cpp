#include "engine.h"
#include <pybind11/stl.h>
#include <sstream>

namespace sa {

Engine::Engine() : vtk_module_(py::module_::import("vtk")) {}

std::string Engine::greet(const std::string &name) {
  return "Hello, " + name + " from the C++ Engine!";
}

std::map<std::string, std::string> Engine::get_data_info(py::object data_obj) {
  std::map<std::string, std::string> info;
  if (data_obj.is_none())
    return {{"Error", "No data object"}};

  info["Points"] = py::str(data_obj.attr("GetNumberOfPoints")());
  info["Cells"] = py::str(data_obj.attr("GetNumberOfCells")());

  py::list bounds = data_obj.attr("GetBounds")();
  std::stringstream ss;
  ss << "[" << py::float_(bounds[0]) << ", " << py::float_(bounds[1])
     << "] x [" << py::float_(bounds[2]) << ", " << py::float_(bounds[3])
     << "] x [" << py::float_(bounds[4]) << ", " << py::float_(bounds[5])
     << "]";
  info["Bounds"] = ss.str();

  return info;
}

py::object Engine::apply_slice(py::object data_obj, double ox, double oy,
                               double oz, double nx, double ny, double nz) {
  auto plane = vtk_module_.attr("vtkPlane")();
  plane.attr("SetOrigin")(ox, oy, oz);
  plane.attr("SetNormal")(nx, ny, nz);

  auto cutter = vtk_module_.attr("vtkCutter")();
  cutter.attr("SetInputData")(data_obj);
  cutter.attr("SetCutFunction")(plane);
  cutter.attr("Update")();

  return cutter.attr("GetOutput")();
}

py::object Engine::apply_contour(py::object data_obj, double value) {
  auto contour = vtk_module_.attr("vtkContourFilter")();
  contour.attr("SetInputData")(data_obj);
  contour.attr("SetValue")(0, value);
  contour.attr("Update")();

  return contour.attr("GetOutput")();
}

} // namespace sa

PYBIND11_MODULE(sa_engine, m) {
  py::class_<sa::Engine>(m, "Engine")
      .def(py::init<>())
      .def("greet", &sa::Engine::greet)
      .def("get_data_info", &sa::Engine::get_data_info)
      .def("apply_slice", &sa::Engine::apply_slice)
      .def("apply_contour", &sa::Engine::apply_contour);
}
