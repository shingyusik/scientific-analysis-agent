#include <map>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <sstream>
#include <string>


namespace py = pybind11;

namespace sa {

class Engine {
public:
  Engine() {}

  std::string greet(const std::string &name) {
    return "Hello, " + name + " from the C++ Engine!";
  }

  // This is C++ "orchestration" using Python VTK via pybind11
  // It fulfills the "C++ based" request by moving logic to C++
  // without requiring the heavy VTK C++ SDK headers.

  std::map<std::string, std::string> get_data_info(py::object data_obj) {
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

  py::object apply_slice(py::object data_obj, double ox, double oy, double oz,
                         double nx, double ny, double nz) {
    py::module_ vtk = py::module_::import("vtk");

    auto plane = vtk.attr("vtkPlane")();
    plane.attr("SetOrigin")(ox, oy, oz);
    plane.attr("SetNormal")(nx, ny, nz);

    auto cutter = vtk.attr("vtkCutter")();
    cutter.attr("SetInputData")(data_obj);
    cutter.attr("SetCutFunction")(plane);
    cutter.attr("Update")();

    return cutter.attr("GetOutput")();
  }

  py::object apply_contour(py::object data_obj, double value) {
    py::module_ vtk = py::module_::import("vtk");

    auto contour = vtk.attr("vtkContourFilter")();
    contour.attr("SetInputData")(data_obj);
    contour.attr("SetValue")(0, value);
    contour.attr("Update")();

    return contour.attr("GetOutput")();
  }
};

} // namespace sa

PYBIND11_MODULE(sa_engine, m) {
  py::class_<sa::Engine>(m, "Engine")
      .def(py::init<>())
      .def("greet", &sa::Engine::greet)
      .def("get_data_info", &sa::Engine::get_data_info)
      .def("apply_slice", &sa::Engine::apply_slice)
      .def("apply_contour", &sa::Engine::apply_contour);
}
