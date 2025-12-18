# Find Python and Pybind11
find_package(Python COMPONENTS Interpreter REQUIRED)

# The C++ extension module
pybind11_add_module(sa_engine engine.cpp)

# Minimal linking for now (no VTK C++ link until headers are correctly in project)
target_link_libraries(sa_engine PRIVATE)

# Installation
install(TARGETS sa_engine DESTINATION .)
