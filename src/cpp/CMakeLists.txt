# Find Python and Pybind11
find_package(Python COMPONENTS Interpreter REQUIRED)

# Include engine.h
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# The C++ extension module
pybind11_add_module(sa_engine engine.cpp)

# Installation
install(TARGETS sa_engine DESTINATION .)
