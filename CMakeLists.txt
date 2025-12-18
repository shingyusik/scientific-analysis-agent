cmake_minimum_required(VERSION 3.15)
project(sa_agent LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Pybind11
find_package(pybind11 REQUIRED)

# Add C++ source directory
add_subdirectory(src/cpp)
