#include <map> // Added for std::map
#include <string>

namespace sa {
class Engine {
public:
  Engine();
  std::string greet(const std::string &name);

  // Check if VTK C++ support is enabled
  bool has_vtk_support();

  // Return information about a VTK object given its memory address
  std::map<std::string, std::string> get_data_info(long long address);

  // Apply filters (returns address of the new data object)
  long long apply_slice(long long address, double ox, double oy, double oz,
                        double nx, double ny, double nz);
  long long apply_contour(long long address, double value);
};
} // namespace sa
