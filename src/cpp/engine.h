#pragma once

#include <string>

namespace sa {
    class Engine {
    public:
        Engine();
        ~Engine();

        std::string greet(const std::string& name);
        // Future: add VTK processing methods here
    };
}
