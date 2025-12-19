#ifndef SA_ENGINE_H
#define SA_ENGINE_H

#include <map>
#include <string>
#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace sa {

class Engine {
public:
  Engine();

  std::string greet(const std::string &name);

  std::map<std::string, std::string> get_data_info(py::object data_obj);

  py::object apply_slice(py::object data_obj, double ox, double oy, double oz,
                         double nx, double ny, double nz);

  py::object apply_contour(py::object data_obj, double value);

private:
  py::module_ vtk_module_;
};

} // namespace sa

#endif // SA_ENGINE_H
