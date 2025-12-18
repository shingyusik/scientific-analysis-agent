#include <string>

namespace sa {
class Engine {
public:
  Engine();
  ~Engine();

  std::string greet(const std::string &name);
};
} // namespace sa
